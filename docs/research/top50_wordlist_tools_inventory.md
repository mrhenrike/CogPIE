# Top 50 Wordlist Generation Tools: Inventory and Algorithmic Classification

> Author: Andre Henrique (@mrhenrike)
> Date: 2026-10-21
> Purpose: Comprehensive inventory of wordlist generation tools cloned for CogPIE paper comparative benchmark.
> Local path: `/run/media/mrhenrike/Data/Projects/UniaoGeek/tools/wordlist-tools-benchmark/`

## Summary

- **50 tools cloned** from GitHub
- **7 algorithmic categories** identified
- **Top 20 selected** for paper benchmark (by relevance + stars)
- WordlistXPL-Forge included as 21st entry for comparison

## Algorithmic Categories

| ID | Category | Description | Tools |
|----|----------|-------------|-------|
| C1 | **Profile/Target-based** | Generates candidates from personal information (names, dates, keywords) | cupp, bopscrk, BEWGor, elpscrk, longtongue, psudohash, CrackSmith, Mikara, PassPro, pwg, passpwn, ComPP |
| C2 | **Combinatoric/Exhaustive** | Enumerates all permutations of charset/length/mask | crunch, maskprocessor, TTPassGen, cracken |
| C3 | **Rule/Mangling** | Applies transformation rules to base words | hashcat, john, RSMangler, mentalist, hashcat-utils, cook, wister, pipal |
| C4 | **Probabilistic/Statistical** | Uses Markov chains, PCFG, or other statistical models | OMEN, pcfg_cracker, Cpcfg, OMEN-reborn |
| C5 | **Neural/Deep Learning** | GAN or LLM-based password generation | PassGAN, PassGPT |
| C6 | **Scraping/Extraction** | Builds wordlists from web content, lyrics, or OSINT | CeWL, lyricpass, WordHound, username-anarchy, wlkit |
| C7 | **Hybrid Cognitive** | Multi-layer pipeline with cognitive bias modeling | CogPIE (within WordlistXPL-Forge) |

## Complete Inventory (sorted by stars)

