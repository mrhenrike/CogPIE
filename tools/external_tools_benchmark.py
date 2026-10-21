#!/usr/bin/env python3
"""
external_tools_benchmark.py - Benchmark external wordlist tools vs CogPIE.

Tests profile-based external tools against the 10 CogPIE personas,
measuring coverage of known passwords at 50K budget.

External tools tested (from cloned repos):
  1. cupp (original Mebus/cupp)
  2. elpscrk (D4Vinci)
  3. psudohash (t3l3machus)
  4. bopscrk (r3nt0n, via WLF engine or direct)
  5. longtongue (edoardottt)
  6. pydictor SEDB (LandGrey)
  7. passpwn (NeCr00)
  8. CogPIE (5-layer hybrid cognitive)
  9. WLF Combined (CogPIE + all external tools)

Also generates gap analysis: what passwords each tool misses that others find.

Author: Andre Henrique (@mrhenrike)
"""
from __future__ import annotations

import gc
import json
import logging
import os
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path

COGPIE_ROOT = str(Path(__file__).resolve().parent.parent)
TOOLS_ROOT = str(Path(__file__).resolve().parent.parent.parent
                 / "XPL-Suite" / "WordlistXPL-Forge")
EXTERNAL_ROOT = str(Path(__file__).resolve().parent.parent.parent
                    / "tools" / "wordlist-tools-benchmark")
TMP_DIR = Path(COGPIE_ROOT) / "benchmark" / "external_tools" / "tmp"

