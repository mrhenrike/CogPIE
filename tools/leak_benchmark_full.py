#!/usr/bin/env python3
"""
leak_benchmark_full.py - Full-scale benchmark of CogPIE vs external tools
on 13K+ real leaked credentials with PII correlation.

Tests: CogPIE, CUPP (WLF), Bopscrk, elpscrk, psudohash, longtongue, pydictor.
Uses email local-part as PII source for profile construction.

Author: Andre Henrique (@mrhenrike)
"""
from __future__ import annotations

import gc
import json
import logging
import re
import sys
import time
from collections import Counter
from pathlib import Path

COGPIE_ROOT = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, COGPIE_ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("cogpie.leak_benchmark")
logging.getLogger("cogpie.engine").setLevel(logging.WARNING)
logging.getLogger("cogpie.semantic_expander").setLevel(logging.WARNING)

MAX_CANDIDATES = 10_000
BATCH_SIZE = 500
_COGPIE_ENGINE = None
_CUPP_ENGINE = None


def extract_pii_from_email(email: str) -> dict:
    """Extract name tokens and build a minimal CogPIE profile from email."""
    local = email.split("@")[0].lower() if "@" in email else email.lower()
    domain = email.split("@")[1].lower() if "@" in email else ""

    clean = re.sub(r"[._+\-]", " ", local)
    clean = re.sub(r"\d+", " ", clean)
    tokens = [t for t in clean.split() if len(t) >= 2 and t.isalpha()]

    numbers = re.findall(r"\d+", local)
    years = [n for n in numbers if len(n) == 4 and 1940 <= int(n) <= 2010]
    short_years = [n for n in numbers if len(n) == 2 and 50 <= int(n) <= 99]

    birth_year = ""
    if years:
        birth_year = years[0]
    elif short_years:
        birth_year = "19" + short_years[0]

    first_name = tokens[0] if tokens else local[:6]
    last_name = tokens[1] if len(tokens) > 1 else ""

    profile = {
        "first_name": first_name,
        "last_name": last_name,
        "nickname": local.split(".")[0] if "." in local else "",
        "email": email,
        "birth_year": birth_year,
        "keywords": tokens[2:] if len(tokens) > 2 else [],
        "numbers": numbers,
    }
    return profile


def build_cogpie_profile(profile: dict) -> dict:
    """Convert extracted PII into CogPIE engine profile format."""
    names = []
    if profile["first_name"]:
        names.append(profile["first_name"])
    if profile.get("last_name"):
        names.append(profile["last_name"])
    if profile.get("nickname") and profile["nickname"] not in names:
        names.append(profile["nickname"])
    full = " ".join(n for n in [profile["first_name"], profile.get("last_name", "")] if n)
    if full and " " in full:
        names.append(full)

    dates = []
    by = profile.get("birth_year", "")
    if by:
        dates.append(by)
    for n in profile.get("numbers", []):
        if n not in dates:
            dates.append(n)

    return {
        "names": names,
        "dates": dates,
        "keywords": profile.get("keywords", []),
        "pets": [],
        "companies": [],
        "phones": [],
        "emails": [profile.get("email", "")],
        "old_passwords": [],
        "numbers": [n for n in profile.get("numbers", []) if len(n) <= 4],
    }


def run_cogpie(profile: dict, max_candidates: int = MAX_CANDIDATES) -> list[str]:
    """Run CogPIE engine on a profile."""
    global _COGPIE_ENGINE
    try:
        if _COGPIE_ENGINE is None:
            from cogpie.engine import CogPIEEngine
            _COGPIE_ENGINE = CogPIEEngine()

        cogpie_profile = build_cogpie_profile(profile)
        result = _COGPIE_ENGINE.generate(cogpie_profile, max_candidates=max_candidates)
        candidates = [c for c, _ in result]
        return candidates
    except Exception as e:
        logger.debug("CogPIE error for %s: %s", profile.get("email", "?"), e)
        return []


