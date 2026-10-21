#!/usr/bin/env python3
"""
cogpie_persona_benchmark.py - Benchmark CogPIE with 10 realistic personas.

Creates 10 personas with varying profile completeness (minimal to full),
generates passwords with CogPIE and baseline algorithms, then evaluates
each against known target passwords derived from the persona's data.

Profile completeness levels:
  Level 1 (Minimal):    first name only
  Level 2 (Basic):      name + birth year
  Level 3 (Names):      name + nickname + birth date
  Level 4 (Family):     + partner + child
  Level 5 (Extended):   + pet + company
  Level 6 (Social):     + phones + social handles
  Level 7 (Cultural):   + religion + city + keywords
  Level 8 (Phrases):    + phrases + special dates
  Level 9 (Rich):       + old passwords + national ID
  Level 10 (Complete):  all fields filled (full wizard)

Each persona has a set of "ground truth" passwords that a real human with
those cognitive biases would plausibly create. The benchmark measures how
many of these passwords each algorithm finds at various budgets.

Author: Andre Henrique (@mrhenrike)
Version: 0.1.0
"""
from __future__ import annotations

import gc
import json
import logging
import os
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logger = logging.getLogger("cogpie.persona_benchmark")

PERSONAS = [
    {
        "id": "P01_minimal",
        "level": 1,
        "level_name": "Minimal",
        "fields_filled": ["first_name"],
        "profile": {
            "names": ["joao"],
            "dates": [],
            "keywords": [],
            "pets": [],
            "companies": [],
            "phones": [],
            "emails": [],
            "old_passwords": [],
            "numbers": [],
        },
        "cupp_profile": {
            "first_name": "joao",
        },
        "ground_truth": [
            "joao123", "joao1234", "Joao123", "joao2024", "joao!",
            "joao@123", "JOAO123", "joao#1", "j04o123", "joao2026",
            "joao12", "joao1", "joao!", "Joao@2024", "joao321",
        ],
    },
    {
        "id": "P02_basic",
        "level": 2,
        "level_name": "Basic",
        "fields_filled": ["first_name", "birth_year"],
        "profile": {
            "names": ["maria"],
            "dates": ["1995"],
            "keywords": [],
            "pets": [],
            "companies": [],
            "phones": [],
            "emails": [],
            "old_passwords": [],
            "numbers": ["95"],
        },
        "cupp_profile": {
            "first_name": "maria",
            "birth_date": "01011995",
        },
        "ground_truth": [
            "maria1995", "maria95", "Maria1995", "maria@1995", "m4r14",
            "maria95!", "MARIA1995", "maria199!", "Maria95", "maria#95",
            "maria1995!", "mar1a95", "maria19", "Maria@95", "maria!1995",
        ],
    },
    {
        "id": "P03_names",
        "level": 3,
        "level_name": "Names",
        "fields_filled": ["first_name", "last_name", "nickname", "birth_date"],
        "profile": {
            "names": ["carlos", "silva", "kadu"],
            "dates": ["1988", "0315", "15031988"],
            "keywords": [],
            "pets": [],
            "companies": [],
            "phones": [],
            "emails": [],
            "old_passwords": [],
            "numbers": ["88", "15", "03"],
        },
        "cupp_profile": {
            "first_name": "carlos",
            "last_name": "silva",
            "nickname": "kadu",
            "birth_date": "15031988",
        },
        "ground_truth": [
            "carlos1988", "kadu1988", "silva88", "carlos15", "kadu88",
            "Carlos1988", "carlossilva", "kadu@1988", "silva1988",
            "carlos0315", "Kadu88!", "c4rlos88", "carlos#15", "silva15",
            "kadukadu", "carlossilva88", "Carlos@88", "kadu150388",
            "silvacarlos", "k4du1988",
        ],
    },
    {
        "id": "P04_family",
        "level": 4,
        "level_name": "Family",
        "fields_filled": ["first_name", "nickname", "birth_date",
                          "partner_name", "partner_birth", "child_name", "child_birth"],
        "profile": {
            "names": ["pedro", "pedrinho", "ana", "lucas"],
            "dates": ["1990", "0722", "1992", "2018", "07"],
            "keywords": [],
            "pets": [],
            "companies": [],
            "phones": [],
            "emails": [],
            "old_passwords": [],
            "numbers": ["90", "92", "18", "22", "07"],
        },
        "cupp_profile": {
            "first_name": "pedro",
            "nickname": "pedrinho",
            "birth_date": "22071990",
            "partner_first": "ana",
            "partner_birth": "15031992",
            "child_name": "lucas",
            "child_birth": "10052018",
        },
        "ground_truth": [
            "pedro1990", "pedrinho90", "ana1992", "lucas2018", "pedro@ana",
            "pedroana", "pedrinho!", "Pedro1990", "anapedro", "lucas18",
            "pedro0722", "ana!1992", "pedrolucas", "pedrinho1990",
            "ana@pedro", "lucas10", "Pedro@90", "p3dr0", "anaPedro",
            "pedro#ana92", "lucas2018!", "pedrinho22",
        ],
    },
    {
        "id": "P05_extended",
        "level": 5,
        "level_name": "Extended",
        "fields_filled": ["first_name", "last_name", "nickname", "birth_date",
                          "partner_name", "pet_name", "company"],
        "profile": {
            "names": ["fernanda", "costa", "fer", "rafael"],
            "dates": ["1987", "0510", "10051987"],
            "keywords": ["marketing"],
            "pets": ["thor"],
            "companies": ["globo"],
            "phones": [],
            "emails": ["fernanda.costa@globo.com"],
            "old_passwords": [],
            "numbers": ["87", "10", "05"],
        },
        "cupp_profile": {
            "first_name": "fernanda",
            "last_name": "costa",
            "nickname": "fer",
            "birth_date": "10051987",
            "partner_first": "rafael",
            "pet_name": "thor",
            "company": "globo",
        },
        "ground_truth": [
            "fernanda1987", "fer87", "thor1987", "globo2024", "fernanda@globo",
            "Fer1987!", "rafael@fer", "costa87", "Thor123", "fernandacosta",
            "fer0510", "globo87", "fernanda#thor", "Rafael87", "fer!thor",
            "globofernanda", "f3rnand4", "thor@globo", "costa1987",
            "fercosta87", "marketing2024", "fernanda10",
        ],
    },
    {
        "id": "P06_social",
        "level": 6,
        "level_name": "Social",
        "fields_filled": ["first_name", "last_name", "nickname", "birth_date",
                          "partner_name", "pet_name", "company",
                          "phones", "social_handles"],
        "profile": {
            "names": ["bruno", "santos", "bru", "camila"],
            "dates": ["1993", "0828", "28081993"],
            "keywords": ["developer", "python"],
            "pets": ["mel"],
            "companies": ["nubank"],
            "phones": ["11987654321"],
            "emails": ["bruno@nubank.com.br"],
            "old_passwords": [],
            "numbers": ["93", "28", "08", "987654321", "4321"],
        },
        "cupp_profile": {
            "first_name": "bruno",
            "last_name": "santos",
            "nickname": "bru",
            "birth_date": "28081993",
            "partner_first": "camila",
            "pet_name": "mel",
            "company": "nubank",
        },
        "ground_truth": [
            "bruno1993", "bru93", "nubank2024", "mel1993", "camila@bruno",
            "santos93", "Bruno@93", "python123", "developer!", "brunodev",
            "mel!bru", "nubank93", "santos1993", "bru@nubank", "4321bruno",
            "b.santos93", "camila93", "brunosantos", "mel@bruno",
            "python2024", "nubank!", "bru280893", "987654bruno",
        ],
    },
    {
        "id": "P07_cultural",
        "level": 7,
        "level_name": "Cultural",
        "fields_filled": ["first_name", "last_name", "nickname", "birth_date",
                          "partner_name", "pet_name", "company",
                          "phones", "city", "religion", "keywords"],
        "profile": {
            "names": ["juliana", "oliveira", "ju", "marcos"],
            "dates": ["1991", "0614", "14061991"],
            "keywords": ["flamengo", "samba", "rio", "evangelica"],
            "pets": ["nina"],
            "companies": ["petrobras"],
            "phones": ["21999887766"],
            "emails": ["juliana.oliveira@petrobras.com.br"],
            "old_passwords": [],
            "numbers": ["91", "14", "06", "9988"],
        },
        "cupp_profile": {
            "first_name": "juliana",
            "last_name": "oliveira",
            "nickname": "ju",
            "birth_date": "14061991",
            "partner_first": "marcos",
            "pet_name": "nina",
            "company": "petrobras",
            "extra_words": ["flamengo", "samba", "rio", "evangelica"],
        },
        "ground_truth": [
            "juliana1991", "ju91", "flamengo91", "petrobras2024", "nina91",
            "marcos@ju", "samba1991", "Flamengo!", "julianario", "oliveira91",
            "Ju@1991", "nina!ju", "mengao91", "petrobras!", "rio91",
            "flamengo123", "ju140691", "evangelica!", "samba@rio",
            "marcos1991", "julianaoliveira", "nina2024", "juflamengo",
            "Juliana@fla", "rio2024",
        ],
    },
    {
        "id": "P08_phrases",
        "level": 8,
        "level_name": "Phrases",
        "fields_filled": ["first_name", "last_name", "nickname", "birth_date",
                          "partner_name", "pet_name", "company",
                          "city", "keywords", "phrases", "special_dates"],
        "profile": {
            "names": ["lucas", "ferreira", "lukinha", "beatriz"],
            "dates": ["1989", "0203", "02031989", "2015", "1225"],
            "keywords": ["corinthians", "guitarra", "rock", "cerveja", "sp"],
            "pets": ["bob"],
            "companies": ["itau"],
            "phones": [],
            "emails": ["lucas.ferreira@itau.com.br"],
            "old_passwords": [],
            "numbers": ["89", "02", "03", "15", "25"],
        },
        "cupp_profile": {
            "first_name": "lucas",
            "last_name": "ferreira",
            "nickname": "lukinha",
            "birth_date": "02031989",
            "partner_first": "beatriz",
            "pet_name": "bob",
            "company": "itau",
            "extra_words": ["corinthians", "guitarra", "rock", "cerveja", "sp"],
        },
        "ground_truth": [
            "lucas1989", "lukinha89", "corinthians89", "guitarra!", "bob1989",
            "beatriz@lucas", "itau2024", "rock123", "cerveja89", "Ferreira89",
            "lucas0203", "timao89", "lukinha!", "bobferreira", "sp1989",
            "lucas@itau", "guitarra1989", "beatriz89", "corinthians!",
            "rockbeer", "lucas#1225", "itau89", "lukinha0203",
            "Cerveja2024", "bobinho",
        ],
    },
    {
        "id": "P09_rich",
        "level": 9,
        "level_name": "Rich",
        "fields_filled": ["first_name", "last_name", "nickname", "birth_date",
                          "partner_name", "partner_birth", "child_name",
                          "pet_name", "company", "phones", "city",
                          "keywords", "old_passwords", "national_id"],
        "profile": {
            "names": ["andre", "henrique", "dede", "patricia", "sophia"],
            "dates": ["1985", "0917", "17091985", "1988", "2016"],
            "keywords": ["seguranca", "hacker", "linux", "metal", "curitiba"],
            "pets": ["zeus"],
            "companies": ["safelabs"],
            "phones": ["41998765432"],
            "emails": ["andre@safelabs.com.br"],
            "old_passwords": ["dede1985!", "Andre@123", "zeus1985"],
            "numbers": ["85", "17", "09", "88", "16", "432"],
        },
        "cupp_profile": {
            "first_name": "andre",
            "last_name": "henrique",
            "nickname": "dede",
            "birth_date": "17091985",
            "partner_first": "patricia",
            "partner_birth": "22041988",
            "child_name": "sophia",
            "child_birth": "15032016",
            "pet_name": "zeus",
            "company": "safelabs",
            "extra_words": ["seguranca", "hacker", "linux", "metal", "curitiba"],
        },
        "ground_truth": [
            "dede1985!", "Andre@123", "zeus1985", "andre1985", "henrique85",
            "hacker123", "safelabs2024", "patricia88", "sophia2016",
            "linux!", "zeus@dede", "dede170985", "metal1985", "curitiba85",
            "patricia@andre", "sophia16", "safelabs!", "andrehenrique",
            "Zeus@1985", "dede!hacker", "seguranca123", "dede85",
            "andre@safelabs", "patriciasophia", "zeus2024", "d3d31985",
        ],
    },
    {
        "id": "P10_complete",
        "level": 10,
        "level_name": "Complete",
        "fields_filled": ["first_name", "last_name", "nickname", "birth_date",
                          "partner_name", "partner_nick", "partner_birth",
                          "child_name", "child_birth",
                          "pet_name", "pet_year",
                          "company", "department", "company_email", "company_domain",
                          "phones", "social_handles", "city", "state", "country",
                          "national_id", "religion", "church",
                          "keywords", "special_dates", "phrases",
                          "old_passwords"],
        "profile": {
            "names": ["gabriel", "rodrigues", "gabi", "biel",
                      "amanda", "mandinha", "enzo"],
            "dates": ["1992", "0411", "11041992", "1994", "2019",
                      "0704", "1225"],
            "keywords": ["palmeiras", "averdao", "cerveja", "churrasco",
                         "engenheiro", "construcao", "saopaulo",
                         "universal", "forca", "jovem"],
            "pets": ["pipoca"],
            "companies": ["odebrecht", "engenharia"],
            "phones": ["11976543210"],
            "emails": ["gabriel.rodrigues@odebrecht.com",
                       "gabi_biel@gmail.com"],
            "old_passwords": ["gabi1992!", "Palmeiras@92", "pipoca2019",
                              "amanda1994", "Gabi@ode"],
            "numbers": ["92", "11", "04", "94", "19", "25", "04",
                        "3210", "76543210"],
        },
        "cupp_profile": {
            "first_name": "gabriel",
            "last_name": "rodrigues",
            "nickname": "gabi",
            "birth_date": "11041992",
            "partner_first": "amanda",
            "partner_nick": "mandinha",
            "partner_birth": "04071994",
            "child_name": "enzo",
            "child_birth": "15062019",
            "pet_name": "pipoca",
            "company": "odebrecht",
            "extra_words": ["palmeiras", "averdao", "cerveja", "churrasco",
                            "engenheiro", "construcao", "saopaulo",
                            "universal", "forca", "jovem", "biel"],
        },
        "ground_truth": [
            "gabi1992!", "Palmeiras@92", "pipoca2019", "amanda1994",
            "Gabi@ode", "gabriel1992", "rodrigues92", "biel92",
            "palmeiras!", "enzo2019", "mandinha94", "odebrecht2024",
            "churrasco!", "gabriel@amanda", "pipoca!", "averdao92",
            "saopaulo92", "engenheiro1992", "gabi0411", "cerveja123",
            "enzo@gabi", "universal!", "gabrielrodrigues", "amanda@gabi",
            "forca92", "g4br13l92", "Biel@1992", "pipocaenzo",
            "construcao!", "odebrecht92", "mandinhagabi",
        ],
    },
]