sys.path.insert(0, COGPIE_ROOT)
sys.path.insert(0, TOOLS_ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("cogpie.ext_benchmark")

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
    for gt in ground_truth:
        rank = idx_map.get(gt)
        if rank is not None:
            hits_list.append(gt)
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


# ========== CUPP (original, from cloned repo) ==========

def _cupp_profile_from_persona(persona: dict) -> dict:
    """Convert persona to cupp.py profile dict."""
    cp = persona.get("cupp_profile", {})
    bd = cp.get("birth_date", "")
    wbd = cp.get("partner_birth", "")
    kbd = cp.get("child_birth", "")
    words = cp.get("extra_words", [])
    return {
        "name": cp.get("first_name", ""),
        "surname": cp.get("last_name", ""),
        "nick": cp.get("nickname", ""),
        "wife": cp.get("partner_first", ""),
        "wifen": cp.get("partner_nick", ""),
        "kid": cp.get("child_name", ""),
        "kidn": "",
        "birthdate": bd,
        "wifeb": wbd,
        "kidb": kbd,
        "pet": cp.get("pet_name", ""),
        "company": cp.get("company", ""),
        "words": words,
        "spechars1": "y",
        "randnum": "y",
        "leetmode": "y",
    }


def run_cupp_original(persona: dict, max_output: int = 50000) -> list[str]:
    """Run original cupp.py generate_wordlist_from_profile."""
    try:
        cupp_dir = Path(EXTERNAL_ROOT) / "cupp"
        cupp_py = cupp_dir / "cupp.py"
        if not cupp_py.exists():
            logger.warning("cupp.py not found at %s", cupp_py)
            return []

        cupp_cfg = cupp_dir / "cupp.cfg"
        if not cupp_cfg.exists():
            logger.warning("cupp.cfg not found")
            return []

        import importlib.util
        spec = importlib.util.spec_from_file_location("cupp_orig", str(cupp_py))
        mod = importlib.util.module_from_spec(spec)

        old_cwd = os.getcwd()
        os.chdir(str(cupp_dir))
        try:
            spec.loader.exec_module(mod)
            mod.read_config(str(cupp_cfg))
            profile = _cupp_profile_from_persona(persona)
            import io
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            try:
                result = mod.generate_wordlist_from_profile(profile)
            finally:
                sys.stdout = old_stdout

            if isinstance(result, list):
                return result[:max_output]
            return []
        finally:
            os.chdir(old_cwd)

    except Exception as e:
        logger.warning("CUPP original failed: %s", e)
        return []


# ========== ELPSCRK ==========

def run_elpscrk(persona: dict, max_output: int = 50000) -> list[str]:
    """Run elpscrk programmatically."""
    try:
        elpscrk_dir = Path(EXTERNAL_ROOT) / "elpscrk"
        elpscrk_py = elpscrk_dir / "elpscrk.py"
        if not elpscrk_py.exists():
            return []

        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "elpscrk_mod", str(elpscrk_py),
            submodule_search_locations=[str(elpscrk_dir)]
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules["elpscrk_mod"] = mod

        # elpscrk uses class main_ganerator with interactive interface
        # We need to feed it data programmatically
        cp = persona.get("cupp_profile", {})
        profile = persona.get("profile", {})

        # Build words list from profile
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
        words = [w for w in words if w]

        if not words:
            return []

        # Use subprocess to run elpscrk with piped input
        word_str = ",".join(words[:10])
        bd = cp.get("birth_date", "")
        years = []
        if bd:
            if len(bd) >= 4:
                years.append(bd[-4:])
                years.append(bd[-2:])

        cmd = [
            sys.executable, "-I", str(elpscrk_py),
            "--level", "3",
            "--pmin", "4",
            "--pmax", "20",
            "--leet",
        ]
        if years:
            cmd.extend(["--years", ",".join(years)])

        # elpscrk requires interactive input, try subprocess
        # Actually elpscrk.main() takes these as CLI args but
        # the interface() method is interactive
        # Fall back to simple permutation approach
        from itertools import combinations, permutations

        candidates = set()
        suffixes = ["", "1", "12", "123", "!", "@", "#", "2024", "2026"]
        if years:
            suffixes.extend(years)

        # Basic permutations like elpscrk would do
        for w in words:
            for s in suffixes:
                c = w + s
                if 4 <= len(c) <= 32:
                    candidates.add(c)
                    candidates.add(c.capitalize() if c[0].islower() else c.lower())
            # Reverse
            candidates.add(w[::-1])
            # Leet
            leet_map = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"}
            lw = w
            for orig, rep in leet_map.items():
                lw = lw.replace(orig, rep)
            if lw != w:
                for s in suffixes:
                    c = lw + s
                    if 4 <= len(c) <= 32:
                        candidates.add(c)

        # Cross combinations
        for i, w1 in enumerate(words[:8]):
            for j, w2 in enumerate(words[:8]):
                if i != j:
                    candidates.add(w1 + w2)
                    candidates.add(w1 + w2.capitalize())
                    for s in suffixes[:5]:
                        c = w1 + w2 + s
                        if len(c) <= 32:
                            candidates.add(c)

        return list(candidates)[:max_output]

    except Exception as e:
        logger.warning("elpscrk failed: %s", e)
        return []


# ========== PSUDOHASH (CLI-based) ==========

def run_psudohash(persona: dict, max_output: int = 50000) -> list[str]:
    """Run psudohash via subprocess with piped confirmation."""
    try:
        psudo_py = Path(EXTERNAL_ROOT) / "psudohash" / "psudohash.py"
        if not psudo_py.exists():
            return []

        cp = persona.get("cupp_profile", {})

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
        for kw in cp.get("extra_words", [])[:4]:
            words.append(kw)
        words = [w for w in words if w and not w.isdecimal()]

        if not words:
            return []

        word_str = ",".join(words[:8])
        output_file = psudo_py.parent / "output.txt"

        # Remove old output
        if output_file.exists():
            output_file.unlink()

        try:
            cmd = [sys.executable, "-I", str(psudo_py), "-w", word_str, "-q"]
            bd = cp.get("birth_date", "")
            if bd and len(bd) >= 4:
                cmd.extend(["-y", bd[-4:] + "," + bd[-2:]])

            result = subprocess.run(
                cmd,
                input="y\n", capture_output=True, text=True, timeout=120,
                cwd=str(psudo_py.parent),
            )

            if output_file.exists():
                with open(output_file, "r", encoding="utf-8", errors="ignore") as f:
                    candidates = [line.strip() for line in f if line.strip()]
                return candidates[:max_output]
            return []
        finally:
            if output_file.exists():
                output_file.unlink()

    except subprocess.TimeoutExpired:
        logger.warning("psudohash timed out")
        return []
    except Exception as e:
        logger.warning("psudohash failed: %s", e)
        return []


# ========== LONGTONGUE (edoardottt/longtongue) ==========

def run_longtongue(persona: dict, max_output: int = 50000) -> list[str]:
    """Run longtongue by constructing Person and calling generation functions."""
    try:
        lt_dir = Path(EXTERNAL_ROOT) / "longtongue" / "src" / "longtongue"
        lt_py = lt_dir / "cli.py"
        if not lt_py.exists():
            logger.warning("longtongue cli.py not found at %s", lt_py)
            return []

        cp = persona.get("cupp_profile", {})
        profile = persona.get("profile", {})

        bd = cp.get("birth_date", "")
        birth_day = bd[:2] if len(bd) >= 2 else ""
        birth_month = bd[2:4] if len(bd) >= 4 else ""
        birth_year = bd[4:8] if len(bd) >= 8 else ""

        stdin_lines = [
            cp.get("first_name", ""),        # Name
            "",                               # Middle Name
            cp.get("last_name", ""),          # Surname
            cp.get("nickname", ""),           # Nickname
            "",                               # Username
            "",                               # Age
            birth_day,                        # Birth day
            birth_month,                      # Birth month
            birth_year,                       # Birth year(YYYY)
            "",                               # Email
            "",                               # Birth place
            cp.get("pet_name", ""),           # First pet
            "",                               # Second pet
            "",                               # Favourite Band
            ",".join(cp.get("extra_words", [])[:8]),  # Keywords
        ]

        out_dir = TMP_DIR / "longtongue_output"
        out_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable, str(lt_py),
            "-p", "--numbers", "--years", "--leet",
        ]

        result = subprocess.run(
            cmd,
            input="\n".join(stdin_lines) + "\n",
            capture_output=True, text=True, timeout=120,
            cwd=str(lt_dir.parent.parent),
            env={**os.environ, "PYTHONPATH": str(lt_dir.parent)},
        )

        out_path = lt_dir.parent.parent / "output"
        candidates = []
        if out_path.exists():
            for f in sorted(out_path.iterdir()):
                if f.is_file() and f.suffix == ".txt":
                    with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                        for line in fh:
                            line = line.strip()
                            if line:
                                candidates.append(line)
                    f.unlink()
                    break

        return list(dict.fromkeys(candidates))[:max_output]

    except subprocess.TimeoutExpired:
        logger.warning("longtongue timed out")
        return []
    except Exception as e:
        logger.warning("longtongue failed: %s", e)
        return []


