# Tool API Inspection: Profile-Based Wordlist Generators (Batch 1)

> Inspected 2026-10-21 for CogPIE benchmark integration

## 1. CUPP (Mebus/cupp)

**Can import as module:** Yes, with patching. The `generate_wordlist_from_profile(profile)` function is defined at module level but writes to file via `print_to_file()` which calls `input()` (Hyperspeed print prompt). Not cleanly importable without monkeypatching.

**Profile dict structure:**
```python
profile = {
    "name": "joao",           # first name (required, lowercase)
    "surname": "silva",       # last name
    "nick": "jsilva",         # nickname
    "birthdate": "15031990",  # DDMMYYYY
    "wife": "maria",          # partner's name
    "wifen": "mari",          # partner's nickname
    "wifeb": "22071992",      # partner's birthdate DDMMYYYY
    "kid": "pedro",           # child's name
    "kidn": "pedrinho",       # child's nickname
    "kidb": "10052015",       # child's birthdate DDMMYYYY
    "pet": "rex",             # pet name
    "company": "acme",        # company name
    "words": ["futebol", "flamengo"],  # keywords
    "spechars1": "y",         # add special chars (y/n)
    "randnum": "y",           # add random numbers (y/n)
    "leetmode": "y",          # leet mode (y/n)
}
```

**How to call programmatically (workaround):**
```python
import sys, os
sys.path.insert(0, "cupp/")
import cupp
cupp.read_config(os.path.join("cupp", "cupp.cfg"))

profile = {
    "name": "joao", "surname": "silva", "nick": "jsilva",
    "birthdate": "15031990", "wife": "maria", "wifen": "mari",
    "wifeb": "22071992", "kid": "pedro", "kidn": "pedrinho",
    "kidb": "10052015", "pet": "rex", "company": "acme",
    "words": ["futebol", "flamengo"],
    "spechars1": "y", "randnum": "y", "leetmode": "y",
}
# Must monkeypatch print_to_file and input to capture output
import io
captured = []
original_print_to_file = cupp.print_to_file
cupp.print_to_file = lambda fname, lst: captured.extend(lst)
cupp.generate_wordlist_from_profile(profile)
cupp.print_to_file = original_print_to_file
# captured now has the wordlist
```

**Output:** list of strings (written to `{name}.txt` normally)
**Fields:** 12 fields (name, surname, nick, birthdate, wife, wifen, wifeb, kid, kidn, kidb, pet, company) + words list

---

## 2. bopscrk (r3nt0n/bopscrk)

**Can import as module:** Partially. It's heavily CLI-coupled. The `args` module parses `sys.argv` at import time. The `main.run()` function relies on the global `args` state.

**Profile input:** Words are passed as a flat comma-separated list via `-w`. There's no structured profile dict; all personal data is flattened into the word list.

**CLI approach (most reliable):**
```bash
python -m bopscrk -w joao,silva,maria,rex,acme,futebol,flamengo,1990,2015 \
    -m 4 -M 20 -n 2 -c -l -o output.txt
```

**Programmatic workaround:**
```python
import sys
sys.argv = ["bopscrk", "-w", "joao,silva,maria,rex,acme,futebol,flamengo,15031990",
            "-m", "4", "-M", "20", "-n", "2", "-c", "-l", "-o", "/dev/stdout"]
# Then import and run, but beware of argparse side effects
```

**Fields:** Flat list of words (no structured profile), dates split into components, artists for lyrics
**Output:** File (default tmp.txt)

---

## 3. elpscrk (D4Vinci/elpscrk)

**Can import as module:** Partially. Uses `click` decorators and interactive `input()` prompts. The `main_ganerator` class IS instantiable programmatically but it reads inputs from `perm_classes` global instances.

**Profile input via perm_classes:**
```python
# perm_classes.py has these global instances:
# names_perm(names_list, complicated=level)
# dates_perm(dates_list_in_DD-MM-YYYY, complicated=level)
# phones_perm(phones_list_in_E164, complicated=level)
# oldpwds (old passwords class)
```

**Programmatic approach:**
```python
import sys
sys.path.insert(0, "elpscrk/")
from perm_classes import names_perm, dates_perm, phones_perm, data_plus

# Must create perm class instances with target data
names = names_perm(["joao", "silva", "maria"], complicated=1)
dates = dates_perm(["15-03-1990", "22-07-1992"], complicated=1)
# Then set as module-level globals before calling main_ganerator
```

**Fields:** names, dates (DD-MM-YYYY), phone numbers (E.164), old passwords, keywords
**Output:** File (default passwords.txt), list in `self.total_result`
**Dependencies:** psutil, click, phonenumbers

---

## 4. psudohash (t3l3machus/psudohash)

**Can import as module:** No clean API. All logic is at module level with `argparse.parse_args()` at import time. It writes directly to output file.

