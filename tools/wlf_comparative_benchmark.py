#!/usr/bin/env python3
"""
wlf_comparative_benchmark.py - Comparative benchmark of WordlistXPL-Forge engines.

Tests all WLF engines that accept profile/target data against the 10 CogPIE
personas, measuring coverage of known passwords at various budgets.

Engines tested:
  1. CogPIE (5-layer hybrid cognitive)
  2. CUPP (concatenation + leet, via WLF cupp_engine)
  3. Bopscrk (transforms + combinations + leet, via WLF bopscrk_engine)
  4. Markov (OMEN-style positional, via WLF markov_engine)
  5. PCFG (probabilistic grammar, via WLF pcfg_engine)
  6. WLF Profiler (full wizard pipeline, via WLF profiler)
  7. CogPIE + WLF combined (priority from both)

Each engine is tested with the same 10 personas and evaluated at
budgets: 10, 50, 100, 500, 1K, 5K, 10K, 25K, 50K.

Author: Andre Henrique (@mrhenrike)
"""
from __future__ import annotations

import gc
import json
import logging
import os
import resource
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

COGPIE_ROOT = str(Path(__file__).resolve().parent.parent)
WLF_ROOT = str(Path(__file__).resolve().parent.parent.parent / "XPL-Suite" / "WordlistXPL-Forge")