| # | Tool | Stars | Language | Category | Algorithm Core | GitHub |
|---|------|-------|----------|----------|----------------|--------|
| 1 | hashcat | 27,036 | C | C3 | GPU-accelerated rule engine (mask, combinator, hybrid, PRINCE, brute-force) | hashcat/hashcat |
| 2 | john | 13,806 | C | C3 | Rules-based mangling, incremental mode, wordlist mode | openwall/john |
| 3 | Probable-Wordlists | 9,376 | Wordlists | -- | Pre-sorted frequency-ranked lists from breach analysis | berzerk0/Probable-Wordlists |
| 4 | cupp | 6,597 | Python | C1 | Profile concatenation + case/leet/number mutations | Mebus/cupp |
| 5 | pydictor | 3,655 | Python | C1+C2 | Social engineering dictionary + combinatoric engine | LandGrey/pydictor |
| 6 | CeWL | 2,863 | Ruby | C6 | Web spider + word frequency extraction | digininja/CeWL |
| 7 | mentalist | 2,041 | Python | C3 | GUI chain of transform nodes (case, append, prepend, leet) | sc0tfree/mentalist |
| 8 | PassGAN | 2,014 | Python | C5 | Wasserstein GAN with gradient penalty on password corpora | brannondorsey/PassGAN |
| 9 | hate_crack | 1,867 | Python | C3+C4 | Automated hashcat methodology (PRINCE + OMEN + PCFG + rules) | trustedsec/hate_crack |
| 10 | hashcat-utils | 1,627 | C | C3 | Combinator, rule generation, expander, splitlen | hashcat/hashcat-utils |
| 11 | psudohash | 1,473 | Python | C1 | Keyword-based pattern imitation (leet, case, padding) | t3l3machus/psudohash |
| 12 | username-anarchy | 1,489 | Ruby | C6 | Name-to-username format enumeration (40+ formats) | urbanadventurer/username-anarchy |
| 13 | xkcdpass | 1,434 | Python | C2 | Random word sampling (Diceware/XKCD method) | redacted/XKCD-password-generator |
| 14 | cook | 1,380 | Go | C3 | Permutation + encoding + extension framework | glitchedgitz/cook |
| 15 | Passhunt | 1,310 | Python | -- | Default credential lookup (not generation) | Viralmaniar/Passhunt |
| 16 | bopscrk | 1,124 | Python | C1 | Profile transforms + combinations + leet + lyrics (lyricpass) | r3nt0n/bopscrk |
| 17 | awesome-password-cracking | 1,122 | Markdown | -- | Curated list (reference, not a tool) | n0kovo/awesome-password-cracking |
| 18 | duplicut | 983 | C | -- | Bloom filter deduplication of massive wordlists | nil0x42/duplicut |
| 19 | elpscrk | 964 | Python | C1 | Permutation + statistics-based profiling (Mr. Robot inspired) | D4Vinci/elpscrk |
| 20 | weakpass | 749 | Python | C2+C3 | Rule generation + wordlist compilation framework | zzzteph/weakpass |
| 21 | pipal | 665 | Ruby | -- | Password analysis/statistics (not generation) | digininja/pipal |
| 22 | kwprocessor | 611 | C | C2 | Keyboard-walk pattern generator (routes + keymaps) | hashcat/kwprocessor |
| 23 | maskprocessor | 515 | C | C2 | Per-position charset word generator (mask-based) | hashcat/maskprocessor |
| 24 | princeprocessor | 502 | C | C2 | PRINCE algorithm (Probability Infinite Chained Elements) | hashcat/princeprocessor |
| 25 | BEWGor | 422 | Python | C1 | Profile-based (CUPP-inspired) with extended biographical data | berzerk0/BEWGor |
| 26 | cracken | 379 | Rust | C2 | Fast mask-based generator + smart list analysis | shmuelamar/cracken |
| 27 | pcfg_cracker | 372 | Python | C4 | Probabilistic Context-Free Grammar with trained terminals | lakiw/pcfg_cracker |
| 28 | OMEN | 335 | C | C4 | Ordered Markov ENumerator (positional n-gram model) | RUB-SysSec/OMEN |
| 29 | clem9669-wordlists | 329 | Wordlists | -- | Curated French/international wordlists | clem9669/wordlists |
| 30 | passphraseme | 271 | Python | C2 | EFF Diceware passphrase generation | micahflee/passphraseme |
| 31 | RSMangler | 240 | Ruby | C3 | Keyword mutation (case, leet, reverse, year, suffix) | digininja/RSMangler |
| 32 | TTPassGen | 169 | Python | C2 | Multi-mode generator (brute, combination, rule) | tp7309/TTPassGen |
| 33 | dcipher | 152 | JavaScript | -- | Hash lookup (not generation) | k4m4/dcipher |
| 34 | wister | 127 | Python | C3 | Word variation craft (case, leet, prefix, suffix) | cycurity/wister |
| 35 | crunch | 120 | C | C2 | Exhaustive charset x length permutation generator | jim3ma/crunch |
| 36 | longtongue | 109 | Go | C1 | Target info to password/passphrase candidates | edoardottt/longtongue |
| 37 | PassGPT | 103 | Python | C5 | GPT-2 fine-tuned on password corpora (guided generation) | javirandor/passgpt |
| 38 | lyricpass | 102 | Python | C6 | Lyrics scraping + passphrase candidate extraction | initstring/lyricpass |
| 39 | ComPP | 64 | Python | C1+C6 | Company password profiling (web scrape + patterns) | sec-it/ComPP |
| 40 | CrackSmith | 10 | JavaScript | C1 | Dictionary + pattern generation (8/12-word passphrases) | hackops-academy/CrackSmith |
| 41 | passpwn | 10 | Python | C1 | Rule-based custom patterns + user-defined rules | NeCr00/passpwn |
| 42 | Cpcfg | 6 | C | C4 | C implementation of PCFG + OMEN Markov integration | Cynosureprime/Cpcfg |
| 43 | pwg | 5 | Python | C1 | Personal profile to password patterns | shrkwv/pwg |
| 44 | OMEN-reborn | 4 | Python | C4 | Modernized OMEN (Python rewrite) | fvsion/OMEN-reborn |
| 45 | wlkit | 3 | Python | C6 | Unified toolkit (crunch + CeWL + CUPP + rules) | kanishk-dadhich/wlkit |
| 46 | Brute-Wordlist | 1 | Python | C2 | Basic permutation-based brute generator | siwam-king1/Brute-Wordlist |
| 47 | Mikara | 1 | Python | C1 | Target information to password list | kod34/Mikara |
| 48 | PassPro | 0 | Python | C1 | Custom wordlist from user-provided info | gandolf0/PassPro |
| 49 | WordHound | 0 | Python | C6 | Targeted wordlists from websites/tweets/PDFs/Reddit | sealight001/wordhound |
| 50 | wordlistgenerator | 0 | Python | C2 | Basic combination-based generation | h4jack/wordlistgenerator |