def run_cupp_wlf(profile: dict, max_candidates: int = MAX_CANDIDATES) -> list[str]:
    """Run CUPP via WLF engine."""
    global _CUPP_ENGINE
    try:
        wlf_root = str(Path(COGPIE_ROOT).parent / "XPL-Suite" / "WordlistXPL-Forge")
        if wlf_root not in sys.path:
            sys.path.insert(0, wlf_root)

        from wlf_modules.cupp_engine import CuppEngine, CuppProfile
        if _CUPP_ENGINE is None:
            _CUPP_ENGINE = CuppEngine()

        cupp_profile = CuppProfile(
            first_name=profile["first_name"],
            last_name=profile.get("last_name", ""),
            nickname=profile.get("nickname", ""),
            birth_date=profile.get("birth_year", ""),
            extra_words=profile.get("keywords", []),
        )
        words = _CUPP_ENGINE.generate(cupp_profile)
        return list(words)[:max_candidates]
    except Exception as e:
        logger.debug("CUPP WLF error: %s", e)
        return []


def run_elpscrk(profile: dict, max_candidates: int = MAX_CANDIDATES) -> list[str]:
    """Run elpscrk-style generation."""
    try:
        tokens = [profile["first_name"]]
        if profile.get("last_name"):
            tokens.append(profile["last_name"])
        if profile.get("nickname"):
            tokens.append(profile["nickname"])
        tokens.extend(profile.get("keywords", []))

        candidates = set()
        years = profile.get("numbers", [])
        specials = ["!", "@", "#", "$", "123", "1234"]

        for t in tokens:
            candidates.add(t)
            candidates.add(t.capitalize())
            candidates.add(t.upper())
            candidates.add(t + "123")
            candidates.add(t + "1234")
            candidates.add(t + "!")
            candidates.add(t + "@")
            for y in years:
                candidates.add(t + y)
                candidates.add(t.capitalize() + y)
            for s in specials:
                candidates.add(t + s)
                candidates.add(t.capitalize() + s)

        for i, t1 in enumerate(tokens):
            for t2 in tokens[i + 1:]:
                candidates.add(t1 + t2)
                candidates.add(t2 + t1)
                candidates.add(t1 + t2 + "123")
                for y in years:
                    candidates.add(t1 + t2 + y)

        return list(candidates)[:max_candidates]
    except Exception as e:
        logger.debug("elpscrk error: %s", e)
        return []


def run_psudohash(profile: dict, max_candidates: int = MAX_CANDIDATES) -> list[str]:
    """Run psudohash-style keyword mutation."""
    try:
        base_words = [profile["first_name"]]
        if profile.get("last_name"):
            base_words.append(profile["last_name"])

        candidates = set()
        leet = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"}
        suffixes = ["!", "@", "#", "123", "1234", "12345"]

        for w in base_words:
            candidates.add(w)
            candidates.add(w.capitalize())
            candidates.add(w.upper())
            candidates.add(w.lower())
            leet_w = "".join(leet.get(c, c) for c in w.lower())
            candidates.add(leet_w)
            for s in suffixes:
                candidates.add(w + s)
                candidates.add(w.capitalize() + s)
                candidates.add(leet_w + s)
            for y in range(2020, 2027):
                candidates.add(w + str(y))
                candidates.add(w.capitalize() + str(y))
            for n in profile.get("numbers", []):
                candidates.add(w + n)
                candidates.add(w.capitalize() + n)
                candidates.add(n + w)

        return list(candidates)[:max_candidates]
    except Exception as e:
        logger.debug("psudohash error: %s", e)
        return []


def run_longtongue(profile: dict, max_candidates: int = MAX_CANDIDATES) -> list[str]:
    """Run longtongue-style generation."""
    try:
        tokens = [profile["first_name"]]
        if profile.get("last_name"):
            tokens.append(profile["last_name"])
        if profile.get("nickname"):
            tokens.append(profile["nickname"])

        candidates = set()
        for t in tokens:
            for suffix in ["", "1", "12", "123", "1234", "!", "@", "#"]:
                candidates.add(t + suffix)
                candidates.add(t.capitalize() + suffix)
            for t2 in tokens:
                if t != t2:
                    candidates.add(t + t2)
                    candidates.add(t.capitalize() + t2)

        return list(candidates)[:max_candidates]
    except Exception as e:
        logger.debug("longtongue error: %s", e)
        return []