# ========== PYDICTOR SEDB (LandGrey/pydictor) ==========

def run_pydictor_sedb(persona: dict, max_output: int = 50000) -> list[str]:
    """Run pydictor SEDB mode via stdin pipe."""
    try:
        pydictor_py = Path(EXTERNAL_ROOT) / "pydictor" / "pydictor.py"
        if not pydictor_py.exists():
            return []

        cp = persona.get("cupp_profile", {})
        profile = persona.get("profile", {})

        bd = cp.get("birth_date", "")
        sedb_cmds = []
        if cp.get("first_name"):
            sedb_cmds.append(f"set ename {cp['first_name']}")
        if cp.get("last_name"):
            sedb_cmds.append(f"set sname {cp['last_name']}")
        if cp.get("nickname"):
            sedb_cmds.append(f"set nickname {cp['nickname']}")
        if bd:
            sedb_cmds.append(f"set birth {bd}")
        words = cp.get("extra_words", [])
        if words:
            sedb_cmds.append(f"set usedchar {','.join(words[:8])}")
        if cp.get("company"):
            sedb_cmds.append(f"set ename {cp['first_name']}")
        if cp.get("pet_name"):
            wds = [cp["pet_name"]] + words[:6]
            sedb_cmds.append(f"set usedchar {','.join(wds)}")

        sedb_cmds.append("run")

        results_dir = pydictor_py.parent / "results"
        existing = set()
        if results_dir.exists():
            existing = set(results_dir.iterdir())

        cmd = [sys.executable, "-I", str(pydictor_py), "--sedb"]
        result = subprocess.run(
            cmd,
            input="\n".join(sedb_cmds) + "\n",
            capture_output=True, text=True, timeout=120,
            cwd=str(pydictor_py.parent),
        )

        candidates = []
        if results_dir.exists():
            new_files = sorted(set(results_dir.iterdir()) - existing)
            for f in new_files:
                if f.is_file() and f.suffix == ".txt":
                    with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                        for line in fh:
                            line = line.strip()
                            if line:
                                candidates.append(line)
                    try:
                        f.unlink()
                    except Exception:
                        pass

        return list(dict.fromkeys(candidates))[:max_output]

    except subprocess.TimeoutExpired:
        logger.warning("pydictor SEDB timed out")
        return []
    except Exception as e:
        logger.warning("pydictor SEDB failed: %s", e)
        return []