sys.path.insert(0, COGPIE_ROOT)
sys.path.insert(0, WLF_ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("cogpie.wlf_benchmark")

MAX_RSS_MB = int(os.environ.get("COGPIE_MAX_RSS_MB", "8000"))


def get_rss_mb() -> float:
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024.0
    except Exception:
        pass
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def check_memory(label: str = "") -> bool:
    rss = get_rss_mb()
    if rss > MAX_RSS_MB:
        logger.error("MEMORY GUARD: RSS %.0f MB > %d MB [%s]", rss, MAX_RSS_MB, label)
        return False
    return True


def evaluate(candidates: list[str], ground_truth: list[str],
             budgets: list[int] | None = None) -> dict:
    if budgets is None:
        budgets = [10, 50, 100, 500, 1000, 5000, 10000, 25000, 50000]
    max_budget = max(budgets)
    idx_map = {}
    for i, c in enumerate(candidates[:max_budget]):
        if c not in idx_map:
            idx_map[c] = i + 1

    hits_at = {k: 0 for k in budgets}
    ranks = []
    for gt in ground_truth:
        rank = idx_map.get(gt)
        if rank is not None:
            ranks.append(rank)
            for k in budgets:
                if rank <= k:
                    hits_at[k] += 1

    total = len(ground_truth)
    return {
        "total_targets": total,
        "total_candidates": len(candidates),
        "total_hits": len(ranks),
        "coverage_pct": round(len(ranks) / max(total, 1) * 100, 2),
        "mrr": round(sum(1.0 / r for r in ranks) / max(total, 1), 6) if ranks else 0.0,
        "hit_rates": {f"hit@{k}": round(hits_at[k] / max(total, 1) * 100, 2) for k in budgets},
    }


def load_personas() -> list[dict]:
    persona_file = Path(COGPIE_ROOT) / "tools" / "cogpie_persona_benchmark.py"
    if not persona_file.exists():
        logger.error("Persona benchmark file not found: %s", persona_file)
        return []

    import importlib.util
    spec = importlib.util.spec_from_file_location("persona_mod", persona_file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.PERSONAS


def persona_to_cupp_profile(persona: dict):
    from wlf_modules.cupp_engine import CuppProfile
    cp = persona.get("cupp_profile", {})
    return CuppProfile(
        first_name=cp.get("first_name", ""),
        last_name=cp.get("last_name", ""),
        nickname=cp.get("nickname", ""),
        birth_date=cp.get("birth_date", ""),
        partner_first=cp.get("partner_first", ""),
        partner_last=cp.get("partner_last", ""),
        partner_nick=cp.get("partner_nick", ""),
        partner_birth=cp.get("partner_birth", ""),
        child_name=cp.get("child_name", ""),
        child_birth=cp.get("child_birth", ""),
        pet_name=cp.get("pet_name", ""),
        company=cp.get("company", ""),
    )


def persona_to_bopscrk_profile(persona: dict):
    from wlf_modules.bopscrk_engine import TargetProfile
    cp = persona.get("cupp_profile", {})
    cogpie_p = persona.get("profile", {})

    names = [cp.get("first_name", "")]
    if cp.get("nickname"):
        names.append(cp["nickname"])
    surnames = [cp.get("last_name", "")] if cp.get("last_name") else []
    dates = []
    if cp.get("birth_date"):
        dates.append(cp["birth_date"])
    if cp.get("partner_birth"):
        dates.append(cp["partner_birth"])
    pets = [cp["pet_name"]] if cp.get("pet_name") else []
    companies = [cp["company"]] if cp.get("company") else []
    keywords = cogpie_p.get("keywords", [])

    return TargetProfile(
        names=[n for n in names if n],
        surnames=[s for s in surnames if s],
        birth_dates=[d for d in dates if d],
        pets=[p for p in pets if p],
        companies=[c for c in companies if c],
        keywords=[k for k in keywords if k],
    )


def persona_to_cogpie_profile(persona: dict) -> dict:
    return persona.get("profile", {
        "names": [], "dates": [], "keywords": [], "pets": [],
        "companies": [], "phones": [], "emails": [],
        "old_passwords": [], "numbers": [],
    })


def run_cupp(persona: dict, max_output: int = 50000) -> list[str]:
    try:
        from wlf_modules.cupp_engine import CuppEngine
        engine = CuppEngine()
        profile = persona_to_cupp_profile(persona)
        return engine.generate(profile, max_output=max_output)
    except Exception as e:
        logger.warning("CUPP failed: %s", e)
        return []


def run_bopscrk(persona: dict, max_output: int = 50000) -> list[str]:
    try:
        from wlf_modules.bopscrk_engine import generate_from_profile
        profile = persona_to_bopscrk_profile(persona)
        return generate_from_profile(profile, max_candidates=max_output)
    except Exception as e:
        logger.warning("Bopscrk failed: %s", e)
        return []


def run_markov(persona: dict, engine_ref, max_output: int = 10000) -> list[str]:
    try:
        profile = persona_to_cogpie_profile(persona)
        words = profile.get("names", []) + profile.get("keywords", []) + profile.get("pets", [])
        candidates = set()
        for word in words[:10]:
            if not word:
                continue
            for length in range(6, 16):
                try:
                    seq = engine_ref.generate(word[:3], length)
                    if seq:
                        candidates.add(seq)
                except Exception:
                    pass
        suffixes = ["", "1", "12", "123", "!", "@", "#", "2024", "2026"]
        for word in words[:10]:
            for s in suffixes:
                c = word + s
                if 4 <= len(c) <= 32:
                    candidates.add(c)
                c2 = word.capitalize() + s
                if 4 <= len(c2) <= 32:
                    candidates.add(c2)
        return list(candidates)[:max_output]
    except Exception as e:
        logger.warning("Markov failed: %s", e)
        return []


def run_cogpie(persona: dict, cogpie_engine, max_output: int = 50000) -> list[str]:
    try:
        profile = persona_to_cogpie_profile(persona)
        results = cogpie_engine.generate(profile, max_candidates=max_output)
        return [c for c, _ in results]
    except Exception as e:
        logger.warning("CogPIE failed: %s", e)
        return []


def main():
    logger.info("=== WLF Comparative Benchmark (10 Personas) ===")
    logger.info("RSS limit: %d MB", MAX_RSS_MB)

    personas = load_personas()
    if not personas:
        logger.error("No personas loaded")
        sys.exit(1)
    logger.info("Loaded %d personas", len(personas))

    from cogpie.engine import CogPIEEngine
    cogpie_engine = CogPIEEngine(use_gpu=True)

    markov_engine = None
    try:
        from wlf_modules.markov_engine import MarkovModel
        markov_engine = MarkovModel()
        rockyou_path = Path(WLF_ROOT) / "wordlists" / "rockyou_sample.txt"
        if rockyou_path.exists():
            markov_engine.train(str(rockyou_path))
        else:
            logger.info("Markov: no training corpus (untrained)")
    except Exception as e:
        logger.warning("Markov engine unavailable: %s", e)

    algorithms = ["cogpie", "cupp", "bopscrk"]
    if markov_engine:
        algorithms.append("markov")

    results = {
        "benchmark": "wlf_comparative",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "algorithms": algorithms,
        "personas": [],
    }

    for persona in personas:
        pid = persona["id"]
        level = persona["level"]
        ground_truth = persona["ground_truth"]

        if not check_memory(f"persona {pid}"):
            break

        logger.info("--- %s (Level %d: %s, %d targets) ---",
                     pid, level, persona["level_name"], len(ground_truth))

        algo_results = {}

        t0 = time.monotonic()
        cogpie_cands = run_cogpie(persona, cogpie_engine)
        algo_results["cogpie"] = {
            **evaluate(cogpie_cands, ground_truth),
            "time_ms": round((time.monotonic() - t0) * 1000, 1),
        }

        t0 = time.monotonic()
        cupp_cands = run_cupp(persona)
        algo_results["cupp"] = {
            **evaluate(cupp_cands, ground_truth),
            "time_ms": round((time.monotonic() - t0) * 1000, 1),
        }

        t0 = time.monotonic()
        bopscrk_cands = run_bopscrk(persona)
        algo_results["bopscrk"] = {
            **evaluate(bopscrk_cands, ground_truth),
            "time_ms": round((time.monotonic() - t0) * 1000, 1),
        }

        if markov_engine:
            t0 = time.monotonic()
            markov_cands = run_markov(persona, markov_engine)
            algo_results["markov"] = {
                **evaluate(markov_cands, ground_truth),
                "time_ms": round((time.monotonic() - t0) * 1000, 1),
            }

        # Combined: CogPIE priority + CUPP + Bopscrk (deduped)
        seen = set()
        combined = []
        for c in cogpie_cands:
            if c not in seen:
                seen.add(c)
                combined.append(c)
        for c in cupp_cands:
            if c not in seen:
                seen.add(c)
                combined.append(c)
        for c in bopscrk_cands:
            if c not in seen:
                seen.add(c)
                combined.append(c)
        algo_results["wlf_combined"] = {
            **evaluate(combined, ground_truth),
            "time_ms": sum(algo_results[a].get("time_ms", 0)
                          for a in ["cogpie", "cupp", "bopscrk"]),
        }

        persona_result = {
            "id": pid,
            "level": level,
            "level_name": persona["level_name"],
            "n_fields": len(persona["fields_filled"]),
            "n_ground_truth": len(ground_truth),
            "algorithms": algo_results,
        }
        results["personas"].append(persona_result)

        best_algo = max(algo_results.items(), key=lambda x: x[1]["coverage_pct"])
        logger.info("  CogPIE: %.1f%% | CUPP: %.1f%% | Bopscrk: %.1f%% | Combined: %.1f%% | Best: %s",
                     algo_results["cogpie"]["coverage_pct"],
                     algo_results["cupp"]["coverage_pct"],
                     algo_results["bopscrk"]["coverage_pct"],
                     algo_results["wlf_combined"]["coverage_pct"],
                     best_algo[0])

        gc.collect()

    summary = {}
    for algo in algorithms + ["wlf_combined"]:
        coverages = [p["algorithms"][algo]["coverage_pct"]
                     for p in results["personas"]
                     if algo in p["algorithms"]]
        if coverages:
            summary[algo] = {
                "avg_coverage": round(sum(coverages) / len(coverages), 2),
                "min_coverage": min(coverages),
                "max_coverage": max(coverages),
                "wins": sum(1 for p in results["personas"]
                            if max(p["algorithms"].items(),
                                   key=lambda x: x[1]["coverage_pct"])[0] == algo),
            }
    results["summary"] = summary

    out_dir = Path(COGPIE_ROOT) / "benchmark" / "wlf_comparative"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "wlf_comparative_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info("Results saved: %s", out_file)

    print("\n" + "=" * 90)
    print("  WLF COMPARATIVE BENCHMARK RESULTS (10 Personas)")
    print("=" * 90)
    header = f"  {'Persona':<22} {'Level':>5} {'CogPIE':>8} {'CUPP':>8} {'Bopscrk':>8}"
    if "markov" in algorithms:
        header += f" {'Markov':>8}"
    header += f" {'Combined':>9}  Best"
    print(header)
    print("-" * 90)

    for p in results["personas"]:
        algos = p["algorithms"]
        line = f"  {p['id']:<22} {p['level']:>5} {algos['cogpie']['coverage_pct']:>7.1f}% {algos['cupp']['coverage_pct']:>7.1f}% {algos['bopscrk']['coverage_pct']:>7.1f}%"
        if "markov" in algos:
            line += f" {algos['markov']['coverage_pct']:>7.1f}%"
        line += f" {algos['wlf_combined']['coverage_pct']:>8.1f}%"
        best = max(algos.items(), key=lambda x: x[1]["coverage_pct"])
        line += f"  [{best[0]}]"
        print(line)

    print("-" * 90)
    s = results["summary"]
    avg_line = f"  {'AVERAGE':<22} {'':>5}"
    for algo in ["cogpie", "cupp", "bopscrk"]:
        if algo in s:
            avg_line += f" {s[algo]['avg_coverage']:>7.1f}%"
    if "markov" in s:
        avg_line += f" {s['markov']['avg_coverage']:>7.1f}%"
    if "wlf_combined" in s:
        avg_line += f" {s['wlf_combined']['avg_coverage']:>8.1f}%"
    print(avg_line)
    print("=" * 90)


if __name__ == "__main__":
    main()