def run_bopscrk(profile: dict, max_candidates: int = MAX_CANDIDATES) -> list[str]:
    """Run bopscrk-style generation."""
    try:
        tokens = [profile["first_name"]]
        if profile.get("last_name"):
            tokens.append(profile["last_name"])
        if profile.get("nickname"):
            tokens.append(profile["nickname"])
        tokens.extend(profile.get("keywords", []))

        candidates = set()
        leet = {"a": "@", "e": "3", "i": "1", "o": "0", "s": "$"}

        for t in tokens:
            candidates.add(t)
            candidates.add(t.capitalize())
            candidates.add(t.upper())
            leet_t = "".join(leet.get(c, c) for c in t.lower())
            candidates.add(leet_t)
            for s in ["!", ".", "123", "1234", "*"]:
                candidates.add(t + s)
            for y in profile.get("numbers", []):
                candidates.add(t + y)
                candidates.add(y + t)

        for i, t1 in enumerate(tokens):
            for t2 in tokens[i + 1:]:
                candidates.add(t1 + t2)
                candidates.add(t1 + "." + t2)
                candidates.add(t1 + "_" + t2)

        return list(candidates)[:max_candidates]
    except Exception as e:
        logger.debug("bopscrk error: %s", e)
        return []


def run_pydictor(profile: dict, max_candidates: int = MAX_CANDIDATES) -> list[str]:
    """Run pydictor SEDB-style generation."""
    try:
        tokens = [profile["first_name"]]
        if profile.get("last_name"):
            tokens.append(profile["last_name"])

        candidates = set()
        for t in tokens:
            for n in [""] + profile.get("numbers", []):
                for s in ["", "!", "@", "#", ".", "_"]:
                    candidates.add(t + n + s)
                    candidates.add(t + s + n)
                    candidates.add(t.capitalize() + n + s)
                    if n:
                        candidates.add(n + t)
                        candidates.add(n + t + s)

        return list(candidates)[:max_candidates]
    except Exception as e:
        logger.debug("pydictor error: %s", e)
        return []


TOOLS = {
    "cogpie": run_cogpie,
    "cupp_wlf": run_cupp_wlf,
    "bopscrk": run_bopscrk,
    "elpscrk": run_elpscrk,
    "psudohash": run_psudohash,
    "longtongue": run_longtongue,
    "pydictor": run_pydictor,
}


def benchmark_credential(cred: dict, tools: dict) -> dict:
    """Benchmark a single credential against all tools."""
    email = cred["email"]
    password = cred["password"]
    profile = extract_pii_from_email(email)

    result = {"email": email, "password_len": len(password), "tools": {}}

    for name, func in tools.items():
        t0 = time.monotonic()
        try:
            candidates = func(profile)
        except Exception:
            candidates = []
        elapsed = time.monotonic() - t0

        hit = password in candidates
        hit_lower = password.lower() in [c.lower() for c in candidates[:10000]] if not hit else True
        rank = -1
        if hit:
            try:
                rank = candidates.index(password)
            except ValueError:
                rank = -1

        result["tools"][name] = {
            "hit": hit,
            "hit_case_insensitive": hit_lower,
            "rank": rank,
            "n_candidates": len(candidates),
            "time_ms": round(elapsed * 1000, 1),
        }

    return result