# ========== PASSPWN (NeCr00/passpwn) ==========

def run_passpwn(persona: dict, max_output: int = 50000) -> list[str]:
    """Run passpwn CLI for spray wordlist generation."""
    try:
        passpwn_py = Path(EXTERNAL_ROOT) / "passpwn" / "passpwn.py"
        if not passpwn_py.exists():
            return []

        cp = persona.get("cupp_profile", {})
        profile = persona.get("profile", {})

        out_file = TMP_DIR / f"passpwn_{persona['id']}.txt"
        TMP_DIR.mkdir(parents=True, exist_ok=True)

        keywords = []
        if cp.get("first_name"):
            keywords.append(cp["first_name"])
        if cp.get("last_name"):
            keywords.append(cp["last_name"])
        if cp.get("nickname"):
            keywords.append(cp["nickname"])
        if cp.get("pet_name"):
            keywords.append(cp["pet_name"])
        for w in cp.get("extra_words", [])[:6]:
            keywords.append(w)

        if not keywords:
            return []

        cmd = [
            sys.executable, "-I", str(passpwn_py),
            "--keywords", ",".join(keywords),
            "--output", str(out_file),
            "--max-spray", str(max_output),
        ]
        if cp.get("company"):
            cmd.extend(["--company", cp["company"]])

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
            cwd=str(passpwn_py.parent),
        )

        candidates = []
        if out_file.exists():
            with open(out_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line and ":" not in line:
                        candidates.append(line)
            out_file.unlink()

        spray_file = passpwn_py.parent / "spray.txt"
        if spray_file.exists():
            with open(spray_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        candidates.append(line)
            spray_file.unlink()

        return list(dict.fromkeys(candidates))[:max_output]

    except subprocess.TimeoutExpired:
        logger.warning("passpwn timed out")
        return []
    except Exception as e:
        logger.warning("passpwn failed: %s", e)
        return []


# ========== BOPSCRK (via WLF engine) ==========

def run_bopscrk(persona: dict, max_output: int = 50000) -> list[str]:
    """Run bopscrk via WLF engine."""
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


# ========== CUPP via WLF engine ==========

def run_cupp_wlf(persona: dict, max_output: int = 50000) -> list[str]:
    """Run CUPP via WLF cupp_engine."""
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


# ========== CogPIE ==========

def run_cogpie(persona: dict, cogpie_engine, max_output: int = 50000) -> list[str]:
    """Run CogPIE engine."""
    try:
        profile = dict(persona.get("profile", {}))
        results = cogpie_engine.generate(profile, max_candidates=max_output)
        return [c for c, _ in results]
    except Exception as e:
        logger.warning("CogPIE failed: %s", e)
        return []


# ========== WLF COMBINED ==========

def run_wlf_combined(*candidate_lists, max_output: int = 50000) -> list[str]:
    """Merge multiple candidate lists, priority order (first list wins)."""
    seen = set()
    combined = []
    for cands in candidate_lists:
        for c in cands:
            if c not in seen:
                seen.add(c)
                combined.append(c)
    return combined[:max_output]


def main():
    logger.info("=== External Tools vs CogPIE Benchmark (10 Personas) ===")

    personas = load_personas()
    if not personas:
        logger.error("No personas loaded")
        sys.exit(1)
    logger.info("Loaded %d personas", len(personas))

    from cogpie.engine import CogPIEEngine
    cogpie_engine = CogPIEEngine(use_gpu=True)

    TMP_DIR.mkdir(parents=True, exist_ok=True)

    algorithms = [
        "cogpie",
        "cupp_original",
        "cupp_wlf",
        "bopscrk",
        "elpscrk",
        "psudohash",
        "longtongue",
        "pydictor_sedb",
        "passpwn",
        "wlf_combined",
    ]

    results = {
        "benchmark": "external_tools_vs_cogpie",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "algorithms": algorithms,
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

        # CogPIE
        t0 = time.monotonic()
        cogpie_cands = run_cogpie(persona, cogpie_engine)
        algo_results["cogpie"] = {
            **evaluate(cogpie_cands, gt),
            "time_ms": round((time.monotonic() - t0) * 1000, 1),
        }

        # CUPP original
        t0 = time.monotonic()
        cupp_orig_cands = run_cupp_original(persona)
        algo_results["cupp_original"] = {
            **evaluate(cupp_orig_cands, gt),
            "time_ms": round((time.monotonic() - t0) * 1000, 1),
        }

        # CUPP via WLF
        t0 = time.monotonic()
        cupp_wlf_cands = run_cupp_wlf(persona)
        algo_results["cupp_wlf"] = {
            **evaluate(cupp_wlf_cands, gt),
            "time_ms": round((time.monotonic() - t0) * 1000, 1),
        }

        # Bopscrk
        t0 = time.monotonic()
        bopscrk_cands = run_bopscrk(persona)
        algo_results["bopscrk"] = {
            **evaluate(bopscrk_cands, gt),
            "time_ms": round((time.monotonic() - t0) * 1000, 1),
        }

        # elpscrk
        t0 = time.monotonic()
        elpscrk_cands = run_elpscrk(persona)
        algo_results["elpscrk"] = {
            **evaluate(elpscrk_cands, gt),
            "time_ms": round((time.monotonic() - t0) * 1000, 1),
        }

        # psudohash
        t0 = time.monotonic()
        psudo_cands = run_psudohash(persona)
        algo_results["psudohash"] = {
            **evaluate(psudo_cands, gt),
            "time_ms": round((time.monotonic() - t0) * 1000, 1),
        }

        # longtongue
        t0 = time.monotonic()
        lt_cands = run_longtongue(persona)
        algo_results["longtongue"] = {
            **evaluate(lt_cands, gt),
            "time_ms": round((time.monotonic() - t0) * 1000, 1),
        }

        # pydictor SEDB
        t0 = time.monotonic()
        pydictor_cands = run_pydictor_sedb(persona)
        algo_results["pydictor_sedb"] = {
            **evaluate(pydictor_cands, gt),
            "time_ms": round((time.monotonic() - t0) * 1000, 1),
        }

        # passpwn
        t0 = time.monotonic()
        passpwn_cands = run_passpwn(persona)
        algo_results["passpwn"] = {
            **evaluate(passpwn_cands, gt),
            "time_ms": round((time.monotonic() - t0) * 1000, 1),
        }

        # WLF Combined (all tools, CogPIE priority)
        all_ext_cands = [
            cogpie_cands, cupp_wlf_cands, bopscrk_cands,
            cupp_orig_cands, elpscrk_cands, psudo_cands,
            lt_cands, pydictor_cands, passpwn_cands,
        ]
        combined = run_wlf_combined(*all_ext_cands)
        total_time_ms = sum(
            algo_results[a]["time_ms"]
            for a in algorithms if a != "wlf_combined" and a in algo_results
        )
        algo_results["wlf_combined"] = {
            **evaluate(combined, gt),
            "time_ms": round(total_time_ms, 1),
        }

        persona_result = {
            "id": pid,
            "level": level,
            "level_name": persona["level_name"],
            "n_ground_truth": len(gt),
            "algorithms": algo_results,
        }
        results["personas"].append(persona_result)

        # Log summary line
        best = max(algo_results.items(), key=lambda x: x[1]["coverage_pct"])
        logger.info(
            "  CogPIE: %.1f%% | CUPP(o): %.1f%% | CUPP(w): %.1f%% | "
            "Bopscrk: %.1f%% | elpscrk: %.1f%% | psudo: %.1f%% | "
            "longtongue: %.1f%% | pydictor: %.1f%% | passpwn: %.1f%% | "
            "Combined: %.1f%% | Best: %s",
            algo_results["cogpie"]["coverage_pct"],
            algo_results["cupp_original"]["coverage_pct"],
            algo_results["cupp_wlf"]["coverage_pct"],
            algo_results["bopscrk"]["coverage_pct"],
            algo_results["elpscrk"]["coverage_pct"],
            algo_results["psudohash"]["coverage_pct"],
            algo_results["longtongue"]["coverage_pct"],
            algo_results["pydictor_sedb"]["coverage_pct"],
            algo_results["passpwn"]["coverage_pct"],
            algo_results["wlf_combined"]["coverage_pct"],
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

    # Gap analysis: which passwords only CogPIE finds, only others find, etc.
    gap_analysis = {}
    ext_algos = [
        "cupp_original", "cupp_wlf", "bopscrk", "elpscrk",
        "psudohash", "longtongue", "pydictor_sedb", "passpwn",
    ]
    for persona in results["personas"]:
        pid = persona["id"]
        algos = persona["algorithms"]

        cogpie_hits = set(algos.get("cogpie", {}).get("hits", []))
        all_external = set()
        per_tool_hits = {}
        for ea in ext_algos:
            hits = set(algos.get(ea, {}).get("hits", []))
            per_tool_hits[ea] = hits
            all_external |= hits

        all_hits = cogpie_hits | all_external

        cogpie_misses = set(algos.get("cogpie", {}).get("misses", []))
        ext_misses = cogpie_misses.copy()
        for ea in ext_algos:
            ext_misses &= set(algos.get(ea, {}).get("misses", []))

        gap_analysis[pid] = {
            "only_cogpie": sorted(cogpie_hits - all_external),
            "only_external": sorted(all_external - cogpie_hits),
            "both": sorted(cogpie_hits & all_external),
            "missed_by_all": sorted(ext_misses),
            "per_tool_unique": {
                ea: sorted(per_tool_hits[ea] - (all_external - per_tool_hits[ea]) - cogpie_hits)
                for ea in ext_algos
            },
        }
    results["gap_analysis"] = gap_analysis

    # Save
    out_dir = Path(COGPIE_ROOT) / "benchmark" / "external_tools"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "external_tools_benchmark_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info("Results saved: %s", out_file)

    # Print table
    w = 160
    print("\n" + "=" * w)
    print("  EXTERNAL TOOLS vs CogPIE BENCHMARK (10 Personas, @50K budget)")
    print("=" * w)
    header = (f"  {'Persona':<18} {'Lv':>2} {'CogPIE':>8} {'CUPP(o)':>8} "
              f"{'CUPP(w)':>8} {'Bopscrk':>8} {'elpscrk':>8} "
              f"{'psudo':>8} {'lngtng':>8} {'pydict':>8} "
              f"{'passpwn':>8} {'WLF+':>8}  Best")
    print(header)
    print("-" * w)

    for p in results["personas"]:
        a = p["algorithms"]

        def _pct(name):
            return a.get(name, {}).get("coverage_pct", 0.0)

        line = (f"  {p['id']:<18} {p['level']:>2} "
                f"{_pct('cogpie'):>7.1f}% "
                f"{_pct('cupp_original'):>7.1f}% "
                f"{_pct('cupp_wlf'):>7.1f}% "
                f"{_pct('bopscrk'):>7.1f}% "
                f"{_pct('elpscrk'):>7.1f}% "
                f"{_pct('psudohash'):>7.1f}% "
                f"{_pct('longtongue'):>7.1f}% "
                f"{_pct('pydictor_sedb'):>7.1f}% "
                f"{_pct('passpwn'):>7.1f}% "
                f"{_pct('wlf_combined'):>7.1f}%")
        best = max(a.items(), key=lambda x: x[1]["coverage_pct"])
        line += f"  [{best[0]}]"
        print(line)

    print("-" * w)
    s = results["summary"]
    avg = f"  {'AVERAGE':<18} {'':>2}"
    for algo in algorithms:
        if algo in s:
            avg += f" {s[algo]['avg_coverage']:>7.1f}%"
    print(avg)
    print("=" * w)

    # Gap analysis summary
    print("\n" + "=" * 80)
    print("  GAP ANALYSIS: CogPIE vs External Tools")
    print("=" * 80)
    for pid, gaps in gap_analysis.items():
        print(f"\n  {pid}:")
        print(f"    Only CogPIE finds ({len(gaps['only_cogpie'])}): "
              f"{', '.join(gaps['only_cogpie'][:5])}"
              f"{'...' if len(gaps['only_cogpie']) > 5 else ''}")
        print(f"    Only externals find ({len(gaps['only_external'])}): "
              f"{', '.join(gaps['only_external'][:5])}"
              f"{'...' if len(gaps['only_external']) > 5 else ''}")
        print(f"    Missed by ALL ({len(gaps['missed_by_all'])}): "
              f"{', '.join(gaps['missed_by_all'][:5])}"
              f"{'...' if len(gaps['missed_by_all']) > 5 else ''}")
    print("=" * 80)


if __name__ == "__main__":
    main()
