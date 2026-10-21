#!/usr/bin/env python3
"""
expanded_tools_benchmark.py - Expanded benchmark: external tools + CrackSmith vs CogPIE.

Tests profile-based tools against the 10 CogPIE personas,
measuring coverage of known passwords at various budgets.

Tools tested:
  1. CogPIE (5-layer hybrid cognitive)
  2. CUPP (via WLF cupp_engine)
  3. Bopscrk (via WLF bopscrk_engine)
  4. elpscrk (permutation simulation)
  5. CrackSmith (profile_generator API)
  6. Expanded Combined (CogPIE + CrackSmith + CUPP + Bopscrk + elpscrk)

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
from itertools import combinations, permutations
from pathlib import Path

COGPIE_ROOT = str(Path(__file__).resolve().parent.parent)
WLF_ROOT = str(Path(__file__).resolve().parent.parent.parent / "XPL-Suite" / "WordlistXPL-Forge")
EXTERNAL_ROOT = str(Path(__file__).resolve().parent.parent.parent / "tools" / "wordlist-tools-benchmark")

sys.path.insert(0, COGPIE_ROOT)
sys.path.insert(0, WLF_ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("cogpie.expanded_benchmark")

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
        budgets = [100, 500, 1000, 5000, 10000, 25000, 50000]
    max_budget = max(budgets)
    idx_map = {}
    for i, c in enumerate(candidates[:max_budget]):
        if c not in idx_map:
            idx_map[c] = i + 1

    hits_at = {k: 0 for k in budgets}
    hits_list = []
    misses = []
    ranks = []
    for gt in ground_truth:
        rank = idx_map.get(gt)
        if rank is not None:
            hits_list.append(gt)
            ranks.append(rank)
            for k in budgets:
                if rank <= k:
                    hits_at[k] += 1
        else:
            misses.append(gt)

    total = len(ground_truth)
    return {
        "total_targets": total,
        "total_candidates": min(len(candidates), max_budget),
        "total_hits": len(hits_list),
        "coverage_pct": round(len(hits_list) / max(total, 1) * 100, 2),
        "mrr": round(sum(1.0 / r for r in ranks) / max(total, 1), 6) if ranks else 0.0,
        "hit_rates": {f"hit@{k}": round(hits_at[k] / max(total, 1) * 100, 2)
                      for k in budgets},
        "hits": hits_list,
        "misses": misses,
    }


def load_personas() -> list[dict]:
    persona_file = Path(COGPIE_ROOT) / "tools" / "cogpie_persona_benchmark.py"
    import importlib.util
    spec = importlib.util.spec_from_file_location("persona_mod", persona_file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.PERSONAS


# ========== CogPIE ==========

def run_cogpie(persona: dict, cogpie_engine, max_output: int = 50000) -> list[str]:
    try:
        profile = dict(persona.get("profile", {}))
        results = cogpie_engine.generate(profile, max_candidates=max_output)
        return [c for c, _ in results]
    except Exception as e:
        logger.warning("CogPIE failed: %s", e)
        return []


# ========== CUPP via WLF ==========

def run_cupp_wlf(persona: dict, max_output: int = 50000) -> list[str]:
    try:
        from wlf_modules.cupp_engine import CuppEngine, CuppProfile
        cp = persona.get("cupp_profile", {})
        fields = {k: v for k, v in cp.items()
                  if k in CuppProfile.__dataclass_fields__}
        profile = CuppProfile(**fields)
        return CuppEngine().generate(profile, max_output=max_output)
    except Exception as e:
        logger.warning("CUPP WLF failed: %s", e)
        return []


# ========== Bopscrk via WLF ==========

def run_bopscrk(persona: dict, max_output: int = 50000) -> list[str]:
    try:
        from wlf_modules.bopscrk_engine import generate_from_profile, TargetProfile
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

        profile = TargetProfile(
            names=[n for n in names if n],
            surnames=[s for s in surnames if s],
            birth_dates=[d for d in dates if d],
            pets=[p for p in pets if p],
            companies=[c for c in companies if c],
            keywords=[k for k in keywords if k],
        )
        return generate_from_profile(profile, max_candidates=max_output)
    except Exception as e:
        logger.warning("Bopscrk failed: %s", e)
        return []


# ========== elpscrk (simulation) ==========

def run_elpscrk(persona: dict, max_output: int = 50000) -> list[str]:
    try:
        cp = persona.get("cupp_profile", {})
        profile = persona.get("profile", {})

        words = []
        words.append(cp.get("first_name", ""))
        if cp.get("last_name"):
            words.append(cp["last_name"])
        if cp.get("nickname"):
            words.append(cp["nickname"])
        if cp.get("partner_first"):
            words.append(cp["partner_first"])
        if cp.get("pet_name"):
            words.append(cp["pet_name"])
        if cp.get("company"):
            words.append(cp["company"])
        for kw in cp.get("extra_words", []):
            words.append(kw)
        for kw in profile.get("keywords", [])[:5]:
            words.append(kw)
        words = [w for w in words if w]

        if not words:
            return []

        bd = cp.get("birth_date", "")
        years = []
        if bd:
            if len(bd) >= 4:
                years.append(bd[-4:])
                years.append(bd[-2:])

        candidates = set()
        suffixes = ["", "1", "12", "123", "!", "@", "#", "2024", "2026"]
        if years:
            suffixes.extend(years)

        leet_map = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"}

        for w in words:
            for s in suffixes:
                c = w + s
                if 4 <= len(c) <= 32:
                    candidates.add(c)
                    candidates.add(c.capitalize() if c[0].islower() else c.lower())
            candidates.add(w[::-1])
            lw = w
            for orig, rep in leet_map.items():
                lw = lw.replace(orig, rep)
            if lw != w:
                for s in suffixes:
                    c = lw + s
                    if 4 <= len(c) <= 32:
                        candidates.add(c)

        for i, w1 in enumerate(words[:8]):
            for j, w2 in enumerate(words[:8]):
                if i != j:
                    candidates.add(w1 + w2)
                    candidates.add(w1 + w2.capitalize())
                    candidates.add(w2 + w1)
                    for s in suffixes[:5]:
                        c = w1 + w2 + s
                        if len(c) <= 32:
                            candidates.add(c)

        return list(candidates)[:max_output]

    except Exception as e:
        logger.warning("elpscrk failed: %s", e)
        return []


# ========== CrackSmith ==========

_cracksmith_loaded = False


def _ensure_cracksmith():
    global _cracksmith_loaded
    if not _cracksmith_loaded:
        cs_dir = str(Path(EXTERNAL_ROOT) / "CrackSmith")
        if cs_dir not in sys.path:
            sys.path.insert(0, cs_dir)
        _cracksmith_loaded = True


def run_cracksmith(persona: dict, max_output: int = 50000) -> list[str]:
    try:
        _ensure_cracksmith()
        from CrackSmith import profile_generator

        cp = persona.get("cupp_profile", {})
        profile = persona.get("profile", {})

        data = {
            "first": cp.get("first_name", ""),
            "last": cp.get("last_name", ""),
            "nick": cp.get("nickname", ""),
            "bday": "",
            "bmonth": "",
            "bday2": "",
            "partner": cp.get("partner_first", ""),
            "pet": cp.get("pet_name", ""),
            "company": cp.get("company", ""),
            "hobby": "",
            "phone": "",
        }

        bd = cp.get("birth_date", "")
        if bd and len(bd) >= 4:
            data["bday"] = bd[-4:]
            if len(bd) == 8:
                data["bday2"] = bd[:2]
                data["bmonth"] = bd[2:4]

        keywords = profile.get("keywords", [])
        if keywords:
            data["hobby"] = keywords[0]

        extra_words = cp.get("extra_words", [])
        for ew in extra_words[:2]:
            if not data["hobby"]:
                data["hobby"] = ew
            elif not data["phone"]:
                data["phone"] = ew

        candidates = []
        for pwd in profile_generator(data, leet=True, combos=2):
            candidates.append(pwd)
            if len(candidates) >= max_output:
                break
        return candidates

    except Exception as e:
        logger.warning("CrackSmith failed: %s", e)
        import traceback
        traceback.print_exc()
        return []


# ========== Combined ==========

def run_combined(all_candidates: dict[str, list[str]],
                 max_output: int = 50000) -> list[str]:
    seen = set()
    combined = []
    priority_order = ["cogpie", "cracksmith", "cupp_wlf", "bopscrk", "elpscrk"]
    for algo in priority_order:
        for c in all_candidates.get(algo, []):
            if c not in seen:
                seen.add(c)
                combined.append(c)
                if len(combined) >= max_output:
                    return combined
    return combined


def main():
    logger.info("=== Expanded Tools Benchmark (10 Personas) ===")
    logger.info("RSS limit: %d MB", MAX_RSS_MB)

    personas = load_personas()
    if not personas:
        logger.error("No personas loaded")
        sys.exit(1)
    logger.info("Loaded %d personas", len(personas))

    from cogpie.engine import CogPIEEngine
    cogpie_engine = CogPIEEngine(use_gpu=True)

    algorithms = [
        "cogpie",
        "cupp_wlf",
        "bopscrk",
        "elpscrk",
        "cracksmith",
        "expanded_combined",
    ]

    results = {
        "benchmark": "expanded_tools_vs_cogpie",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "algorithms": algorithms,
        "budget": 50000,
        "personas": [],
    }

    for persona in personas:
        pid = persona["id"]
        level = persona["level"]
        gt = persona["ground_truth"]

        if not check_memory(f"persona {pid}"):
            break

        logger.info("--- %s (Level %d: %s, %d targets) ---",
                     pid, level, persona["level_name"], len(gt))

        algo_results = {}
        all_cands = {}

        # CogPIE
        t0 = time.monotonic()
        cogpie_cands = run_cogpie(persona, cogpie_engine)
        all_cands["cogpie"] = cogpie_cands
        algo_results["cogpie"] = {
            **evaluate(cogpie_cands, gt),
            "time_ms": round((time.monotonic() - t0) * 1000, 1),
        }

        # CUPP via WLF
        t0 = time.monotonic()
        cupp_cands = run_cupp_wlf(persona)
        all_cands["cupp_wlf"] = cupp_cands
        algo_results["cupp_wlf"] = {
            **evaluate(cupp_cands, gt),
            "time_ms": round((time.monotonic() - t0) * 1000, 1),
        }

        # Bopscrk
        t0 = time.monotonic()
        bopscrk_cands = run_bopscrk(persona)
        all_cands["bopscrk"] = bopscrk_cands
        algo_results["bopscrk"] = {
            **evaluate(bopscrk_cands, gt),
            "time_ms": round((time.monotonic() - t0) * 1000, 1),
        }

        # elpscrk
        t0 = time.monotonic()
        elpscrk_cands = run_elpscrk(persona)
        all_cands["elpscrk"] = elpscrk_cands
        algo_results["elpscrk"] = {
            **evaluate(elpscrk_cands, gt),
            "time_ms": round((time.monotonic() - t0) * 1000, 1),
        }

        # CrackSmith
        t0 = time.monotonic()
        cs_cands = run_cracksmith(persona)
        all_cands["cracksmith"] = cs_cands
        algo_results["cracksmith"] = {
            **evaluate(cs_cands, gt),
            "time_ms": round((time.monotonic() - t0) * 1000, 1),
        }

        # Expanded Combined
        t0_comb = time.monotonic()
        combined = run_combined(all_cands)
        algo_results["expanded_combined"] = {
            **evaluate(combined, gt),
            "time_ms": sum(algo_results[a].get("time_ms", 0)
                          for a in ["cogpie", "cupp_wlf", "bopscrk",
                                    "elpscrk", "cracksmith"]),
        }

        persona_result = {
            "id": pid,
            "level": level,
            "level_name": persona["level_name"],
            "n_ground_truth": len(gt),
            "algorithms": algo_results,
        }
        results["personas"].append(persona_result)

        best = max(algo_results.items(), key=lambda x: x[1]["coverage_pct"])
        logger.info(
            "  CogPIE: %.1f%% | CUPP: %.1f%% | Bopscrk: %.1f%% | "
            "elpscrk: %.1f%% | CrackSmith: %.1f%% | Combined: %.1f%% | Best: %s",
            algo_results["cogpie"]["coverage_pct"],
            algo_results["cupp_wlf"]["coverage_pct"],
            algo_results["bopscrk"]["coverage_pct"],
            algo_results["elpscrk"]["coverage_pct"],
            algo_results["cracksmith"]["coverage_pct"],
            algo_results["expanded_combined"]["coverage_pct"],
            best[0],
        )

        gc.collect()

    # Summary
    summary = {}
    for algo in algorithms:
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

    # Gap analysis
    gap_analysis = {}
    for persona in results["personas"]:
        pid = persona["id"]
        algos = persona["algorithms"]

        cogpie_hits = set(algos.get("cogpie", {}).get("hits", []))
        cupp_hits = set(algos.get("cupp_wlf", {}).get("hits", []))
        bopscrk_hits = set(algos.get("bopscrk", {}).get("hits", []))
        elpscrk_hits = set(algos.get("elpscrk", {}).get("hits", []))
        cs_hits = set(algos.get("cracksmith", {}).get("hits", []))

        all_external = cupp_hits | bopscrk_hits | elpscrk_hits | cs_hits
        all_hits = cogpie_hits | all_external

        gap_analysis[pid] = {
            "only_cogpie": sorted(cogpie_hits - all_external),
            "only_external": sorted(all_external - cogpie_hits),
            "both": sorted(cogpie_hits & all_external),
            "missed_by_all": sorted(
                set(algos.get("cogpie", {}).get("misses", []))
                - all_external
            ),
            "cracksmith_unique": sorted(cs_hits - cogpie_hits - cupp_hits - bopscrk_hits - elpscrk_hits),
        }
    results["gap_analysis"] = gap_analysis

    # Save
    out_dir = Path(COGPIE_ROOT) / "benchmark" / "expanded_tools"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "expanded_tools_benchmark_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info("Results saved: %s", out_file)

    # Print table
    print("\n" + "=" * 120)
    print("  EXPANDED TOOLS BENCHMARK (10 Personas, @50K budget)")
    print("=" * 120)
    header = (f"  {'Persona':<18} {'Lv':>2} {'CogPIE':>8} {'CUPP':>8} "
              f"{'Bopscrk':>8} {'elpscrk':>8} {'CrackSm':>8} "
              f"{'Expand+':>8}  Best")
    print(header)
    print("-" * 120)

    for p in results["personas"]:
        a = p["algorithms"]
        line = (f"  {p['id']:<18} {p['level']:>2} "
                f"{a['cogpie']['coverage_pct']:>7.1f}% "
                f"{a['cupp_wlf']['coverage_pct']:>7.1f}% "
                f"{a['bopscrk']['coverage_pct']:>7.1f}% "
                f"{a['elpscrk']['coverage_pct']:>7.1f}% "
                f"{a['cracksmith']['coverage_pct']:>7.1f}% "
                f"{a['expanded_combined']['coverage_pct']:>7.1f}%")
        best = max(a.items(), key=lambda x: x[1]["coverage_pct"])
        line += f"  [{best[0]}]"
        print(line)

    print("-" * 120)
    s = results["summary"]
    avg = f"  {'AVERAGE':<18} {'':>2}"
    for algo in algorithms:
        if algo in s:
            avg += f" {s[algo]['avg_coverage']:>7.1f}%"
    print(avg)

    print("\n  WINS:")
    for algo in algorithms:
        if algo in s:
            print(f"    {algo}: {s[algo]['wins']}/10 personas")
    print("=" * 120)

    # Gap analysis summary
    print("\n" + "=" * 100)
    print("  GAP ANALYSIS: CogPIE vs All External Tools")
    print("=" * 100)
    total_only_cogpie = 0
    total_only_ext = 0
    total_cs_unique = 0
    total_missed = 0
    for pid, gaps in gap_analysis.items():
        total_only_cogpie += len(gaps["only_cogpie"])
        total_only_ext += len(gaps["only_external"])
        total_cs_unique += len(gaps["cracksmith_unique"])
        total_missed += len(gaps["missed_by_all"])
        print(f"\n  {pid}:")
        print(f"    Only CogPIE ({len(gaps['only_cogpie'])}): "
              f"{', '.join(gaps['only_cogpie'][:5])}"
              f"{'...' if len(gaps['only_cogpie']) > 5 else ''}")
        print(f"    Only externals ({len(gaps['only_external'])}): "
              f"{', '.join(gaps['only_external'][:5])}"
              f"{'...' if len(gaps['only_external']) > 5 else ''}")
        print(f"    CrackSmith unique ({len(gaps['cracksmith_unique'])}): "
              f"{', '.join(gaps['cracksmith_unique'][:5])}"
              f"{'...' if len(gaps['cracksmith_unique']) > 5 else ''}")
        print(f"    Missed by ALL ({len(gaps['missed_by_all'])}): "
              f"{', '.join(gaps['missed_by_all'][:5])}"
              f"{'...' if len(gaps['missed_by_all']) > 5 else ''}")

    print(f"\n  TOTALS:")
    print(f"    Only CogPIE: {total_only_cogpie}")
    print(f"    Only External: {total_only_ext}")
    print(f"    CrackSmith Unique: {total_cs_unique}")
    print(f"    Missed by ALL: {total_missed}")
    print("=" * 100)


if __name__ == "__main__":
    main()
