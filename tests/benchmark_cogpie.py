"""
benchmark_cogpie.py - Synthetic benchmark for CogPIE vs other approaches.

Generates synthetic profiles and corresponding "real passwords" using known
cognitive patterns, then measures hit rate of each approach.

IMPORTANT: Uses ONLY synthetic data. No real breach data is used.

Author: Andre Henrique (@mrhenrike)
Version: 0.1.0
"""
from __future__ import annotations

import csv
import json
import random
import string
import time
from pathlib import Path

from cogpie.engine import CogPIEEngine
from cogpie.policy_filter import PasswordPolicy
from cogpie.semantic_expander import expand_token


SYNTHETIC_PROFILES = [
    {
        "names": ["Carlos Eduardo Silva"],
        "dates": ["15/03/1990", "1990"],
        "keywords": ["flamengo", "futebol", "cerveja"],
        "pets": ["Rex", "Mel"],
        "companies": ["Empresa ABC"],
        "phones": ["11987654321"],
        "emails": ["carlos.silva@email.com"],
        "old_passwords": ["Carlos90!", "flamengo2020"],
        "numbers": ["13", "7"],
    },
    {
        "names": ["Maria Fernanda Costa"],
        "dates": ["22/07/1985", "1985"],
        "keywords": ["amor", "yoga", "praia"],
        "pets": ["Luna"],
        "companies": ["Studio Bem Estar"],
        "phones": ["21999887766"],
        "emails": ["mfcosta@gmail.com"],
        "old_passwords": ["Maria@85"],
        "numbers": ["22"],
    },
    {
        "names": ["Joao Pedro Almeida"],
        "dates": ["10/12/1995", "1995"],
        "keywords": ["corinthians", "games", "python"],
        "pets": ["Thor"],
        "companies": ["TechSoft"],
        "phones": ["11955443322"],
        "emails": ["jp.almeida@outlook.com"],
        "old_passwords": ["Joao1995!"],
        "numbers": ["10", "42"],
    },
    {
        "names": ["Ana Beatriz Santos"],
        "dates": ["01/01/2000", "2000"],
        "keywords": ["musica", "kpop", "dance"],
        "pets": ["Mia", "Bowie"],
        "companies": [],
        "phones": ["11944332211"],
        "emails": ["anabea@yahoo.com"],
        "old_passwords": ["AnaBea2000"],
        "numbers": ["1"],
    },
    {
        "names": ["Roberto Nascimento"],
        "dates": ["05/08/1978", "1978"],
        "keywords": ["palmeiras", "churrasco", "moto"],
        "pets": ["Bob"],
        "companies": ["Mecanica Nascimento"],
        "phones": ["19988776655"],
        "emails": ["rnascimento@terra.com.br"],
        "old_passwords": ["Roberto78"],
        "numbers": ["5", "78"],
    },
]


def _generate_real_passwords(profile: dict) -> list[str]:
    """Generate synthetic 'real passwords' that follow known cognitive patterns.

    These simulate what a real user with this profile would actually choose,
    based on documented cognitive biases.
    """
    passwords = []
    names = profile.get("names", [])
    dates = profile.get("dates", [])
    keywords = profile.get("keywords", [])
    pets = profile.get("pets", [])
    old_pws = profile.get("old_passwords", [])

    if names:
        first = names[0].split()[0].lower()
        passwords.append(first.capitalize() + "123")
        passwords.append(first + "!")
        if dates:
            year = [d for d in dates if len(str(d)) == 4]
            if year:
                passwords.append(first.capitalize() + year[0])
                passwords.append(first + year[0][-2:])
                passwords.append(first.capitalize() + "@" + year[0])

    if keywords:
        kw = keywords[0].lower()
        passwords.append(kw + "123")
        passwords.append(kw.capitalize() + "!")
        if dates:
            year = [d for d in dates if len(str(d)) == 4]
            if year:
                passwords.append(kw + year[0])

    if pets:
        pet = pets[0].lower()
        passwords.append(pet.capitalize() + "2024")
        passwords.append(pet + "!")

    if old_pws:
        for old in old_pws:
            passwords.append(old + "1")
            passwords.append(old.replace("!", "@") if "!" in old else old + "!")

    if names and keywords:
        first = names[0].split()[0].lower()
        kw = keywords[0].lower()
        passwords.append(first[0].upper() + first[1:] + kw + "!")
        passwords.append(kw + first.capitalize())
        leet = first.replace("a", "4").replace("e", "3").replace("o", "0")
        passwords.append(leet + "123")

    if pets:
        pet = pets[0].lower()
        if dates:
            year = [d for d in dates if len(str(d)) == 4]
            if year:
                passwords.append(pet.capitalize() + year[0])
                passwords.append(pet + year[0][-2:])

    return passwords