def main():
    logger.info("=== Full Leak Benchmark: CogPIE vs External Tools ===")

    data_file = Path(COGPIE_ROOT) / "benchmark" / "brazilian_leaks" / "intelx_credentials_pii_filtered.json"
    with open(data_file) as f:
        all_creds = json.load(f)

    logger.info("Total PII-filtered credentials: %d", len(all_creds))

    # Filter to only those with extractable name tokens
    valid_creds = []
    for c in all_creds:
        profile = extract_pii_from_email(c["email"])
        tokens = [t for t in [profile["first_name"], profile.get("last_name", "")]
                  if len(t) >= 2 and t.isalpha()]
        pwd = c["password"]
        if tokens and 4 <= len(pwd) <= 40:
            valid_creds.append(c)

    logger.info("Valid credentials (name tokens + pwd 4-40 chars): %d", len(valid_creds))

    # Domain distribution
    domains = Counter()
    for c in valid_creds:
        dom = c["email"].split("@")[1].lower() if "@" in c["email"] else "unknown"
        tld = ".".join(dom.split(".")[-2:])
        if tld.endswith(".br"):
            domains["BR"] += 1
        elif tld.endswith(".cn") or tld.endswith(".tw") or tld.endswith(".hk"):
            domains["CN/TW/HK"] += 1
        elif tld in ("gmail.com", "yahoo.com", "hotmail.com", "aol.com",
                      "msn.com", "live.com", "outlook.com"):
            domains["Global webmail"] += 1
        else:
            domains["Other"] += 1
    logger.info("Domain distribution: %s", dict(domains))

    # Run benchmark in batches
    results = []
    tool_hits = Counter()
    tool_hits_ci = Counter()
    tool_exclusive = Counter()
    tool_ranks = {name: [] for name in TOOLS}
    errors = 0

    total = len(valid_creds)
    logger.info("Starting benchmark on %d credentials...", total)

    for i, cred in enumerate(valid_creds):
        if i % BATCH_SIZE == 0 and i > 0:
            logger.info(
                "Progress: %d/%d (%.1f%%) | Hits: %s",
                i, total, i / total * 100,
                {k: v for k, v in tool_hits.most_common()},
            )
            gc.collect()

        try:
            r = benchmark_credential(cred, TOOLS)
            results.append(r)

            hits_this = set()
            for name, tr in r["tools"].items():
                if tr["hit"]:
                    tool_hits[name] += 1
                    hits_this.add(name)
                    if tr["rank"] >= 0:
                        tool_ranks[name].append(tr["rank"])
                if tr["hit_case_insensitive"]:
                    tool_hits_ci[name] += 1

            if len(hits_this) == 1:
                tool_exclusive[hits_this.pop()] += 1

        except Exception as e:
            errors += 1
            if errors <= 5:
                logger.warning("Error on %s: %s", cred.get("email", "?"), e)

    # Summary
    logger.info("\n=== RESULTS: %d credentials benchmarked ===", len(results))

    summary = {
        "benchmark": "full_leak_benchmark",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_credentials": len(all_creds),
        "valid_targets": len(valid_creds),
        "benchmarked": len(results),
        "errors": errors,
        "max_candidates": MAX_CANDIDATES,
        "domain_distribution": dict(domains),
        "tools": {},
    }

    for name in TOOLS:
        hits = tool_hits[name]
        hits_ci = tool_hits_ci[name]
        exclusive = tool_exclusive[name]
        ranks = tool_ranks[name]
        median_rank = sorted(ranks)[len(ranks) // 2] if ranks else -1

        coverage = hits / len(results) * 100 if results else 0
        coverage_ci = hits_ci / len(results) * 100 if results else 0

        summary["tools"][name] = {
            "hits": hits,
            "coverage_pct": round(coverage, 2),
            "hits_case_insensitive": hits_ci,
            "coverage_ci_pct": round(coverage_ci, 2),
            "exclusive_hits": exclusive,
            "median_rank": median_rank,
            "mean_rank": round(sum(ranks) / len(ranks), 1) if ranks else -1,
        }

        logger.info(
            "  %s: %d/%d (%.1f%%) | CI: %.1f%% | Exclusive: %d | Median rank: %d",
            name, hits, len(results), coverage, coverage_ci, exclusive, median_rank,
        )

    # Combined
    combined_hits = 0
    for r in results:
        if any(tr["hit"] for tr in r["tools"].values()):
            combined_hits += 1
    summary["combined_coverage_pct"] = round(
        combined_hits / len(results) * 100 if results else 0, 2
    )
    logger.info(
        "  COMBINED: %d/%d (%.1f%%)",
        combined_hits, len(results),
        combined_hits / len(results) * 100 if results else 0,
    )

    # Save results
    out_file = Path(COGPIE_ROOT) / "benchmark" / "brazilian_leaks" / "full_leak_benchmark_results.json"
    with open(out_file, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info("Results saved to %s", out_file)

    # Save detailed results (first 1000 for analysis)
    detail_file = Path(COGPIE_ROOT) / "benchmark" / "brazilian_leaks" / "full_leak_benchmark_detail.json"
    with open(detail_file, "w") as f:
        json.dump(results[:1000], f, indent=2, ensure_ascii=False)
    logger.info("Detail (first 1000) saved to %s", detail_file)

    return summary


if __name__ == "__main__":
    main()
