"""
engine.py - CogPIE main engine: orchestrates all 5 layers.

Pipeline:
  Layer 1 (Semantic Expansion)  -> expanded token banks
  Layer 2 (Cognitive Transforms) -> raw candidate set
  Layer 3 (Probabilistic Ranking) -> scored candidates
  Layer 4 (Entropy Scoring)       -> guessability metadata
  Layer 5 (Policy Filtering)      -> final output

The engine accepts a target profile and optional training corpus,
then generates password candidates ordered by estimated probability.

Complexity analysis:
  Let N = |profile tokens|, E = avg expansion factor (Layer 1),
      T = avg transforms per token (Layer 2), K = output budget.
  - Layer 1: O(N * E) where E ~ 20-50 per token
  - Layer 2: O(N * E * T) where T ~ 100-200 per token
  - Layer 3: O(C * log C) where C = total candidates (scoring + sorting)
  - Layer 4: O(C) (linear scan)
  - Layer 5: O(C) (linear filter with CRC32 dedup)
  Total: O(N * E * T * log(N * E * T))

Author: Andre Henrique (@mrhenrike)
Version: 0.1.0
"""
from __future__ import annotations

import logging
import pickle
import time
from collections.abc import Generator
from typing import Any

from cogpie.cognitive_transforms import (
    apply_credential_mutation,
    transform_pair,
    transform_token,
    transform_triple,
)
from cogpie.markov_pcfg_hybrid import HybridRanker
from cogpie.policy_filter import PasswordPolicy, filter_candidates
from cogpie.scorer import score_candidate
from cogpie.semantic_expander import expand_profile

logger = logging.getLogger(__name__)


def _init_ranker(
    alpha: float, beta: float, markov_order: int, use_gpu: bool
) -> HybridRanker:
    if use_gpu:
        try:
            from cogpie.gpu_backend import GPUHybridRanker, is_gpu_available
            if is_gpu_available():
                logger.info("Initializing GPU-accelerated ranker (CUDA)")
                return GPUHybridRanker(alpha=alpha, beta=beta, markov_order=markov_order)
            logger.warning("GPU requested but CUDA unavailable; falling back to CPU")
        except ImportError:
            logger.warning("gpu_backend not available; falling back to CPU")
    return HybridRanker(alpha=alpha, beta=beta, markov_order=markov_order)