def _cupp_baseline(profile: dict) -> set[str]:
    """Simulate CUPP-style generation (names + dates + basic concats)."""
    candidates: set[str] = set()
    names = profile.get("names", [])
    dates = profile.get("dates", [])
    keywords = profile.get("keywords", [])
    pets = profile.get("pets", [])

    all_words = []
    for n in names:
        for part in n.split():
            all_words.append(part.lower())
    all_words.extend(k.lower() for k in keywords)
    all_words.extend(p.lower() for p in pets)

    for w in all_words:
        candidates.add(w)
        candidates.add(w.capitalize())
        candidates.add(w + "123")
        candidates.add(w + "!")
        candidates.add(w.capitalize() + "!")
        for d in dates:
            d_str = str(d)
            candidates.add(w + d_str)
            candidates.add(w.capitalize() + d_str)
            if len(d_str) == 4:
                candidates.add(w + d_str[-2:])
                candidates.add(w.capitalize() + d_str[-2:])

    for i, w1 in enumerate(all_words[:5]):
        for w2 in all_words[i + 1:i + 4]:
            candidates.add(w1 + w2)
            candidates.add(w1 + "." + w2)
            candidates.add(w1 + "@" + w2)

    return candidates


def _markov_baseline(profile: dict) -> set[str]:
    """Simulate Markov-only generation (no profile info, pure statistics)."""
    candidates: set[str] = set()
    common = [
        "password", "123456", "password1", "abc123", "letmein",
        "qwerty", "admin", "welcome", "monkey", "dragon",
        "master", "login", "princess", "football", "shadow",
    ]
    for p in common:
        candidates.add(p)
        candidates.add(p + "1")
        candidates.add(p + "!")
        candidates.add(p.capitalize())
        candidates.add(p.capitalize() + "1")
    return candidates