## Top 20 Selected for Paper (by relevance and impact)

Selection criteria: algorithmic diversity, community adoption (stars), academic citation, and representation of each category.

| # | Tool | Stars | Category | Why Selected |
|---|------|-------|----------|-------------|
| 1 | hashcat (rule engine) | 27,036 | C3 | Industry standard rule-based engine |
| 2 | John the Ripper | 13,806 | C3 | Industry standard mangling rules |
| 3 | cupp | 6,597 | C1 | Most popular profile-based generator |
| 4 | pydictor | 3,655 | C1+C2 | Social engineering + combinatoric hybrid |
| 5 | CeWL | 2,863 | C6 | Standard web scraping generator |
| 6 | mentalist | 2,041 | C3 | GUI rule chain builder |
| 7 | PassGAN | 2,014 | C5 | Reference GAN-based approach |
| 8 | princeprocessor | 502 | C2 | PRINCE algorithm reference |
| 9 | bopscrk | 1,124 | C1 | Profile + lyrics + leet |
| 10 | psudohash | 1,473 | C1 | Pattern imitation from keywords |
| 11 | elpscrk | 964 | C1 | Statistics-based profiling |
| 12 | crunch | 120 | C2 | Classic exhaustive generator |
| 13 | maskprocessor | 515 | C2 | Mask-based per-position charset |
| 14 | OMEN | 335 | C4 | Ordered Markov ENumerator |
| 15 | pcfg_cracker | 372 | C4 | PCFG reference implementation |
| 16 | RSMangler | 240 | C3 | Keyword mutation tool |
| 17 | kwprocessor | 611 | C2 | Keyboard walk generator |
| 18 | PassGPT | 103 | C5 | LLM-based password generation |
| 19 | BEWGor | 422 | C1 | Extended profile-based |
| 20 | **WordlistXPL-Forge** | private | C1-C7 | 109 modules, all 7 categories, includes CogPIE |

## Algorithmic Coverage Matrix

| Category | External Tools | WLF Engines | CogPIE |
|----------|---------------|-------------|--------|
| C1 Profile/Target | cupp, bopscrk, BEWGor, elpscrk, psudohash | cupp_engine, bopscrk_engine, profiler, br_deep_engine | Yes (Layer 1+2) |
| C2 Combinatoric | crunch, maskprocessor, princeprocessor, kwprocessor | charset_gen, prince_engine, combo_engine, kwalk_gen | Partial (Layer 2) |
| C3 Rule/Mangling | hashcat, john, RSMangler, mentalist | rule_engine, rsmangler_engine, leet_permuter, keyword_mutations, affix_engine, mangler | Yes (Layer 3) |
| C4 Probabilistic | OMEN, pcfg_cracker | markov_engine, pcfg_engine, semantic_pcfg, domain_pcfg | Yes (Layer 4) |
| C5 Neural/DL | PassGAN, PassGPT | gan_engine, transformer_engine, neural_engine, vae_engine, diffusion_engine, tcn_engine, masked_lm_engine, nflow_engine | No (design choice) |
| C6 Scraping/OSINT | CeWL, lyricpass, username-anarchy | (via integration) | No |
| C7 Hybrid Cognitive | -- | **CogPIE (5-layer pipeline)** | Yes (unique) |

## Key Metrics

- **Languages:** Python (30), C (10), Ruby (4), Go (2), Rust (1), JavaScript (2), Markdown/Wordlists (4)
- **Active (updated 2025-2026):** 28/50
- **Academic papers cited:** hashcat, john, OMEN, pcfg_cracker, PassGAN, PassGPT, princeprocessor (PRINCE), CogPIE
- **Total GitHub stars (all 50):** ~84,000+