def _build_cogpie_profile(persona: dict) -> dict:
    """Return the CogPIE profile dict for a persona."""
    return dict(persona["profile"])


def _build_cupp_candidates(persona: dict, max_output: int = 50000) -> list[str]:
    """Generate CUPP candidates from persona's cupp_profile."""
    try:
        from cogpie._cupp_mini import cupp_generate
        return cupp_generate(persona["cupp_profile"], max_output=max_output)
    except ImportError:
        pass
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent /
                                "XPL-Suite" / "WordlistXPL-Forge"))
        from wlf_modules.cupp_engine import CuppEngine, CuppProfile
        cp = CuppProfile(**{k: v for k, v in persona["cupp_profile"].items()
                            if k in CuppProfile.__dataclass_fields__})
        return CuppEngine().generate(cp, max_output=max_output)
    except Exception as e:
        logger.warning("CUPP engine unavailable: %s", e)
        return []


def _build_markov_candidates(
    ranker, profile_words: list[str], n_candidates: int = 10000
) -> list[str]:
    """Generate Markov-seeded candidates from profile words."""
    candidates = set()
    for word in profile_words:
        if not word:
            continue
        for length in range(6, 16):
            try:
                seq = ranker.generate_sequence(word[:3], length)
                if seq:
                    candidates.add(seq)
            except Exception:
                pass
    suffixes = ["", "1", "12", "123", "!", "@", "#", "2024", "2026"]
    for word in profile_words[:10]:
        for s in suffixes:
            c = word + s
            if 4 <= len(c) <= 32:
                candidates.add(c)
            c2 = word.capitalize() + s
            if 4 <= len(c2) <= 32:
                candidates.add(c2)
    return list(candidates)[:n_candidates]