def run_benchmark() -> dict:
    """Run the full benchmark suite."""
    results = {
        "profiles": [],
        "summary": {},
    }

    cogpie_hits_total = 0
    cupp_hits_total = 0
    markov_hits_total = 0
    total_passwords = 0

    for i, profile in enumerate(SYNTHETIC_PROFILES):
        real_passwords = set(_generate_real_passwords(profile))
        total_passwords += len(real_passwords)

        engine = CogPIEEngine()
        t0 = time.monotonic()
        cogpie_results = engine.generate(profile, max_candidates=0)
        cogpie_time = time.monotonic() - t0
        cogpie_candidates = {r[0] for r in cogpie_results}
        cogpie_hits = real_passwords & cogpie_candidates

        t1 = time.monotonic()
        cupp_candidates = _cupp_baseline(profile)
        cupp_time = time.monotonic() - t1
        cupp_hits = real_passwords & cupp_candidates

        t2 = time.monotonic()
        markov_candidates = _markov_baseline(profile)
        markov_time = time.monotonic() - t2
        markov_hits = real_passwords & markov_candidates

        cogpie_hits_total += len(cogpie_hits)
        cupp_hits_total += len(cupp_hits)
        markov_hits_total += len(markov_hits)

        profile_result = {
            "profile_id": i + 1,
            "name": profile["names"][0] if profile.get("names") else f"Profile {i+1}",
            "real_passwords": len(real_passwords),
            "cogpie": {
                "candidates": len(cogpie_candidates),
                "hits": len(cogpie_hits),
                "hit_rate": len(cogpie_hits) / max(len(real_passwords), 1),
                "time_s": round(cogpie_time, 4),
            },
            "cupp": {
                "candidates": len(cupp_candidates),
                "hits": len(cupp_hits),
                "hit_rate": len(cupp_hits) / max(len(real_passwords), 1),
                "time_s": round(cupp_time, 4),
            },
            "markov": {
                "candidates": len(markov_candidates),
                "hits": len(markov_hits),
                "hit_rate": len(markov_hits) / max(len(real_passwords), 1),
                "time_s": round(markov_time, 4),
            },
        }
        results["profiles"].append(profile_result)

    results["summary"] = {
        "total_profiles": len(SYNTHETIC_PROFILES),
        "total_real_passwords": total_passwords,
        "cogpie_total_hits": cogpie_hits_total,
        "cogpie_hit_rate": cogpie_hits_total / max(total_passwords, 1),
        "cupp_total_hits": cupp_hits_total,
        "cupp_hit_rate": cupp_hits_total / max(total_passwords, 1),
        "markov_total_hits": markov_hits_total,
        "markov_hit_rate": markov_hits_total / max(total_passwords, 1),
    }

    return results


def main() -> None:
    print("Running CogPIE Benchmark Suite...")
    print("=" * 60)

    results = run_benchmark()

    for profile in results["profiles"]:
        print(f"\nProfile: {profile['name']}")
        print(f"  Real passwords: {profile['real_passwords']}")
        print(f"  CogPIE: {profile['cogpie']['hits']}/{profile['real_passwords']} "
              f"({profile['cogpie']['hit_rate']:.1%}) "
              f"[{profile['cogpie']['candidates']} candidates, {profile['cogpie']['time_s']}s]")
        print(f"  CUPP:   {profile['cupp']['hits']}/{profile['real_passwords']} "
              f"({profile['cupp']['hit_rate']:.1%}) "
              f"[{profile['cupp']['candidates']} candidates, {profile['cupp']['time_s']}s]")
        print(f"  Markov: {profile['markov']['hits']}/{profile['real_passwords']} "
              f"({profile['markov']['hit_rate']:.1%}) "
              f"[{profile['markov']['candidates']} candidates, {profile['markov']['time_s']}s]")

    s = results["summary"]
    print("\n" + "=" * 60)
    print("SUMMARY")
    print(f"  CogPIE overall hit rate: {s['cogpie_hit_rate']:.1%} ({s['cogpie_total_hits']}/{s['total_real_passwords']})")
    print(f"  CUPP overall hit rate:   {s['cupp_hit_rate']:.1%} ({s['cupp_total_hits']}/{s['total_real_passwords']})")
    print(f"  Markov overall hit rate: {s['markov_hit_rate']:.1%} ({s['markov_total_hits']}/{s['total_real_passwords']})")

    out_dir = Path(__file__).resolve().parent.parent / "docs" / "research" / "cogpie-paper" / "benchmarks"
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "benchmark_results.json").open("w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    with (out_dir / "benchmark_summary.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Profile", "Real_PWs", "CogPIE_Hits", "CogPIE_Rate",
                          "CUPP_Hits", "CUPP_Rate", "Markov_Hits", "Markov_Rate"])
        for p in results["profiles"]:
            writer.writerow([
                p["name"], p["real_passwords"],
                p["cogpie"]["hits"], f"{p['cogpie']['hit_rate']:.3f}",
                p["cupp"]["hits"], f"{p['cupp']['hit_rate']:.3f}",
                p["markov"]["hits"], f"{p['markov']['hit_rate']:.3f}",
            ])

    print(f"\nResults saved to: {out_dir}/")


if __name__ == "__main__":
    main()