class CogPIEEngine:
    """Cognitive Pattern Inference Engine.

    Orchestrates the 5-layer pipeline for targeted password generation
    based on cognitive bias modeling. When use_gpu=True (default),
    Layer 3 scoring runs on CUDA if available.
    """

    def __init__(
        self,
        alpha: float = 0.4,
        beta: float = 0.2,
        markov_order: int = 3,
        max_pair_depth: int = 2,
        use_gpu: bool = True,
    ) -> None:
        self.ranker = _init_ranker(alpha, beta, markov_order, use_gpu)
        self.max_pair_depth = max_pair_depth
        self._stats: dict[str, Any] = {}
        self._use_gpu = use_gpu

    def train(self, corpus_path: str, max_lines: int = 0) -> int:
        """Train the probabilistic model from a password corpus file.

        Args:
            corpus_path: Path to newline-delimited password file.
            max_lines: Max lines to process (0 = unlimited).

        Returns:
            Number of passwords trained on.
        """
        count = self.ranker.train_from_file(corpus_path, max_lines)
        logger.info("Trained on %d passwords from %s", count, corpus_path)
        return count

    def generate(
        self,
        profile: dict[str, Any],
        policy: PasswordPolicy | None = None,
        max_candidates: int = 100_000,
    ) -> list[tuple[str, dict[str, Any]]]:
        """Execute the full 5-layer pipeline.

        Args:
            profile: Target profile dict with keys:
                names, dates, keywords, pets, companies, phones,
                emails, old_passwords, numbers.
            policy: Target system password policy.
            max_candidates: Maximum candidates in final output.

        Returns:
            List of (candidate, metadata) tuples, sorted by probability.
        """
        t0 = time.monotonic()

        # Layer 1: Semantic Expansion
        banks = expand_profile(profile)
        all_tokens: set[str] = set()
        for category_tokens in banks.values():
            all_tokens.update(category_tokens)

        self._stats["layer1_tokens"] = len(all_tokens)
        self._stats["layer1_time"] = time.monotonic() - t0
        logger.info("Layer 1: %d expanded tokens", len(all_tokens))

        # Layer 2: Cognitive Transforms
        t1 = time.monotonic()
        raw_candidates: set[str] = set()

        for token in all_tokens:
            if len(token) < 2 or len(token) > 40:
                continue
            raw_candidates.update(transform_token(token))

        name_tokens = sorted(banks.get("names", set()), key=len, reverse=True)[:15]
        date_tokens = sorted(banks.get("dates", set()), key=len, reverse=True)[:10]
        kw_tokens = sorted(banks.get("keywords", set()), key=len, reverse=True)[:8]
        pet_tokens = sorted(banks.get("pets", set()), key=len, reverse=True)[:5]
        co_tokens = sorted(banks.get("companies", set()), key=len, reverse=True)[:5]

        for name_t in name_tokens:
            for date_t in date_tokens:
                raw_candidates.update(transform_pair(name_t, date_t))
            for kw_t in kw_tokens:
                raw_candidates.update(transform_pair(name_t, kw_t))
            for pet_t in pet_tokens:
                raw_candidates.update(transform_pair(name_t, pet_t))

        for kw_t in kw_tokens:
            for date_t in date_tokens:
                raw_candidates.update(transform_pair(kw_t, date_t))

        for pet_t in pet_tokens:
            for date_t in date_tokens:
                raw_candidates.update(transform_pair(pet_t, date_t))

        for co_t in co_tokens:
            for date_t in date_tokens:
                raw_candidates.update(transform_pair(co_t, date_t))

        suffix_tokens = sorted(
            banks.get("dates", set()) | banks.get("numbers", set()),
            key=len,
        )[:8]
        for name_t in name_tokens[:10]:
            for date_t in date_tokens[:6]:
                for suf in ["!", "1", "123", "@", "#", ""]:
                    if suf:
                        raw_candidates.update(
                            transform_triple(name_t.lower(), date_t, suf)
                        )
            for kw_t in kw_tokens[:5]:
                for num_t in suffix_tokens[:4]:
                    raw_candidates.update(
                        transform_triple(name_t.lower(), kw_t.lower(), num_t)
                    )

        for old_pw in banks.get("old_passwords", set()):
            raw_candidates.update(apply_credential_mutation(old_pw))

        self._stats["layer2_candidates"] = len(raw_candidates)
        self._stats["layer2_time"] = time.monotonic() - t1
        logger.info("Layer 2: %d raw candidates", len(raw_candidates))

        # Layer 3: Probabilistic Ranking with direct-concat priority band
        t2 = time.monotonic()

        raw_old_pws = list(profile.get("old_passwords", []))
        priority_candidates = self._build_priority_band(banks, raw_old_pws, profile)
        priority_set = set(priority_candidates)

        remaining = [c for c in raw_candidates if c not in priority_set]
        scored_remaining = self.ranker.rank(remaining)

        scored = [(c, 0.0) for c in priority_candidates] + scored_remaining

        self._stats["layer3_time"] = time.monotonic() - t2
        self._stats["priority_band_size"] = len(priority_candidates)
        logger.info(
            "Layer 3: ranked %d candidates (%d priority)",
            len(scored), len(priority_candidates),
        )

        # Layer 4 + Layer 5: Score and Filter
        t3 = time.monotonic()
        results: list[tuple[str, dict[str, Any]]] = []
        for candidate, hybrid_score in filter_candidates(
            scored, policy=policy, max_candidates=max_candidates
        ):
            meta = score_candidate(candidate, hybrid_log_prob=hybrid_score)
            results.append((candidate, meta))

        self._stats["layer45_time"] = time.monotonic() - t3
        self._stats["total_time"] = time.monotonic() - t0
        self._stats["output_count"] = len(results)
        logger.info(
            "Pipeline complete: %d candidates in %.2fs",
            len(results),
            self._stats["total_time"],
        )

        return results

    @staticmethod
    def _build_priority_band(
        banks: dict[str, set[str]],
        raw_old_passwords: list[str] | None = None,
        raw_profile: dict[str, list[str]] | None = None,
    ) -> list[str]:
        """Build a priority band of high-probability direct concatenations.

        These are the candidates that CUPP-style tools generate: direct
        name+date, name+number, keyword+number combinations that match
        the simplest and most common password patterns.

        Tokens are selected in priority order: raw profile inputs first
        (unmodified by Layer 1 expansion), then nicknames and diminutives,
        then leet variants. This ensures real keywords like 'flamengo' are
        always in the band instead of being displaced by '3vangelica'.
        """
        seen: set[str] = set()
        priority: list[str] = []
        raw = raw_profile or {}

        old_pw_originals: list[str] = []
        old_pw_mutations: list[str] = []

        raw_set = set(raw_old_passwords or [])
        for raw_pw in (raw_old_passwords or []):
            if raw_pw not in seen and len(raw_pw) >= 1:
                seen.add(raw_pw)
                old_pw_originals.append(raw_pw)

        for old_pw in sorted(banks.get("old_passwords", set()), key=len):
            if old_pw not in seen and old_pw not in raw_set and len(old_pw) >= 1:
                seen.add(old_pw)
                old_pw_originals.append(old_pw)
            for mut in apply_credential_mutation(old_pw):
                if mut not in seen and mut != old_pw and 4 <= len(mut) <= 30:
                    seen.add(mut)
                    old_pw_mutations.append(mut)

        def _select_core(
            bank_key: str,
            raw_list: list[str],
            max_items: int,
            min_len: int = 2,
            max_len: int = 15,
            alpha_only: bool = True,
        ) -> list[str]:
            """Select core tokens: raw profile inputs first, then bank expansions."""
            result: list[str] = []
            seen_lows: set[str] = set()
            for t in raw_list:
                low = t.lower().strip()
                ok = alpha_only and low.isalpha() or not alpha_only and low.isalnum()
                if min_len <= len(low) <= max_len and ok and low not in seen_lows:
                    seen_lows.add(low)
                    result.append(low)
            has_digit = set("0123456789")
            has_alpha = set("abcdefghijklmnopqrstuvwxyz")
            for t in sorted(banks.get(bank_key, set()), key=len, reverse=True):
                low = t.lower()
                ok = alpha_only and low.isalpha() or not alpha_only and low.isalnum()
                if min_len <= len(low) <= max_len and ok and low not in seen_lows:
                    chars = set(low)
                    is_leet = bool(chars & has_digit) and bool(chars & has_alpha)
                    if not is_leet:
                        seen_lows.add(low)
                        result.append(low)
            return result[:max_items]

        core_names = _select_core("names", raw.get("names", []), 25, min_len=2)
        core_keywords = _select_core(
            "keywords", raw.get("keywords", []), 15,
            min_len=3, alpha_only=False,
        )
        core_pets = _select_core("pets", raw.get("pets", []), 5, min_len=2)
        core_companies = _select_core(
            "companies", raw.get("companies", []), 5,
            min_len=3, alpha_only=False,
        )

        core_dates: list[str] = []
        for t in sorted(banks.get("dates", set()), key=len):
            if t.isdigit() and len(t) <= 8:
                core_dates.append(t)
        core_dates = list(dict.fromkeys(core_dates))[:15]

        all_words = core_names + core_keywords + core_pets + core_companies
        all_nums = core_dates + [str(n) for n in banks.get("numbers", set())]

        suffixes = ["", "!", "1", "123", "12", "@", "#", "!!", "1!"]
        seps = ["", ".", "_", "-", "@"]

        current_years = ["2024", "2025", "2026", "24", "25", "26"]

        for word in all_words:
            for case_fn in [str.lower, str.capitalize, str.upper]:
                w = case_fn(word)
                for num in all_nums:
                    for s in suffixes[:5]:
                        c = w + num + s
                        if c not in seen and 4 <= len(c) <= 30:
                            seen.add(c)
                            priority.append(c)
                        c2 = num + w + s
                        if c2 not in seen and 4 <= len(c2) <= 30:
                            seen.add(c2)
                            priority.append(c2)
                for sep in seps:
                    for num in all_nums[:8]:
                        c = w + sep + num
                        if sep and c not in seen and 4 <= len(c) <= 30:
                            seen.add(c)
                            priority.append(c)
                for s in suffixes:
                    c = w + s
                    if c not in seen and 4 <= len(c) <= 30:
                        seen.add(c)
                        priority.append(c)

                # I4: current year suffixes for all words
                for cy in current_years:
                    c = w + cy
                    if c not in seen and 4 <= len(c) <= 30:
                        seen.add(c)
                        priority.append(c)
                    for s in suffixes[:4]:
                        if s:
                            c2 = w + cy + s
                            if c2 not in seen and 4 <= len(c2) <= 30:
                                seen.add(c2)
                                priority.append(c2)

        # I1: keyword+special_char combos (keyword!, keyword@, keyword#)
        special_suffixes = ["!", "@", "#", "$", "!!", "!@", "!1", "@!"]
        for kw in core_keywords:
            for case_fn in [str.lower, str.capitalize, str.upper]:
                w = case_fn(kw)
                for sp in special_suffixes:
                    c = w + sp
                    if c not in seen and 4 <= len(c) <= 30:
                        seen.add(c)
                        priority.append(c)
                # I2: keyword+year combos
                for num in all_nums:
                    c = w + num
                    if c not in seen and 4 <= len(c) <= 30:
                        seen.add(c)
                        priority.append(c)
                    for sp in special_suffixes[:3]:
                        c2 = w + num + sp
                        if c2 not in seen and 4 <= len(c2) <= 30:
                            seen.add(c2)
                            priority.append(c2)
                    c3 = num + w
                    if c3 not in seen and 4 <= len(c3) <= 30:
                        seen.add(c3)
                        priority.append(c3)

        cross_words = core_keywords[:5] + core_pets[:3]
        co_words = [t.lower() for t in sorted(banks.get("companies", set()), key=len)
                    if 2 <= len(t) <= 15 and t.isalpha()][:5]
        cross_words += co_words

        for w1 in core_names[:8]:
            for w2 in cross_words:
                for case_fn in [str.lower, str.capitalize]:
                    a, b = case_fn(w1), case_fn(w2)
                    for sep in seps[:3]:
                        for s in suffixes[:4]:
                            c = a + sep + b + s
                            if c not in seen and 4 <= len(c) <= 30:
                                seen.add(c)
                                priority.append(c)
                            c2 = b + sep + a + s
                            if c2 not in seen and 4 <= len(c2) <= 30:
                                seen.add(c2)
                                priority.append(c2)
                    # I7: keyword@name and name+keyword with special char joins
                    for join_ch in ["@", "+", "&"]:
                        c = a + join_ch + b
                        if c not in seen and 4 <= len(c) <= 30:
                            seen.add(c)
                            priority.append(c)
                        c2 = b + join_ch + a
                        if c2 not in seen and 4 <= len(c2) <= 30:
                            seen.add(c2)
                            priority.append(c2)

        # I3: full name concatenation (firstname+lastname as single token)
        raw_names = [n.strip() for n in (raw_old_passwords[0:0] or []) if n.strip()]
        raw_name_parts: list[str] = []
        for t in sorted(banks.get("names", set()), key=len, reverse=True):
            low = t.lower()
            if 3 <= len(low) <= 15 and low.isalpha() and " " not in low:
                raw_name_parts.append(low)
        raw_name_parts = list(dict.fromkeys(raw_name_parts))[:15]

        for i, w1 in enumerate(core_names[:6]):
            for w2 in core_names[i + 1:6]:
                for case_fn in [str.lower, str.capitalize]:
                    a, b = case_fn(w1), case_fn(w2)
                    for sep in seps[:3]:
                        for s in suffixes[:3]:
                            c = a + sep + b + s
                            if c not in seen and 4 <= len(c) <= 30:
                                seen.add(c)
                                priority.append(c)
                            c2 = b + sep + a + s
                            if c2 not in seen and 4 <= len(c2) <= 30:
                                seen.add(c2)
                                priority.append(c2)
                    # I3: direct name+name concatenation with numbers/suffixes
                    for concat_suf in ["", "!", "123", "@"]:
                        for num in all_nums[:6]:
                            c = a + b + num + concat_suf
                            if c not in seen and 4 <= len(c) <= 30:
                                seen.add(c)
                                priority.append(c)
                    # I7: name@name join pattern
                    for join_ch in ["@", "+", "&"]:
                        c = a + join_ch + b
                        if c not in seen and 4 <= len(c) <= 30:
                            seen.add(c)
                            priority.append(c)
                        c2 = b + join_ch + a
                        if c2 not in seen and 4 <= len(c2) <= 30:
                            seen.add(c2)
                            priority.append(c2)

        # keyword abbreviations (first 3 chars) for cross-combination
        kw_abbrevs = list(dict.fromkeys(
            kw[:3] for kw in core_keywords if len(kw) > 3
        ))

        # keyword@keyword, word+!+word, word+sep+abbreviation patterns
        all_cross = core_keywords + core_pets + core_companies + kw_abbrevs
        for i, w1 in enumerate(all_cross):
            for w2 in all_cross[i + 1:]:
                for case_fn in [str.lower, str.capitalize]:
                    a, b = case_fn(w1), case_fn(w2)
                    for join_ch in ["@", "!", "+", ""]:
                        c = a + join_ch + b
                        if c not in seen and 4 <= len(c) <= 30:
                            seen.add(c)
                            priority.append(c)
                        c2 = b + join_ch + a
                        if c2 not in seen and 4 <= len(c2) <= 30:
                            seen.add(c2)
                            priority.append(c2)
        for w1 in all_cross:
            for w2 in core_names[:10]:
                for case_fn in [str.lower, str.capitalize]:
                    a, b = case_fn(w1), case_fn(w2)
                    for join_ch in ["!", "@", ""]:
                        c = a + join_ch + b
                        if c not in seen and 4 <= len(c) <= 30:
                            seen.add(c)
                            priority.append(c)
                        c2 = b + join_ch + a
                        if c2 not in seen and 4 <= len(c2) <= 30:
                            seen.add(c2)
                            priority.append(c2)

        # I5: short nicknames (2-4 chars) + 2-digit year suffix
        two_digit_years = [str(y)[-2:] for y in range(1970, 2027)]
        short_nicks = [w for w in all_words if 2 <= len(w) <= 4]
        for nick in short_nicks:
            for case_fn in [str.lower, str.capitalize]:
                n = case_fn(nick)
                for yr in two_digit_years:
                    c = n + yr
                    if c not in seen and 4 <= len(c) <= 30:
                        seen.add(c)
                        priority.append(c)
                    for sp in ["!", "@", "#"]:
                        c2 = n + yr + sp
                        if c2 not in seen and 4 <= len(c2) <= 30:
                            seen.add(c2)
                            priority.append(c2)

        leet_map = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"}
        leet_batch = []
        for c in priority[:500]:
            leet_c = c
            for orig, repl in leet_map.items():
                leet_c = leet_c.replace(orig, repl)
            if leet_c != c and leet_c not in seen and 4 <= len(leet_c) <= 30:
                seen.add(leet_c)
                leet_batch.append(leet_c)

        return old_pw_originals + old_pw_mutations + priority + leet_batch

    def generate_stream(
        self,
        profile: dict[str, Any],
        policy: PasswordPolicy | None = None,
        max_candidates: int = 0,
    ) -> Generator[str, None, None]:
        """Stream-mode: yields candidates one at a time (password strings only).

        Useful for piping to hashcat or writing large wordlists.
        """
        results = self.generate(profile, policy, max_candidates or 500_000)
        for candidate, _ in results:
            yield candidate

    def train_from_corpus(
        self,
        corpus_path: str,
        max_lines: int = 0,
        progress_every: int = 500_000,
    ) -> int:
        """Train from a processed corpus file with progress reporting.

        This is the preferred method for training on large real-world
        corpora (e.g. processed SecLists output from cogpie_corpus_builder).

        Args:
            corpus_path: Path to newline-delimited password file.
            max_lines: Max lines to process (0 = unlimited).
            progress_every: Log progress every N lines (0 = silent).

        Returns:
            Number of passwords trained on.
        """
        count = 0
        t0 = time.monotonic()
        with open(corpus_path, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                pw = line.rstrip("\n\r")
                if pw:
                    self.ranker.train(pw)
                    count += 1
                    if progress_every and count % progress_every == 0:
                        elapsed = time.monotonic() - t0
                        rate = count / max(elapsed, 0.001)
                        logger.info(
                            "Training: %dk passwords (%.0f pw/s)",
                            count // 1000, rate,
                        )
                    if max_lines and count >= max_lines:
                        break
        elapsed = time.monotonic() - t0
        logger.info(
            "Training complete: %d passwords in %.1fs (%.0f pw/s)",
            count, elapsed, count / max(elapsed, 0.001),
        )
        return count

    def save_model(self, path: str) -> None:
        """Serialize the trained model to disk (pickle)."""
        model_data = {
            "ranker": self.ranker,
            "max_pair_depth": self.max_pair_depth,
            "stats": self._stats,
        }
        with open(path, "wb") as f:
            pickle.dump(model_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        logger.info("Model saved: %s", path)

    @classmethod
    def load_model(cls, path: str) -> CogPIEEngine:
        """Load a previously saved model."""
        with open(path, "rb") as f:
            model_data = pickle.load(f)
        engine = cls.__new__(cls)
        engine.ranker = model_data["ranker"]
        engine.max_pair_depth = model_data.get("max_pair_depth", 2)
        engine._stats = model_data.get("stats", {})
        logger.info("Model loaded: %s (%d trained)", path, engine.ranker.trained_count)
        return engine

    @property
    def stats(self) -> dict[str, Any]:
        return dict(self._stats)
