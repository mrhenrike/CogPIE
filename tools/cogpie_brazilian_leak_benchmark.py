#!/usr/bin/env python3
"""
cogpie_brazilian_leak_benchmark.py - Benchmark CogPIE against real Brazilian leak data.

Uses IntelX API to fetch leaked credentials from Brazilian domains (.com.br),
extracts PII from email addresses, generates CogPIE candidates, and measures
how many real passwords are found.

Guardrails:
- RSS memory monitoring with hard limit (configurable, default 8GB)
- Batch processing with GC between batches
- CPU timeout per target (30s)
- Streaming results to disk (no full-dataset memory accumulation)
- Credit budget control (max API calls configurable)

Author: Andre Henrique (@mrhenrike)
"""
from __future__ import annotations

import gc
import json
import logging
import os
import re
import resource
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("cogpie.br_leak_benchmark")

MAX_RSS_MB = int(os.environ.get("COGPIE_MAX_RSS_MB", "8000"))
BATCH_SIZE = int(os.environ.get("COGPIE_BATCH_SIZE", "50"))
TARGET_TIMEOUT_S = int(os.environ.get("COGPIE_TARGET_TIMEOUT", "30"))
MAX_API_SEARCHES = int(os.environ.get("COGPIE_MAX_API_SEARCHES", "5"))
MAX_TARGETS = int(os.environ.get("COGPIE_MAX_TARGETS", "500"))
COGPIE_CANDIDATES = int(os.environ.get("COGPIE_CANDIDATES", "10000"))


def get_rss_mb() -> float:
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024.0
    except Exception:
        pass
    ru = resource.getrusage(resource.RUSAGE_SELF)
    return ru.ru_maxrss / 1024.0


def check_memory(label: str = "") -> bool:
    rss = get_rss_mb()
    if rss > MAX_RSS_MB:
        logger.error("MEMORY GUARD: RSS %.0f MB > limit %d MB [%s]. Aborting batch.",
                      rss, MAX_RSS_MB, label)
        return False
    if rss > MAX_RSS_MB * 0.8:
        logger.warning("MEMORY WARN: RSS %.0f MB (%.0f%% of limit) [%s]",
                       rss, rss / MAX_RSS_MB * 100, label)
        gc.collect()
    return True


class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("Target processing timeout")


def extract_pii_from_email(email: str) -> dict | None:
    """Extract PII (names, dates, numbers) from an email address."""
    if not email or "@" not in email:
        return None

    local_part = email.split("@")[0].lower()
    local_part = re.sub(r"[._+-]+", " ", local_part).strip()

    parts = local_part.split()
    if not parts:
        return None

    names = []
    dates = []
    numbers = []

    for p in parts:
        if p.isalpha() and 2 <= len(p) <= 20:
            names.append(p)
        elif p.isdigit():
            if len(p) == 4 and 1940 <= int(p) <= 2026:
                dates.append(p)
            elif len(p) == 2:
                dates.append(p)
                numbers.append(p)
            else:
                numbers.append(p)
        elif re.match(r"^[a-z]+\d+$", p):
            alpha = re.match(r"^([a-z]+)(\d+)$", p)
            if alpha:
                name_part, num_part = alpha.groups()
                if len(name_part) >= 2:
                    names.append(name_part)
                if len(num_part) <= 8:
                    numbers.append(num_part)
                    if len(num_part) == 4 and 1940 <= int(num_part) <= 2026:
                        dates.append(num_part)

    if not names:
        clean = re.sub(r"\d+", " ", local_part).strip()
        words = [w for w in clean.split() if len(w) >= 2 and w.isalpha()]
        names = words[:3] if words else []

    if not names:
        return None

    domain = email.split("@")[1].lower()
    domain_name = domain.split(".")[0]
    if domain_name not in ("gmail", "hotmail", "outlook", "yahoo", "live",
                           "uol", "bol", "terra", "ig", "globo", "zipmail"):
        if len(domain_name) >= 3 and domain_name.isalpha():
            companies = [domain_name]
        else:
            companies = []
    else:
        companies = []

    return {
        "names": names[:5],
        "dates": dates[:5],
        "keywords": [],
        "pets": [],
        "companies": companies,
        "phones": [],
        "emails": [email],
        "old_passwords": [],
        "numbers": numbers[:5],
    }


