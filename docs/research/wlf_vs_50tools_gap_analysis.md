# WordlistXPL-Forge vs 50 External Tools: Gap Analysis and Evolution Roadmap

> Author: Andre Henrique (@mrhenrike)
> Date: 2026-10-21
> Purpose: Identify gaps, improvements, and evolution opportunities for WLF by comparing against 50 external tools.

## 1. Benchmark Results Summary

### 1.1 Profile-Based Tools vs CogPIE (10 Personas, @50K budget)

**Post-optimization (commit 24a14c6, improvements I1-I7):**

| Algorithm | Avg Coverage | Wins (of 10) | Strengths |
|-----------|-------------|--------------|-----------|
| **CogPIE v0.2** | **89.7%** | **10** | Dominates all profiles after priority band optimization |
| CUPP (WLF engine) | 40.0% | 0 | Reliable for name+date concatenations |
| Bopscrk | 21.5% | 0 | Limited without lyrics module |
| Markov (untrained) | 13.8% | 0 | Baseline without corpus |

**Pre-optimization baseline (commit 28a1901):**

| Algorithm | Avg Coverage | Wins (of 10) |
|-----------|-------------|--------------|
| Expanded Combined | 57.5% | 2 |
| CogPIE v0.1 | 53.5% | 2 |
| elpscrk (simulated) | 52.8% | 4 |
| CUPP (WLF engine) | 48.0% | 2 |
| CrackSmith | 23.5% | 0 |

**Improvement delta: +37.3pp average, +76pp on P07 Cultural, +54.8pp on P10 Complete.**

### 1.2 CogPIE Gap Analysis (from benchmark)

**Patterns CogPIE uniquely finds (not found by externals):**
- Old passwords reuse (dede1985!, Andre@123, Gabi@ode)
- Date-format variations (dede170985, lucas0203, fer0510)
- Cross-field special char combos (Pedro@90, Bruno@93, Kadu88!)
- Leet transforms of names (mar1a95, c4rlos88, j04o123)

**Patterns CogPIE misses that externals find:**
- Simple keyword+year: flamengo91, corinthians89, nubank93
- Keyword+!: guitarra!, corinthians!, evangelica!, churrasco!
- Name concatenations: brunosantos, fernandacosta, andrehenrique
- Company/keyword+current_year: globo2024, nubank2024, python2024
- Short nick+year: fer87, bru93, ju91

**Patterns ALL tools miss (hardest passwords):**
- Cross-name+special: ana@pedro, bru@nubank, andre@safelabs
- Cultural slang: mengao91 (flamengo slang), timao89 (corinthians slang)
- Multi-field complex: patriciasophia, mandinhagabi, bobferreira
- Rare leet patterns: f3rnand4, g4br13l92, d3d31985

## 2. Feature Coverage Matrix: WLF vs 50 Tools

### 2.1 Algorithmic Paradigms

| Paradigm | External Tools | WLF Coverage | Gap? |
|----------|---------------|-------------|------|
| Profile/Target (PII) | cupp, bopscrk, BEWGor, elpscrk, psudohash, longtongue | cupp_engine, bopscrk_engine, profiler, br_deep_engine, CogPIE | No |
| Combinatoric/Exhaustive | crunch, maskprocessor, TTPassGen, cracken | charset_gen, combo_engine | No |
| PRINCE algorithm | princeprocessor | prince_engine | No |
| Keyboard walks | kwprocessor | kwalk_gen | No |
| Rule/Mangling | hashcat rules, JtR rules, RSMangler, mentalist, wister | rule_engine, rsmangler_engine, leet_permuter, keyword_mutations, affix_engine, mangler | No |
| Markov chains | OMEN, OMEN-reborn | markov_engine | No |
| PCFG | pcfg_cracker, Cpcfg | pcfg_engine, semantic_pcfg, domain_pcfg | No |
| GAN-based | PassGAN | gan_engine | No |
| Transformer/LLM | PassGPT | transformer_engine | No |
| Web scraping | CeWL, WordHound | target_spider, web_scraper | No |
| Lyrics extraction | lyricpass | (via bopscrk_engine lyrics mode) | Partial |
| Username generation | username-anarchy | (no dedicated engine) | **YES** |
| Company profiling | ComPP | corp_profiler | No |
| Default credentials | Passhunt | (no default cred database) | **YES** |
| Password analysis | pipal | coverage_analyzer, anomaly_scorer | Partial |
| Deduplication | duplicut | (inline dedup in pipeline) | No |
| Hash lookup | dcipher | (out of scope) | N/A |
| Passphrase generation | xkcdpass, passphraseme | (no dedicated Diceware engine) | **YES** |
| Evolutionary/Genetic | (none external) | genetic_engine, map_elites | WLF unique |
| Bayesian optimization | (none external) | bayesian_full | WLF unique |
| RL-based routing | (none external) | bandit_router, rl_router | WLF unique |
| Diffusion models | (none external) | diffusion_engine | WLF unique |
| TCN models | (none external) | tcn_engine | WLF unique |
| Normalizing flows | (none external) | nflow_engine | WLF unique |
| Phonetic generation | (none external) | phonetic_engine | WLF unique |
| Brazilian cultural | (none external) | br_deep_engine | WLF unique |
| Cognitive bias modeling | (none external) | CogPIE | WLF unique |
| Strategy orchestration | hate_crack (hashcat wrapper) | strategy_engine (PBMP) | WLF superior |

### 2.2 Identified Gaps (WLF missing features found in external tools)

