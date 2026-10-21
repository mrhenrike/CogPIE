# Tool API Inspection: Batch 2 (Smaller/Profile-Based Tools)

> Author: Andre Henrique (@mrhenrike)
> Date: 2026-10-21
> Purpose: Determine programmatic APIs for 10 wordlist tools to enable automated benchmarking against CogPIE.

## Summary

| # | Tool | Importable? | Profile-Based? | Programmatic API? | Notes |
|---|------|-------------|----------------|-------------------|-------|
| 1 | BEWGor | No | Yes | No | Python 2 only, 141x raw_input, fully interactive |
| 2 | wister | Partial | No (word-based) | Yes (via control.control) | Takes word list, applies mutations (type1-type5) |
| 3 | TTPassGen | No | No | No (CLI only via click) | Combinatoric mask/rule generator, click-based CLI |
| 4 | Mikara | No | Yes | No | Python 3 but fully interactive (input() calls) |
| 5 | PassPro | No | No (word-based) | No | Leet permutation of words, argparse-based CLI |
| 6 | passpwn | Yes | Partial (company) | Yes (generate_spray) | Company-focused spray list generator |
| 7 | pwg | Partial | Yes | Yes (via Pattern+Profile+Generator) | Pattern DSL (.ppwg) + JSON profile (.pwg) |
| 8 | CrackSmith | Yes | Yes | Yes (profile_generator) | Python 3, profile dict -> generator, has CLI mode |
| 9 | RSMangler | No | No (word-based) | No | Ruby, stdin/file-based word mangling |
| 10 | weakpass | No | No | No | Hash lookup API, not a wordlist generator |

---

## 1. BEWGor

**Language:** Python 2
**File:** `BEWGor.py` (2,544 lines, single file)
**Can import:** No. Uses `raw_input()` (Python 2), global variables, writes directly to file.
**Profile fields:** Subject name, maiden name, nicknames, birth date, birth year, gender, nationality, hometown, associates' names/dates, phone numbers, additional words/numbers.
**Generation logic:** `bounded_permutations()` creates all permutations of collected tokens within min/max length bounds.
**API:** None. Fully interactive with 141 `raw_input()` calls.
**Verdict:** Cannot be benchmarked programmatically without rewriting. Would need a subprocess with pexpect or a complete rewrite.

---

## 2. wister

**Language:** Python 3
**Package:** `wister/` with `control.py`, `modes.py`, `utils.py`
**Can import:** Partially. The `control.control(argv)` function drives the pipeline but expects an argparse namespace.
**Profile fields:** Not profile-based. Accepts a list of words (via `-w` or file).
**Generation logic:** 5 mutation types:
  - type1: word mixing (concatenation of 2-5 words)
  - type2: case alternation
  - type3: leet substitution
  - type4: number append (0-9, 00-99, etc.)
  - type5: symbol append
**API:**
```python
import sys
sys.path.insert(0, "wister")
from wister.modes import type1, type2, type3, type4, type5

words = ["john", "smith", "2024"]
final = list(words)
final = type1(0, 50, words, final, False, 3, [0, 1], False)
final = type2(words, final, False, [0, 1], False)
# etc.
```
**Verdict:** Usable for mutation benchmarking on base words, not profile-based.

---

## 3. TTPassGen

**Language:** Python 3
**Package:** `ttpassgen/ttpassgen.py`
**Can import:** No practical API. Uses `click` CLI framework and is designed as a pure combinatoric generator with mask/rule DSL.
**Profile fields:** None. Takes charset rules like `[?l]{6:8}` or `$(word1,word2){1:2}`.
**Generation logic:** CharArrayRule (charset permutation), DictRule (dictionary reference), StringArrayRule (string combinations). Multi-process generation.
**API:** CLI only via `ttpassgen --rule "[?l]{6:8}" -o output.txt`
**Verdict:** Combinatoric tool, not profile-based. Not suitable for persona benchmark.

---

## 4. Mikara