**CLI approach (only reliable method):**
```bash
python3 psudohash.py -w joao,silva,maria,rex,acme \
    -c -cpa -an 2 -y 1990,2015,2026 -o output.txt
```

Flags:
- `-w`: comma-separated keywords
- `-c`: all-order combinations (up to `--max-combine`)
- `-cpa`: common paddings after
- `-an LEVEL`: append numbering (1=1..100, 2=01..100, 3=001..100)
- `-y`: years to append
- `-o`: output file

**Fields:** Flat keyword list only (no structured profile)
**Output:** File (default output.txt)
**Dependencies:** tqdm

---

## 5. pydictor (LandGrey/pydictor) - SEDB mode

**Can import as module:** No. The SEDB class extends `cmd.Cmd` (interactive shell). It reads field values via `do_set` commands.

**SEDB Profile fields:**
```
cname     - Chinese/native name
ename     - English name
sname     - Surname/family name
birth     - Birthday (DDMMYYYY)
usedpwd   - Known old passwords
phone     - Phone number
uphone    - Partner's phone
hphone    - Home phone
email     - Email address
postcode  - Postal code
nickname  - Nickname
idcard    - ID card number
jobnum    - Job/employee number
otherdate - Other important dates (DDMMYYYY)
usedchar  - Frequently used characters/words
```

**CLI approach:**
```bash
# Must use the interactive SEDB shell, or craft a script:
echo "set cname joao
set ename joao
set sname silva
set birth 15031990
set nickname jsilva
set usedchar futebol,flamengo
run" | python3 pydictor.py --sedb
```

**Fields:** 15 fields (richest profile of all tools)
**Output:** File in results/ directory
**Dependencies:** Python stdlib only

---

## 6. ComPP (sec-it/ComPP)

**Can import as module:** Yes, with config setup. The `bake(fields)` function takes a flat list and generates all variants.

**Profile input:** Company-focused: company names, zip codes, cities, keywords (all flattened to one list).

**Programmatic approach:**
```python
import sys, json, os
sys.path.insert(0, "ComPP/")
sys.argv = ["compp", "-p", "2", "-l", "-n", "-o", "/tmp/compp_out.txt"]

# Must set up config before calling
from ComPP.compp import bake, get_parser, main
# Or use JSON input:
# python3 -m ComPP example.json -p 2 -l -n -o output.txt
```

**JSON input format:**
```json
{
    "company": ["Acme", "ACME Corp"],
    "zip_codes": ["01310"],
    "cities": ["Sao Paulo"],
    "keywords": ["security", "admin"]
}
```

**Fields:** company names, zip codes, cities, keywords
**Output:** File or stdout
**Dependencies:** colorama

---

## 7. longtongue (edoardottt/longtongue)

**Can import as module:** Yes, by constructing Person/Company objects. The `person()` function takes the Person object and generates the wordlist.

**Profile class (Person):**
```python
class Person:
    name, middle_name, surname, nickname, username, age,
    birth_day, birth_month, birth_year, email, birth_place,
    first_pet, second_pet, favourite_band, person_keywords
```

**Programmatic approach:**
```python
import sys
sys.path.insert(0, "longtongue/src/")
from longtongue.cli import Person, person, attr_keywords_in_unique_list

target = Person()
target.name = "Joao"
target.surname = "Silva"
target.nickname = "jsilva"
target.birth_day = "15"
target.birth_month = "03"
target.birth_year = "1990"
target.email = "joao@acme.com"
target.first_pet = "Rex"
target.person_keywords = ["futebol", "flamengo"]

# Must monkeypatch input_person() or call person() after setting target
# The person() function calls input_person() internally, so
# best to refactor the flow or pipe stdin
```

**Fields:** 14 fields (name, middle_name, surname, nickname, username, age, birth_day, birth_month, birth_year, email, birth_place, first_pet, second_pet, favourite_band) + keywords
**Output:** File in output/ directory
**Dependencies:** Python stdlib only

---

## Summary: Programmatic Integration Feasibility

| Tool | Clean API | Profile Fields | Best Invocation | Output |
|------|-----------|---------------|-----------------|--------|
| cupp | Monkeypatch `print_to_file` | 12 + keywords | Python import + patch | list -> file |
| bopscrk | CLI only | Flat words | subprocess CLI | file |
| elpscrk | Construct perm_classes | names, dates, phones, old_pwds | Python import (complex) | file |
| psudohash | CLI only | Flat keywords | subprocess CLI | file |
| pydictor | Interactive SEDB | 15 fields | stdin pipe or subprocess | file |
| ComPP | JSON input | company, zips, cities, keywords | subprocess or import | file/stdout |
| longtongue | Python import (partial) | 14 + keywords | Python import + monkeypatch | file |

**Recommendation for benchmark:** Use subprocess calls for bopscrk, psudohash, pydictor. Use Python import with monkeypatching for cupp and longtongue. ComPP can be called via JSON input file. elpscrk needs custom perm_classes construction.