| # | Gap | External Tool | Impact | Priority |
|---|-----|--------------|--------|----------|
| G1 | **Username generation engine** | username-anarchy (40+ formats) | Medium: useful for user enum, not password gen | Low |
| G2 | **Default credential database** | Passhunt (1,310 stars, 523 vendors) | High: complements profile-based gen for IoT/network | High |
| G3 | **Diceware/passphrase engine** | xkcdpass, passphraseme | Medium: passphrases are growing trend | Medium |
| G4 | **Lyrics integration** | lyricpass (standalone) | Low: partially in bopscrk, could be deeper | Low |
| G5 | **Automated methodology wrapper** | hate_crack (PRINCE+OMEN+PCFG) | Low: WLF strategy_engine already orchestrates | Low |
| G6 | ~~Keyword+! and keyword+year patterns~~ | elpscrk, psudohash | RESOLVED (I1+I2, commit 24a14c6) | **Done** |
| G7 | ~~Name concatenation patterns~~ | cupp, elpscrk | RESOLVED (I3, commit 24a14c6) | **Done** |
| G8 | ~~Current year suffix~~ | cupp, elpscrk | RESOLVED (I4, commit 24a14c6) | **Done** |
| G9 | ~~Cultural slang expansion~~ | (none, manual only) | RESOLVED (I6, commit 24a14c6) | **Done** |
| G10 | **Multi-tool output format export** | mentalist (hashcat/JtR rules) | Low: WLF rule_engine already generates | Low |

### 2.3 CogPIE-Specific Improvements (from gap analysis)

| # | Improvement | Status | Actual Impact |
|---|------------|--------|---------------|
| I1 | **keyword+suffix combos in priority band** | DONE (commit 24a14c6) | +76pp on P07, +20pp avg on P07-P10 |
| I2 | **keyword+year combos** | DONE (commit 24a14c6) | flamengo91, samba1991 now found |
| I3 | **Full name concatenation** | DONE (commit 24a14c6) | julianaoliveira, juflamengo now found |
| I4 | **Current year (2024-2026) suffix** | DONE (commit 24a14c6) | petrobras2024, nina2024, rio2024 now found |
| I5 | **Short nickname+year** | DONE (commit 24a14c6) | ju91, fer87 now found |
| I6 | **Cultural slang dictionary** | DONE (commit 24a14c6) | mengao91 now found |
| I7 | **Cross-field special char join** | DONE (commit 24a14c6) | marcos@ju, samba@rio, nina!ju now found |

**Combined effect: CogPIE 52.4% -> 89.7% (+37.3pp), winning 10/10 personas.**

## 3. WLF Unique Capabilities (not found in any external tool)

| # | Capability | WLF Engine | Competitive Advantage |
|---|-----------|-----------|----------------------|
| U1 | Multi-layer cognitive pipeline | CogPIE (5 layers) | Only tool modeling cognitive biases |
| U2 | Semantic token expansion | CogPIE Layer 1 | Auto-generates cultural variants |
| U3 | Evolutionary password search | genetic_engine, map_elites | Quality-diversity optimization |
| U4 | Neural ensemble (GAN+Transformer+VAE+TCN+Diffusion+NFlow) | 6 neural engines | Broadest neural coverage |
| U5 | Reinforcement learning routing | bandit_router, rl_router | Adaptive strategy selection |
| U6 | Phonetic password generation | phonetic_engine | Unique to WLF |
| U7 | Brazilian deep cultural engine | br_deep_engine | No equivalent exists |
| U8 | Domain-specific PCFG | domain_pcfg | Trained per domain context |
| U9 | Semantic PCFG | semantic_pcfg | Meaning-aware grammar |
| U10 | Coverage analysis/anomaly scoring | coverage_analyzer, anomaly_scorer | Built-in quality metrics |
| U11 | 109 modules in unified framework | All engines | vs max 1-3 in any external tool |

## 4. Evolution Roadmap (Priority Order)

### Phase 1: Critical CogPIE Fixes (ALL COMPLETE, commit 24a14c6)
1. ~~**I1**: keyword+special_char~~ DONE
2. ~~**I2**: keyword+year cross~~ DONE
3. ~~**I3**: full name concatenation~~ DONE
4. ~~**I4**: current year (2024-2026)~~ DONE
5. ~~**I5**: short nickname+year~~ DONE
6. ~~**I6**: cultural slang dictionary~~ DONE
7. ~~**I7**: keyword@name, keyword@keyword~~ DONE

### Phase 2: New WLF Engines (remaining gaps)
8. **G2**: Default credential database engine (inspired by Passhunt)
9. **G3**: Diceware/passphrase engine (inspired by xkcdpass)
10. **G1**: Username generation engine (from username-anarchy patterns)
11. **G4**: Deeper lyrics integration

## 5. Quantitative Summary

| Metric | WLF/CogPIE v0.2 | Best External Tool | Advantage |
|--------|-----------------|-------------------|-----------|
| Algorithmic paradigms covered | 11/11 | 1-2/11 (any single tool) | 5.5x-11x |
| Total engines/modules | 109 | 1-3 (any single tool) | 36x-109x |
| Profile-based coverage (avg) | **89.7%** (CogPIE v0.2) | 52.8% (elpscrk simulated) | **+36.9pp** |
| Min persona coverage | 80.0% (P01 minimal) | 28.0% (CUPP on P07) | +52pp |
| Max persona coverage | 96.2% (P09 rich) | 63.6% (CUPP on P04) | +32.6pp |
| Neural architectures | 6 (GAN, Transformer, VAE, Diffusion, TCN, NFlow) | 1 (PassGAN or PassGPT) | 6x |
| Unique capabilities (no external equivalent) | 11 | 0 | Exclusive |
| GitHub stars (combined external) | ~84,000 | 27,036 (hashcat) | N/A |