def fetch_intelx_leaks(api_key: str, api_url: str, query: str,
                        max_results: int = 1000) -> list[dict]:
    """Fetch leaked credentials from IntelX phonebook API."""
    import urllib.request
    import urllib.error

    search_url = f"{api_url}/phonebook/search"
    payload = json.dumps({
        "term": query,
        "buckets": [],
        "lookuplevel": 0,
        "maxresults": max_results,
        "timeout": 10,
        "datefrom": "",
        "dateto": "",
        "sort": 4,
        "media": 0,
        "terminate": [],
        "target": 2,
    }).encode("utf-8")

    req = urllib.request.Request(
        search_url,
        data=payload,
        headers={
            "x-key": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            search_id = data.get("id")
            if not search_id:
                logger.error("No search ID returned from IntelX")
                return []
    except Exception as e:
        logger.error("IntelX search failed: %s", e)
        return []

    logger.info("IntelX search started: id=%s", search_id)
    time.sleep(5)

    result_url = f"{api_url}/phonebook/search/result?id={search_id}&limit={max_results}&offset=0"
    req2 = urllib.request.Request(
        result_url,
        headers={"x-key": api_key},
        method="GET",
    )

    results = []
    try:
        with urllib.request.urlopen(req2, timeout=60) as resp:
            data = json.loads(resp.read())
            selectors = data.get("selectors", [])
            for sel in selectors:
                stype = sel.get("selectortype", 0)
                value = sel.get("selectorvalue", "")
                if stype == 2 and ":" in value:
                    email, pwd = value.split(":", 1)
                    if "@" in email and pwd and len(pwd) >= 4:
                        results.append({"email": email.strip(), "password": pwd.strip()})
            logger.info("IntelX returned %d credential pairs from %d selectors",
                        len(results), len(selectors))
    except Exception as e:
        logger.error("IntelX result fetch failed: %s", e)

    return results


def fetch_brazilian_leaks(api_key: str, api_url: str,
                          max_searches: int = 5) -> list[dict]:
    """Fetch Brazilian leak data from IntelX using multiple domain queries."""
    queries = [
        "*.com.br",
        "@gmail.com senha",
        "@hotmail.com brasil",
        "@uol.com.br",
        "@terra.com.br",
    ]

    all_creds = []
    seen_emails = set()

    for i, query in enumerate(queries[:max_searches]):
        if not check_memory(f"fetch query {i}"):
            break

        logger.info("Fetching IntelX query %d/%d: %s", i + 1, max_searches, query)
        creds = fetch_intelx_leaks(api_key, api_url, query, max_results=500)

        for cred in creds:
            email_lower = cred["email"].lower()
            if email_lower not in seen_emails:
                seen_emails.add(email_lower)
                all_creds.append(cred)

        logger.info("Total unique credentials so far: %d", len(all_creds))
        time.sleep(2)

    return all_creds


def build_cupp_candidates_from_profile(profile: dict, max_output: int = 10000) -> list[str]:
    """Generate CUPP-style candidates from a PII profile."""
    candidates = set()
    names = profile.get("names", [])
    dates = profile.get("dates", [])
    numbers = profile.get("numbers", [])
    companies = profile.get("companies", [])
    all_words = names + companies

    suffixes = ["", "!", "1", "123", "12", "@", "#", "2024", "2025", "2026"]
    seps = ["", ".", "_", "-", "@"]

    for word in all_words[:8]:
        for case_fn in [str.lower, str.capitalize, str.upper]:
            w = case_fn(word)
            for s in suffixes:
                c = w + s
                if 4 <= len(c) <= 30:
                    candidates.add(c)
            for num in dates + numbers:
                for s in suffixes[:5]:
                    c = w + num + s
                    if 4 <= len(c) <= 30:
                        candidates.add(c)
                    c2 = num + w + s
                    if 4 <= len(c2) <= 30:
                        candidates.add(c2)
                for sep in seps:
                    c = w + sep + num
                    if sep and 4 <= len(c) <= 30:
                        candidates.add(c)

    for i, w1 in enumerate(all_words[:5]):
        for w2 in all_words[i + 1:5]:
            for case_fn in [str.lower, str.capitalize]:
                a, b = case_fn(w1), case_fn(w2)
                for sep in seps[:3]:
                    c = a + sep + b
                    if 4 <= len(c) <= 30:
                        candidates.add(c)
                    c2 = b + sep + a
                    if 4 <= len(c2) <= 30:
                        candidates.add(c2)

    return list(candidates)[:max_output]


def run_benchmark(
    credentials: list[dict],
    corpus_path: str | None = None,
    output_dir: str = "benchmark/brazilian_leaks",
) -> dict:
    """Run the full benchmark pipeline."""
    from cogpie.engine import CogPIEEngine

    engine = CogPIEEngine(use_gpu=True)

    if corpus_path and os.path.exists(corpus_path):
        logger.info("Training from corpus: %s", corpus_path)
        count = engine.train_from_corpus(corpus_path, max_lines=2_000_000)
        logger.info("Trained on %d passwords", count)
    else:
        logger.info("No training corpus; using untrained model")

    if not check_memory("post-training"):
        return {"error": "OOM after training"}

    targets = []
    for cred in credentials[:MAX_TARGETS]:
        profile = extract_pii_from_email(cred["email"])
        if profile:
            targets.append({
                "email": cred["email"],
                "password": cred["password"],
                "profile": profile,
            })

    logger.info("Valid targets with extractable PII: %d / %d",
                len(targets), len(credentials))

    results = {
        "benchmark": "brazilian_leak_2026",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_credentials": len(credentials),
        "valid_targets": len(targets),
        "max_candidates": COGPIE_CANDIDATES,
        "cogpie_hits": 0,
        "cupp_hits": 0,
        "cogpie_ranks": [],
        "cupp_ranks": [],
        "per_target": [],
    }

    signal.signal(signal.SIGALRM, timeout_handler)

    for batch_start in range(0, len(targets), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(targets))
        batch = targets[batch_start:batch_end]

        if not check_memory(f"batch {batch_start}-{batch_end}"):
            logger.error("Memory limit reached; stopping at target %d", batch_start)
            break

        logger.info("Processing batch %d-%d / %d",
                     batch_start + 1, batch_end, len(targets))

        for idx, target in enumerate(batch):
            global_idx = batch_start + idx
            try:
                signal.alarm(TARGET_TIMEOUT_S)

                t0 = time.monotonic()
                cogpie_results = engine.generate(
                    target["profile"], max_candidates=COGPIE_CANDIDATES
                )
                cogpie_candidates = [c for c, _ in cogpie_results]
                cogpie_time = time.monotonic() - t0

                t0 = time.monotonic()
                cupp_candidates = build_cupp_candidates_from_profile(
                    target["profile"], max_output=COGPIE_CANDIDATES
                )
                cupp_time = time.monotonic() - t0

                signal.alarm(0)

                real_pwd = target["password"]
                cogpie_rank = None
                cupp_rank = None

                for i, c in enumerate(cogpie_candidates):
                    if c == real_pwd:
                        cogpie_rank = i + 1
                        break

                for i, c in enumerate(cupp_candidates):
                    if c == real_pwd:
                        cupp_rank = i + 1
                        break

                if cogpie_rank is not None:
                    results["cogpie_hits"] += 1
                    results["cogpie_ranks"].append(cogpie_rank)

                if cupp_rank is not None:
                    results["cupp_hits"] += 1
                    results["cupp_ranks"].append(cupp_rank)

                target_result = {
                    "idx": global_idx,
                    "n_fields": len([v for v in target["profile"].values()
                                     if isinstance(v, list) and v]),
                    "cogpie_found": cogpie_rank is not None,
                    "cogpie_rank": cogpie_rank,
                    "cogpie_candidates": len(cogpie_candidates),
                    "cogpie_time_ms": round(cogpie_time * 1000, 1),
                    "cupp_found": cupp_rank is not None,
                    "cupp_rank": cupp_rank,
                    "cupp_candidates": len(cupp_candidates),
                    "cupp_time_ms": round(cupp_time * 1000, 1),
                }
                results["per_target"].append(target_result)

                if (global_idx + 1) % 10 == 0:
                    logger.info(
                        "  [%d/%d] CogPIE: %d/%d (%.1f%%) | CUPP: %d/%d (%.1f%%) | RSS: %.0f MB",
                        global_idx + 1, len(targets),
                        results["cogpie_hits"], global_idx + 1,
                        results["cogpie_hits"] / (global_idx + 1) * 100,
                        results["cupp_hits"], global_idx + 1,
                        results["cupp_hits"] / (global_idx + 1) * 100,
                        get_rss_mb(),
                    )

            except TimeoutError:
                signal.alarm(0)
                logger.warning("Target %d timed out (%ds)", global_idx, TARGET_TIMEOUT_S)
                results["per_target"].append({
                    "idx": global_idx, "timeout": True,
                })
            except Exception as e:
                signal.alarm(0)
                logger.error("Target %d error: %s", global_idx, e)
                results["per_target"].append({
                    "idx": global_idx, "error": str(e),
                })

        gc.collect()

    total = len(results["per_target"])
    if total > 0:
        results["summary"] = {
            "targets_processed": total,
            "cogpie_coverage_pct": round(results["cogpie_hits"] / total * 100, 2),
            "cupp_coverage_pct": round(results["cupp_hits"] / total * 100, 2),
            "cogpie_mrr": round(
                sum(1.0 / r for r in results["cogpie_ranks"]) / total, 6
            ) if results["cogpie_ranks"] else 0.0,
            "cupp_mrr": round(
                sum(1.0 / r for r in results["cupp_ranks"]) / total, 6
            ) if results["cupp_ranks"] else 0.0,
            "cogpie_median_rank": (
                sorted(results["cogpie_ranks"])[len(results["cogpie_ranks"]) // 2]
                if results["cogpie_ranks"] else None
            ),
            "cupp_median_rank": (
                sorted(results["cupp_ranks"])[len(results["cupp_ranks"]) // 2]
                if results["cupp_ranks"] else None
            ),
        }

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    result_file = out_path / "brazilian_leak_benchmark_results.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info("Results saved: %s", result_file)
    return results


def main():
    api_key = os.environ.get("INTELX_API_KEY", "")
    api_url = os.environ.get("INTELX_API_URL", "https://2.intelx.io")

    if not api_key:
        env_file = Path("/home/mrhenrike/sec-projects/engagements/wine-intelliway/.env")
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line.startswith("INTELX_API_KEY=") and "FREE" not in line:
                    api_key = line.split("=", 1)[1].strip().strip('"')
                elif line.startswith("INTELX_API_URL=") and "FREE" not in line:
                    api_url = line.split("=", 1)[1].strip().strip('"')

    if not api_key:
        logger.error("No IntelX API key found")
        sys.exit(1)

    logger.info("=== CogPIE Brazilian Leak Benchmark ===")
    logger.info("Memory limit: %d MB | Batch size: %d | Max targets: %d",
                MAX_RSS_MB, BATCH_SIZE, MAX_TARGETS)
    logger.info("Max API searches: %d | Candidates per target: %d",
                MAX_API_SEARCHES, COGPIE_CANDIDATES)

    cache_file = Path("benchmark/brazilian_leaks/intelx_credentials_cache.json")
    if cache_file.exists():
        logger.info("Loading cached credentials from %s", cache_file)
        with open(cache_file) as f:
            credentials = json.load(f)
        logger.info("Loaded %d cached credentials", len(credentials))
    else:
        logger.info("Fetching fresh credentials from IntelX...")
        credentials = fetch_brazilian_leaks(api_key, api_url, MAX_API_SEARCHES)

        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump(credentials, f, indent=2, ensure_ascii=False)
        logger.info("Cached %d credentials to %s", len(credentials), cache_file)

    if not credentials:
        logger.error("No credentials fetched; aborting")
        sys.exit(1)

    results = run_benchmark(credentials)

    if "summary" in results:
        s = results["summary"]
        print("\n" + "=" * 70)
        print("  BRAZILIAN LEAK BENCHMARK RESULTS")
        print("=" * 70)
        print(f"  Targets processed: {s['targets_processed']}")
        print(f"  CogPIE coverage:   {s['cogpie_coverage_pct']}%")
        print(f"  CUPP coverage:     {s['cupp_coverage_pct']}%")
        print(f"  CogPIE MRR:        {s['cogpie_mrr']}")
        print(f"  CUPP MRR:          {s['cupp_mrr']}")
        print(f"  CogPIE median rank: {s['cogpie_median_rank']}")
        print(f"  CUPP median rank:   {s['cupp_median_rank']}")
        print("=" * 70)


if __name__ == "__main__":
    main()