**Language:** Python 3
**Files:** `mikara.py`, `mods/functions.py`, `mods/args.py`
**Can import:** Not directly. Uses global `profile` dict and `global_list` with `input()` calls.
**Profile fields:** fullname, nickname, birthday (DD-MM-YYYY), significant year, pets, mother/father/partner names, children names/nicks, country/state/city (birth + residence), company, interests, extra keywords.
**Generation logic:**
  - set_0/00/000: solo/pair/triple permutations of profile values
  - set_1/11/111: prepend/middle/append common numbers/symbols
  - set_2/22/222: case variations + combinations
  - set_3/33/333: additional complexity layers
**API:** Can be hacked by injecting `profile` dict directly:
```python
# Requires patching: replace input() calls with dict injection
# mods/functions.py uses global profile dict
import sys
sys.path.insert(0, "Mikara")
from mods.functions import global_list, set_0, set_00, set_000
# Would need to set mods.functions.profile = {...} and mods.functions.size = "4"
# Then call set_0(), set_00(), etc. and read global_list
```
**Verdict:** Hackable for benchmarking with monkey-patching, but fragile.

---

## 5. PassPro

**Language:** Python 3
**File:** `PassPro.py` (single file)
**Can import:** No practical API. CLI-only with argparse.
**Profile fields:** None. Takes a single word or file of words.
**Generation logic:** `permute_word()` generates leet variations using a character substitution alphabet. `scramble_words()` creates n-length combinations. `walk_keyboard()` generates keyboard walk patterns.
**API:** CLI: `python PassPro.py -w password --l33t` or `python PassPro.py -f words.txt --scramble --num 2`
**Verdict:** Word mutation tool, not profile-based. Could be used for leet transformation benchmarking only.

---

## 6. passpwn

**Language:** Python 3
**File:** `passpwn.py` (999 lines, well-structured)
**Can import:** Yes. Clean function-based architecture.
**Profile fields:** Company words, addresses, custom keywords, usernames/names (for per-user mode).
**Generation logic:**
  - `collect_base_words()`: builds targeted + builtin word lists
  - `mutations_for_word()`: tiered mutations (capitalize+suffix, year+symbol, leet, season/month combos)
  - `generate_spray()`: prioritized spray list (most-likely-first)
  - `generate_per_user()`: per-identity candidate lists with overlay
**API:**
```python
import sys
sys.path.insert(0, "passpwn")
from passpwn import collect_base_words, generate_spray

targeted, builtin = collect_base_words(
    company_words=["acme", "acmecorp"],
    addresses=["springfield"],
    custom=["dragon", "batman"],
)
spray = generate_spray(
    targeted_words=targeted,
    builtin_words=builtin,
    years=[2024, 2025, 2026],
    no_seasons=False,
    no_months=False,
    include_leet=True,
    min_len=8,
    max_len=64,
    complexity=set(),
    max_spray=50000,
)
# spray is a list of strings, ordered most-likely-first
```
**Verdict:** Good for company/spray benchmarking. Not personal-profile-based (no names, dates, pets).

---

## 7. pwg (Personal Wordlist Generator)

**Language:** Python 2/3
**Files:** `pwg.py`, `core/Profile.py`, `core/Generator.py`, `core/Pattern.py`
**Can import:** Yes, with caveats (uses `exrex` library dependency).
**Profile fields:** Defined by JSON profile file (.pwg). Categories can include names, dates, hobbies, etc.
**Generation logic:** Pattern DSL (.ppwg files) define how profile fields are combined. Generator resolves patterns against profile values using `exrex` for regex expansion.
**API:**
```python
import sys, json
sys.path.insert(0, "pwg")
from core.Profile import Profile
from core.Generator import Generator
from core.Pattern import Pattern

profile_data = {
    "names": {"first": "joao", "last": "silva"},
    "dates": {"birth": "15081990"},
    "hobbies": {"hobby_A": "football"}
}
profile = Profile(profile_data)
# Requires .ppwg pattern file defining generation rules
# pattern = Pattern("patterns/default.ppwg")
# gen = Generator(pattern, profile)
```
**Verdict:** Most flexible profile-based tool in this batch, but requires pattern file and exrex dependency. Good architecture for comparison.

---