def evaluate_algorithm(
    candidates: list[str],
    ground_truth: list[str],
    budgets: list[int] | None = None,
) -> dict:
    """Evaluate candidate list against ground truth at various budgets."""
    if budgets is None:
        budgets = [10, 50, 100, 500, 1000, 5000, 10000, 25000, 50000]
    max_budget = max(budgets)
    candidate_set = {}
    for idx, c in enumerate(candidates[:max_budget]):
        if c not in candidate_set:
            candidate_set[c] = idx + 1

    hits_at = {k: 0 for k in budgets}
    ranks = []
    for gt in ground_truth:
        rank = candidate_set.get(gt)
        if rank is not None:
            ranks.append(rank)
            for k in budgets:
                if rank <= k:
                    hits_at[k] += 1

    total = len(ground_truth)
    hit_rates = {f"hit@{k}": round(hits_at[k] / max(total, 1) * 100, 2)
                 for k in budgets}
    mrr = sum(1.0 / r for r in ranks) / max(total, 1) if ranks else 0.0
    return {
        "total_targets": total,
        "total_candidates": len(candidates),
        "total_hits": len(ranks),
        "coverage_pct": round(len(ranks) / max(total, 1) * 100, 2),
        "mrr": round(mrr, 6),
        "median_rank": int(statistics.median(ranks)) if ranks else None,
        "hit_rates": hit_rates,
        "hits_raw": {f"hit@{k}": hits_at[k] for k in budgets},
    }