## 8. CrackSmith

**Language:** Python 3
**File:** `CrackSmith.py` (726 lines)
**Can import:** Yes. Clean architecture with `profile_generator()` function.
**Profile fields:** first, last, nick, bday (year), bmonth, bday2 (day), partner, pet, company, hobby, phone (last 4).
**Generation logic:**
  - `expand_word()`: case variations + full leet permutations (10 chars: a,e,i,o,s,t,b,g,l,z)
  - `profile_generator()`: yields singles+suffixes, pairs with separators, triplets
  - Suffixes: 27 standard + 22 complex (digit+symbol combos)
  - Prefixes: "the", "my", "i", "mr", "super", "mega", etc.
  - Separators: "", "_", ".", "-", "@", "!", "#"
**API:**
```python
import sys
sys.path.insert(0, "CrackSmith")
from CrackSmith import profile_generator

data = {
    "first": "joao",
    "last": "silva",
    "nick": "jsilva",
    "bday": "1990",
    "pet": "rex",
    "company": "acme",
}
candidates = []
for pwd in profile_generator(data, leet=True, combos=2):
    candidates.append(pwd)
    if len(candidates) >= 50000:
        break
```
**Verdict:** Best programmatic API in this batch. Profile-based, clean generator pattern, leet+case+suffix+combo. Suitable for benchmark.

---

## 9. RSMangler

**Language:** Ruby
**File:** `rsmangler.rb` (433 lines)
**Can import:** No (Ruby).
**Profile fields:** None. Takes a wordlist file or stdin.
**Generation logic:** Per-word mangles:
  - Case: upper, lower, swap, capitalize
  - Leet: s->$, e->3, a->4/@, o->0, i->1/!, l->1/!, t->7, b->8, z->2
  - Suffixes: numbers 1-123, years, "ed", "ing"
  - Reverse, double, acronym
  - Permutations of all input words (optional, explosive)
  - Common words prepend/append ("pw", "pwd", "admin", "sys")
**API:** CLI: `cat words.txt | ruby rsmangler.rb --leet --capital --years`
**Subprocess invocation:**
```python
import subprocess
result = subprocess.run(
    ["ruby", "RSMangler/rsmangler.rb", "-f", "words.txt", "--leet", "--capital"],
    capture_output=True, text=True
)
candidates = result.stdout.strip().split("\n")
```
**Verdict:** Must use subprocess. Good mangling engine for comparison but not profile-based.

---

## 10. weakpass

**Language:** Python 3 (weakpass.py) + JavaScript (web tools)
**File:** `weakpass.py` (hash lookup only)
**Can import:** Yes, but it's a hash lookup tool, NOT a generator.
**Profile fields:** None.
**Generation logic:** None. The `tools/weakpass-tools/` is a Vue.js web app. The `rules/` directory contains hashcat rule files (nsa64.rule, top_250.rule, etc.).
**API:** `fetch_search(hash_value)` returns `HashResponse` with type/hash/value. This is for looking up known hashes, not generating wordlists.
**Verdict:** Not a wordlist generator. The rules files are useful reference material but cannot be benchmarked as a standalone tool. The web app at weakpass.com generates wordlists but has no local API.

---

## Benchmark Viability Summary

### Directly benchmarkable (programmatic API):
1. **CrackSmith** - `profile_generator(data, leet, combos)` -> yields candidates
2. **passpwn** - `generate_spray(...)` -> ordered list, company-focused
3. **wister** - `type1..type5(words, ...)` -> mutated word list (not profile-based)

### Benchmarkable with monkey-patching:
4. **Mikara** - Inject profile dict into global, call set_0..set_333()
5. **pwg** - Requires .ppwg pattern file + exrex dependency

### Subprocess only (Ruby):
6. **RSMangler** - `ruby rsmangler.rb -f words.txt --flags`

### Not benchmarkable:
7. **BEWGor** - Python 2, fully interactive, would need pexpect
8. **TTPassGen** - Combinatoric only, not profile-based
9. **PassPro** - Word mutation only, not profile-based
10. **weakpass** - Hash lookup, not a generator