def run_persona_benchmark(
    use_gpu: bool = True,
    train_sources: list[str] | None = None,
    train_limit: int = 1_000_000,
    output_dir: str = "benchmark/personas",
) -> dict:
    """Run the full 10-persona benchmark."""
    from cogpie.engine import CogPIEEngine

    logger.info("=== CogPIE Persona Benchmark (10 personas, L1-L10) ===")

    engine = CogPIEEngine(use_gpu=use_gpu)

    if train_sources:
        logger.info("Training CogPIE from external sources...")
        count = 0
        t0 = time.monotonic()
        for src in train_sources:
            if not os.path.isfile(src):
                continue
            with open(src, "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    pw = line.rstrip("\n\r")
                    if not pw or len(pw) < 4 or len(pw) > 64:
                        continue
                    engine.ranker.train(pw)
                    count += 1
                    if train_limit and count >= train_limit:
                        break
            if train_limit and count >= train_limit:
                break
        train_time = time.monotonic() - t0
        logger.info("Trained on %d passwords in %.1fs", count, train_time)
    else:
        count = 0
        train_time = 0.0

    results = {
        "meta": {
            "train_count": count,
            "train_time_seconds": round(train_time, 2),
            "device": "cuda" if use_gpu else "cpu",
            "n_personas": len(PERSONAS),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        },
        "personas": [],
    }

    for persona in PERSONAS:
        pid = persona["id"]
        level = persona["level"]
        ground_truth = persona["ground_truth"]
        logger.info("--- Persona %s (Level %d: %s, %d targets) ---",
                     pid, level, persona["level_name"], len(ground_truth))

        profile = _build_cogpie_profile(persona)

        t0 = time.monotonic()
        try:
            cogpie_results = engine.generate(profile, max_candidates=50000)
            cogpie_candidates = [c for c, _ in cogpie_results]
        except Exception as e:
            logger.error("CogPIE failed for %s: %s", pid, e)
            cogpie_candidates = []
        cogpie_time = time.monotonic() - t0

        t0 = time.monotonic()
        cupp_candidates = _build_cupp_candidates(persona)
        cupp_time = time.monotonic() - t0

        t0 = time.monotonic()
        profile_words = []
        for key in ["names", "keywords", "pets", "companies"]:
            profile_words.extend(profile.get(key, []))
        markov_candidates = _build_markov_candidates(
            engine.ranker, profile_words
        )
        markov_time = time.monotonic() - t0

        cogpie_eval = evaluate_algorithm(cogpie_candidates, ground_truth)
        cupp_eval = evaluate_algorithm(cupp_candidates, ground_truth)
        markov_eval = evaluate_algorithm(markov_candidates, ground_truth)

        persona_result = {
            "id": pid,
            "level": level,
            "level_name": persona["level_name"],
            "fields_filled": persona["fields_filled"],
            "n_fields": len(persona["fields_filled"]),
            "n_ground_truth": len(ground_truth),
            "algorithms": {
                "cogpie": {
                    **cogpie_eval,
                    "generation_time_ms": round(cogpie_time * 1000, 1),
                },
                "cupp": {
                    **cupp_eval,
                    "generation_time_ms": round(cupp_time * 1000, 1),
                },
                "markov": {
                    **markov_eval,
                    "generation_time_ms": round(markov_time * 1000, 1),
                },
            },
        }
        results["personas"].append(persona_result)

        logger.info(
            "  CogPIE: %d/%d (%.1f%%) in %.0fms | CUPP: %d/%d (%.1f%%) | Markov: %d/%d (%.1f%%)",
            cogpie_eval["total_hits"], len(ground_truth), cogpie_eval["coverage_pct"],
            cogpie_time * 1000,
            cupp_eval["total_hits"], len(ground_truth), cupp_eval["coverage_pct"],
            markov_eval["total_hits"], len(ground_truth), markov_eval["coverage_pct"],
        )

    summary = _compute_summary(results)
    results["summary"] = summary

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    result_file = out_path / "persona_benchmark_results.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info("Results saved: %s", result_file)
    _print_summary(results)

    del engine
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass

    return results


def _compute_summary(results: dict) -> dict:
    """Compute aggregate summary across all personas."""
    summary = {}
    for algo in ["cogpie", "cupp", "markov"]:
        coverages = []
        mrrs = []
        for p in results["personas"]:
            a = p["algorithms"].get(algo, {})
            coverages.append(a.get("coverage_pct", 0))
            mrrs.append(a.get("mrr", 0))
        summary[algo] = {
            "avg_coverage": round(statistics.mean(coverages), 2) if coverages else 0,
            "min_coverage": round(min(coverages), 2) if coverages else 0,
            "max_coverage": round(max(coverages), 2) if coverages else 0,
            "avg_mrr": round(statistics.mean(mrrs), 6) if mrrs else 0,
            "coverage_by_level": {
                p["id"]: p["algorithms"].get(algo, {}).get("coverage_pct", 0)
                for p in results["personas"]
            },
        }

    coverage_vs_level = []
    for p in results["personas"]:
        coverage_vs_level.append({
            "level": p["level"],
            "level_name": p["level_name"],
            "n_fields": p["n_fields"],
            "cogpie": p["algorithms"]["cogpie"]["coverage_pct"],
            "cupp": p["algorithms"]["cupp"]["coverage_pct"],
            "markov": p["algorithms"]["markov"]["coverage_pct"],
        })
    summary["coverage_vs_level"] = coverage_vs_level

    return summary


def _print_summary(results: dict) -> None:
    """Print a readable summary table."""
    print("\n" + "=" * 90)
    print("  PERSONA BENCHMARK RESULTS")
    print("=" * 90)
    print(f"  {'Persona':<20} {'Level':>5} {'Fields':>6}  "
          f"{'CogPIE':>8} {'CUPP':>8} {'Markov':>8}")
    print("-" * 90)
    for p in results["personas"]:
        cog = p["algorithms"]["cogpie"]["coverage_pct"]
        cup = p["algorithms"]["cupp"]["coverage_pct"]
        mar = p["algorithms"]["markov"]["coverage_pct"]
        winner = "CogPIE" if cog >= cup and cog >= mar else "CUPP" if cup >= mar else "Markov"
        print(f"  {p['id']:<20} {p['level']:>5} {p['n_fields']:>6}  "
              f"{cog:>7.1f}% {cup:>7.1f}% {mar:>7.1f}%  [{winner}]")
    print("-" * 90)
    s = results["summary"]
    print(f"  {'AVERAGE':<20} {'':>5} {'':>6}  "
          f"{s['cogpie']['avg_coverage']:>7.1f}% "
          f"{s['cupp']['avg_coverage']:>7.1f}% "
          f"{s['markov']['avg_coverage']:>7.1f}%")
    print("=" * 90)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="CogPIE Persona Benchmark")
    parser.add_argument("--train-source", "-s", action="append", default=[],
                        help="Training corpus files (can repeat)")
    parser.add_argument("--train-limit", "-t", type=int, default=1_000_000,
                        help="Max training passwords (default 1M)")
    parser.add_argument("--cpu", action="store_true", help="Force CPU mode")
    parser.add_argument("--output", "-o", default="benchmark/personas")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    default_sources = [
        "/usr/share/seclists/Passwords/Leaked-Databases/rockyou.txt",
        "/usr/share/wordlistxpl-forge/passwords/wlist_brasil.lst",
    ]
    sources = args.train_source or [s for s in default_sources if os.path.isfile(s)]

    run_persona_benchmark(
        use_gpu=not args.cpu,
        train_sources=sources,
        train_limit=args.train_limit,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
