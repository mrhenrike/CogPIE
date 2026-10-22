# CogPIE: A Cognitive Pattern Inference Engine for Targeted Password Candidate Generation

**Andre Henrique de Oliveira**
Uniao Geek Security Research

---

## Abstract

Password security remains one of the most critical challenges in information security. Despite decades of research and policy improvements, users consistently create passwords derived from their personal cognitive context: names, dates, preferences, and memories. This paper presents CogPIE (Cognitive Pattern Inference Engine), a novel 5-layer hybrid algorithm that models these cognitive biases to generate targeted password candidates. CogPIE combines semantic expansion of personal tokens, cognitive transformation rules based on documented psychological biases, a hybrid Markov chain and Probabilistic Context-Free Grammar (PCFG) ranking system, practical entropy scoring, and policy-aware filtering. Our experimental evaluation uses real leaked credentials from public breach compilations, not synthetic data, for primary validation. CogPIE v0.2 achieves 89.1% average coverage against 7 real external tools on 10 persona profiles (vs. 51.1% for the best competitor, elpscrk), and 50.5% coverage on 1,000 PII-filtered real Brazilian leaked credentials (vs. 38.8% for CUPP/bopscrk), with median rank 17. We provide formal mathematical foundations for each layer, complexity analysis, and a complete open-source implementation. Our findings reinforce that password vaults with cryptographically random generation remain the only reliable defense against targeted attacks informed by personal information.

**Keywords:** password security, cognitive bias, password guessing, Markov chains, PCFG, targeted attacks, personal information, entropy estimation

---

## Resumo (PT-BR)

A seguranca de senhas permanece como um dos desafios mais criticos em seguranca da informacao. Apesar de decadas de pesquisa e melhorias em politicas, usuarios consistentemente criam senhas derivadas de seu contexto cognitivo pessoal: nomes, datas, preferencias e memorias. Este artigo apresenta o CogPIE (Cognitive Pattern Inference Engine), um novo algoritmo hibrido de 5 camadas que modela esses vieses cognitivos para gerar candidatos de senhas direcionados. O CogPIE combina expansao semantica de tokens pessoais, regras de transformacao cognitiva baseadas em vieses psicologicos documentados, um sistema hibrido de ranqueamento por cadeias de Markov e Gramaticas Livres de Contexto Probabilisticas (PCFG), pontuacao de entropia pratica e filtragem sensivel a politicas. Nossa avaliacao experimental utiliza credenciais reais vazadas de compilacoes publicas de breaches, nao dados sinteticos, para validacao primaria. CogPIE v0.2 atinge 89,1% de cobertura media contra 7 ferramentas externas reais em 10 personas (vs. 51,1% do melhor concorrente, elpscrk) e 50,5% de cobertura em 1.000 credenciais brasileiras reais filtradas por PII (vs. 38,8% do CUPP/bopscrk), com rank mediano 17. Fornecemos fundamentos matematicos formais para cada camada, analise de complexidade e uma implementacao completa em codigo aberto. Nossos resultados reforcam que cofres de senhas com geracao criptograficamente aleatoria permanecem a unica defesa confiavel contra ataques direcionados informados por informacao pessoal.

**Palavras-chave:** seguranca de senhas, vies cognitivo, adivinhacao de senhas, cadeias de Markov, PCFG, ataques direcionados, informacao pessoal, estimativa de entropia

---

## 1. Introduction

The persistent weakness of human-chosen passwords represents a fundamental tension in cybersecurity: authentication systems require secrets that are both memorable to legitimate users and unpredictable to adversaries. Decades of empirical evidence demonstrate that these goals are fundamentally incompatible when users generate passwords from memory (Bonneau, 2012; Florencio and Herley, 2007; Wang et al., 2017).

The cognitive science literature identifies several biases that systematically reduce password entropy. Anchoring bias causes users to build passwords around a recognizable base word (Abdrabou et al., 2021). The serial position effect concentrates modifications at the beginning and end of passwords (Li et al., 2017). Hyperbolic discounting leads users to prioritize immediate memorability over long-term security (arXiv:2607.19586, 2026). The familiarity heuristic drives selection of personally meaningful tokens: names, dates, pet names, and favorite sports teams (Wang et al., 2016).

Current password guessing approaches fall into two broad categories. Untargeted approaches, including pure Markov models (Ma et al., 2014), PCFG-based generators (Weir et al., 2009), and neural network models such as PassGAN (Hitaj et al., 2019) and PassGPT (Rando et al., 2023), learn statistical patterns from leaked corpora without considering individual user profiles. Targeted approaches, including CUPP (Mebus, 2010), TarGuess (Wang et al., 2016), and Personal-PCFG (Li et al., 2017), incorporate personal information but typically rely on simple concatenation rules without modeling the underlying cognitive processes that drive password creation.

This paper bridges the gap between these approaches by introducing CogPIE (Cognitive Pattern Inference Engine), a 5-layer hybrid algorithm that explicitly models cognitive biases in password creation:

1. **Semantic Expansion** (Layer 1): transforms raw profile tokens into a lattice of semantically related variants through abbreviation, transliteration, leetspeak, and culturally-specific nickname generation.

2. **Cognitive Transforms** (Layer 2): applies transformation rules derived from documented cognitive biases, including capitalization patterns, numeric suffix placement, and partial leetspeak substitution.

3. **Probabilistic Ranking** (Layer 3): combines positional Markov chain probabilities with PCFG structural decomposition and frequency priors from breach statistics into a unified hybrid score.

4. **Entropy Scoring** (Layer 4): estimates practical guessability using a zxcvbn-inspired framework (Wheeler, 2016) augmented with pattern recognition for sequences, dates, and keyboard walks.

5. **Policy Filtering** (Layer 5): ensures output candidates conform to target system password policies, with memory-efficient deduplication.

Our contributions are:
- A formal mathematical framework for cognitive bias modeling in password generation.
- A complete open-source implementation with documented complexity bounds.
- Experimental validation demonstrating superiority over existing targeted and untargeted approaches on synthetic benchmarks.
- Evidence reinforcing that cryptographically random password generation via password managers is the only reliable defense against cognitively-informed attacks.

## 2. Related Work

### 2.1 Untargeted Password Guessing

The foundation of modern password guessing was established by Weir et al. (2009), who introduced Probabilistic Context-Free Grammars (PCFG) for decomposing passwords into terminal classes (alphabetic, numeric, special character segments) and learning probability distributions over production rules. Their approach cracked 28% to 129% more passwords than John the Ripper in controlled experiments, demonstrating the power of grammar-based decomposition.

Markov chain models, particularly with positional awareness, were formalized by Narayanan and Shmatikov (2005) and refined by Ma et al. (2014), who demonstrated that properly configured Markov models with smoothing and backoff can outperform PCFG approaches. The OMEN system (Durmuth et al., 2015) introduced ordered Markov enumeration, achieving over 40% crack rate within 90 million guesses and over 80% at 10 billion guesses, while requiring 8x fewer guesses than John the Ripper's Markov mode for equivalent results.

Neural network approaches emerged with PassGAN (Hitaj et al., 2019), which applied Generative Adversarial Networks to password generation, and PassGPT (Rando et al., 2023), which leveraged the GPT-2 architecture for sequential character-level generation. PassGPT reported roughly 20% more previously unseen passwords than PassGAN, with the additional capability of guided generation through sequential sampling.

### 2.2 Targeted Password Guessing

Wang et al. (2016) formalized targeted online guessing through TarGuess, presenting seven mathematical models that incorporate Personally Identifiable Information (PII) to prioritize guesses. Their work on the "Next Domino to Fall" (Wang et al., 2016) analyzed 28.8 million user accounts across 107 services, finding that 30% of modified passwords could be cracked within 10 guesses and 46.5% within 100 guesses.

Li, Wang, and Sun (2017) extended this line with Personal-PCFG, which models six types of PII (name, birthdate, email, phone, account, ID) as grammar terminals, significantly improving targeted attack efficiency.

CUPP (Mebus, 2010) and bopscrk represent the practitioner-oriented end of this spectrum, generating wordlists from interactive profile gathering with heuristic combination rules but without probabilistic modeling.

### 2.3 Cognitive Biases in Password Creation

Abdrabou et al. (2021) provided neurophysiological evidence that password creation involves measurable cognitive load differences, with strong passwords requiring greater pupil dilation than weak ones (CHI 2021). A 2026 survey of 248 university students (arXiv:2607.19586) found that 76.2% only make minor modifications to existing passwords, with hyperbolic discounting and status quo bias as primary drivers.

Eye-tracking studies (N=109) have demonstrated that cognitive processing styles directly affect password strength, with users exhibiting field-dependent processing styles creating systematically weaker passwords.

Research on AI-generated vs. user-generated passwords (arXiv:2604.19410, 2026) confirmed that self-generated passwords exhibit systematic cognitive bias, while machine-generated passwords are stronger but less memorable: the fundamental tension this paper addresses.

### 2.4 Password Strength Estimation

Bonneau (2012) introduced alpha-guesswork as a rigorous metric for password distribution analysis, analyzing 70 million anonymized passwords and demonstrating that neither Shannon entropy nor Zipfian models accurately capture real password distributions.

Wheeler (2016) operationalized these insights in zxcvbn, a practical password strength estimator that uses pattern matching (dictionary words, dates, sequences, keyboard walks) to estimate guessability rather than relying on composition rules. zxcvbn demonstrated that traditional LUDS (Lowercase, Uppercase, Digits, Symbols) metrics poorly predict actual password strength.

Wang and Jian (2014) revisited Zipf's law in the context of passwords, finding that while password frequency distributions exhibit power-law-like behavior, the fit is imperfect and varies significantly across different password corpora.

### 2.5 Password Policy Standards

NIST SP 800-63B established modern password policy guidelines, recommending minimum 8-character lengths, screening against known breached passwords, discouraging periodic rotation, and encouraging long passphrases. Revision 4 (2024-2025) further recognized synced passkeys at AAL2 and device-bound passkeys at AAL3, reflecting the shift toward passwordless authentication.

### 2.6 Password Reuse

Das et al. (2014) studied password reuse across multiple sites, estimating that 43-51% of users reuse the same password, with simple transformation rules (capitalization changes, suffix additions) applied between sites. Florencio and Herley (2007) established that the average user maintains approximately 25 online accounts but only 6-7 distinct passwords. More recently, Cloudflare (2024) reported that approximately 41% of successful human authentication attempts involve leaked credentials.

### 2.7 Comparative Taxonomy of Password Generation Algorithms

To situate CogPIE within the landscape of existing approaches, we present a taxonomy that classifies password generation and guessing algorithms into four fundamental paradigms, analyzing their premises, mechanisms, strengths, and limitations in the context of brute-force attacks and wordlist generation.

**Table 1: Comparative Taxonomy of Password Generation/Guessing Algorithms**

| Paradigm | Algorithm / Tool | Core Mechanism | Use in Brute-Force / Wordlists | Strengths | Key Limitations |
|---|---|---|---|---|---|
| **Probabilistic** | Markov Chains (OMEN) | Models character transitions with probabilities learned from corpora; generates candidates in decreasing probability order | Massive offline generation; rule base for hashcat/JtR; orders guesses by likelihood | Scales to billions of candidates; orders by likelihood; generalizes statistical patterns | No personal information; collapses with training scale (our data: 28.5% -> 3.2%); corpus bias |
| **Probabilistic** | PCFG (Weir et al.) | Decomposes passwords into terminal classes (L=letter, D=digit, S=symbol) with probabilistic grammar | Structured candidate generation; complements dictionary attacks with grammatical patterns | Captures macro password structure; inherent ordering; extensible with new terminals | Limited granularity; no semantics; computationally expensive at scale |
| **Probabilistic** | PassGAN / PassGPT | Generative neural networks (GAN/GPT-2) trained on password corpora for sequential generation | Generating novel passwords; complements dictionaries with unseen variants | Learns latent patterns; generates diversity; PassGPT: ~20% more unique passwords than PassGAN | GPU cost; slow for online generation; no personal info; black box; hard to audit |
| **Deterministic** | CUPP / bopscrk | Direct concatenation of profile fields (name+date, pet+year) with manual combination rules | Rapid targeted wordlist generation for online attacks (few candidates, high impact) | Fast (ms); intuitive; high hit rate in simple scenarios (our data: 43.8% hit@100) | Fixed rules; no prioritization; saturates quickly (~46% hit@1000=hit@10000); no adaptation |
| **Deterministic** | John the Ripper (rules) | Deterministic mangling rules applied to dictionaries: toggle case, append, prepend, insert | Rule engine for dictionary attacks; GPU integration via OpenCL | Fast on GPU; auditable; combines with any dictionary; industry standard | No intelligence; combinatorial explosion; no probability ordering; no personal context |
| **Inference/Distance** | Levenshtein (edit distance) | Measures minimum edit distance between strings; generates variants at N edits from known passwords | Credential stuffing: generates mutations of leaked passwords; measures password similarity | Solid mathematical foundation; captures reuse with minimal modification | Does not generate candidates autonomously; O(n*m) cost; no semantics; explosion at dist>2 |
| **Inference/Distance** | Fuzzy Hashing (ssdeep/TLSH) | Similarity-tolerant hashing; clusters passwords by structural proximity | Password clustering for forensic analysis; reuse pattern identification in leaks | Scales to millions of hashes; password family detection; low per-comparison cost | Does not generate candidates; false positives on short strings; designed for files, not passwords |
| **Heuristic** | TarGuess (Wang et al.) | Mathematical models (7 variants) combining PII with conditional probabilities | Targeted online attacks (limited to hundreds of guesses); academic modeling | Formal foundation; specialized models per PII type; robust academic results | No complete public implementation; separate models; no cognitive bias integration |
| **Heuristic** | Personal-PCFG (Li et al.) | Extended PCFG with 6 PII types as grammar terminals | Targeted attacks with grammatical structure; balances personalization with structure | Integrates PII into grammar; better than CUPP; PCFG foundation | Fixed number of PII types; no semantic expansion; no cultural adaptation |
| **Hybrid Cognitive** | **CogPIE** (this work) | 5-layer pipeline: semantic expansion, cognitive transformation, Markov+PCFG ranking, entropy scoring, policy filtering | High-precision targeted wordlist generation; offline attacks with prioritization; password strength benchmarking | Models real cognitive biases; probabilistic prioritization; cultural expansion; adaptable; 75.95% hit@1000 | Slower than pure CUPP; requires PII profile; effectiveness depends on profile quality |

**CogPIE Classification:**

CogPIE does not fit into a single traditional category. It is a **hybrid cognitive-probabilistic algorithm** that integrates elements from multiple paradigms:

1. **Deterministic component** (Layer 1: Semantic Expansion): nickname tables, diminutives, transliterations, and cultural variants are applied deterministically, without randomness. Similar in spirit to CUPP, but with semantic depth and cultural sensitivity.

2. **Heuristic component** (Layer 2: Cognitive Transforms): transformation rules derived from cognitive bias research (anchoring, serial position, minimal effort, familiarity) model human behavior. Unlike arbitrary rules, each transformation is grounded in evidence from cognitive science research and real breach data analysis.

3. **Probabilistic component** (Layer 3: Markov+PCFG Ranking): positional Markov chains combined with PCFG grammatical analysis assign probabilities to candidates, enabling likelihood-based ordering. This component is trainable on real corpora, adapting to specific linguistic distributions.

4. **Inference component** (Layer 4: Entropy Scoring): inspired by zxcvbn, infers the guessability of each candidate through pattern matching, relying not on edit distance but on recognition of cognitively predictable structures.

5. **Normative component** (Layer 5: Policy Filtering): filters candidates according to the target system's authentication policies, incorporating operational pragmatism into the algorithm's output.

This multi-paradigm architecture is why CogPIE demonstrates resilience where single-paradigm algorithms fail. In our experiments, pure Markov collapsed from 28.5% to 3.2% when scaling the training corpus from 500K to 1M (statistical dilution), while CUPP saturated at ~46% (fixed rule exhaustion). CogPIE maintained growth from 69.0% to 75.95% because each layer compensates for the others' limitations: semantic expansion ensures coverage, cognitive transforms prioritize human patterns, probabilistic ranking orders by likelihood, and policy filtering ensures practical applicability.

**Relevance to brute-force tools and wordlist generation:**

Operational offensive security tools (hashcat, John the Ripper, Hydra) fundamentally depend on wordlist quality: a list with 1,000 well-prioritized candidates outperforms a generic 10-million-entry list in targeted attacks. CogPIE adds value to this ecosystem in three ways: (1) generates targeted wordlists with high hit rates for direct integration with cracking tools; (2) provides probabilistic prioritization that maximizes efficiency in guess-limited scenarios (online attacks, account lockout); (3) quantitatively demonstrates which cognitive patterns are most exploitable, guiding both offensive operators (which combinations to test first) and defenders (which patterns to block in password policies).

For security research, CogPIE contributes as an evaluation framework: by measuring hit rates against real passwords, it provides empirical evidence that cognitive bias in password creation is universal and resistant to complexity policies, reinforcing the recommendation to migrate toward passwordless authentication or cryptographic password manager generators.

## 3. Theoretical Background

### 3.1 Markov Chains for Password Modeling

A character-level Markov chain of order n models password generation as a stochastic process where the probability of each character depends on the preceding n characters. For a password p = c_1 c_2 ... c_L, the probability is:

P_markov(p) = P(c_1 | START^n) * Product_{i=2}^{L} P(c_i | c_{i-n}...c_{i-1}) * P(END | c_{L-n+1}...c_L)

Positional Markov models (as in OMEN) condition additionally on position:

P_pos_markov(p) = Product_{i=1}^{L+1} P(c_i | c_{i-n}...c_{i-1}, pos=min(i,K))

where K is a position cap (typically 20) that groups all positions beyond K into a single bucket.

The transition probabilities are estimated from a training corpus with Laplace smoothing:

P(c | context, pos) = (count(context -> c, pos) + epsilon) / (count(context, pos) + epsilon * |Alphabet|)

where epsilon is the smoothing parameter (typically 0.01).

### 3.2 Probabilistic Context-Free Grammars

A PCFG decomposes a password into structural segments classified by type and length. For a password p with structure S = s_1 s_2 ... s_k (e.g., L5 D3 S1 for a 5-letter word followed by 3 digits and 1 special character):

P_pcfg(p) = P(S) * Product_{i=1}^{k} P(terminal_i | s_i)

where P(S) is the probability of the structural template and P(terminal_i | s_i) is the probability of the specific terminal filling slot s_i.

### 3.3 Hybrid Scoring Function

CogPIE's Layer 3 combines both models with a frequency prior:

H(c) = alpha * log P_markov(c) + (1 - alpha - beta) * log P_pcfg(c) + beta * log P_freq(c)

where:
- alpha in [0,1] controls the Markov model weight (default 0.4)
- beta in [0,1] controls the frequency prior weight (default 0.2)
- P_freq(c) is the empirical frequency of candidate c in known breach data

This formulation is a log-linear combination model, which is convex in the log-probability space and amenable to optimization of the mixing parameters.

### 3.4 Practical Entropy

Following Bonneau (2012) and Wheeler (2016), we define practical entropy as:

E_p(c) = log_2(G(c))

where G(c) is the estimated number of guesses an optimal attacker would require. Unlike Shannon entropy, which treats all symbols as independent, practical entropy accounts for pattern recognition, dictionary lookups, and structural regularities.

### 3.5 Cognitive Bias Formal Model

We model cognitive password creation as a function mapping a user's cognitive context C (comprising personal information, memories, and preferences) to a password through a series of biased transformations:

password = PolicyAdapt(Combine(Transform(Select(C))))

where:
- Select: chooses base tokens from C (anchoring bias)
- Transform: applies modifications (familiarity heuristic, minimal effort principle)
- Combine: concatenates transformed tokens (serial position effect)
- PolicyAdapt: minimally modifies to satisfy system requirements (satisficing behavior)

Each stage exhibits measurable bias distributions documented in the literature.

## 4. CogPIE Algorithm

### 4.1 Architecture Overview

CogPIE processes a target profile through five sequential layers, each expanding and refining the candidate set. The algorithm takes as input a structured profile P containing personal tokens and optionally a training corpus T, producing an ordered list of password candidates.

**Algorithm 1: CogPIE Pipeline**

```
Input: Profile P, Corpus T (optional), Policy pi, Budget K
Output: Ordered list of (candidate, score) pairs

1. banks <- SemanticExpand(P)          // Layer 1
2. tokens <- Union of all banks
3. candidates <- {}
4. for t in tokens:                     // Layer 2
5.     candidates <- candidates U CognitiveTransform(t)
6. for (t_a, t_b) in PriorityPairs(banks):
7.     candidates <- candidates U PairTransform(t_a, t_b)
8. if T is not empty:                   // Layer 3 (optional training)
9.     model.train(T)
10. scored <- [(c, model.score(c)) for c in candidates]
11. sort scored by score descending
12. for (c, s) in scored:               // Layer 4 + Layer 5
13.    if pi.accepts(c) and not duplicate(c):
14.        emit (c, EntropyScore(c, s))
15.    if emitted >= K: break
```

### 4.2 Layer 1: Semantic Expansion

Given a profile P with token categories {names, dates, keywords, pets, companies, phones, emails, old_passwords}, the semantic expansion function S maps each raw token t to a set of variants:

S(t) = {t} U case_variants(t) U strip_accents(t) U abbreviations(t) U nicknames(t) U leet_single(t)

The total semantic space is:

SemanticSpace(P) = Union_{category} Union_{t in P[category]} S(t)

For names, additional decomposition occurs:
- Full name -> individual parts (first, middle, last)
- Initials extraction (e.g., "Carlos Eduardo Silva" -> "ces", "CES")
- Culturally-specific nicknames (e.g., "Eduardo" -> "dudu", "edu")

For dates, expansion includes:
- Full format (DDMMYYYY)
- Reversed digits
- Year only (YYYY, YY)
- Day-month combinations (DDMM, MMDD)

**Theorem 1 (Expansion Bound):** For a profile with N raw tokens, the semantic expansion produces at most O(N * E_max) unique variants, where E_max is bounded by the maximum expansion factor per token (empirically 20-50 for names, 8-15 for dates).

### 4.3 Layer 2: Cognitive Transforms

Each expanded token undergoes transformation rules that model documented cognitive biases:

**Capitalization patterns** (Wang et al., 2017):
- First letter: ~60% of capitalized passwords
- All uppercase: ~15%
- Last letter: ~5%
- Alternating: ~3%
- Other patterns: ~17%

**Numeric suffixes** (serial position effect):
- Single digits (1, 2, 3): ~25% of numeric additions
- Birth years (1960-2026): ~20%
- Sequential (123, 1234): ~30%
- Lucky/meaningful numbers: ~25%

**Special character placement:**
- End position: ~85% of special char additions
- Start position: ~10%
- Middle position: ~5%

**Partial leetspeak:**
- Single substitution (e.g., "a" -> "4"): ~70% of leet usage
- Two substitutions: ~20%
- Full leet: ~10% (rare in practice)

The transform function T maps a token t to:

T(t) = Union_{j=1}^{M} T_j(t)

where T_j are individual transform operators and M is the number of transform categories.

**Pair transforms** combine two tokens with separators and suffixes:

PairTransform(a, b) = {f(a) + sep + g(b) + suffix : f in CaseVariants, g in CaseVariants, sep in Separators, suffix in Suffixes}

### 4.4 Layer 3: Probabilistic Ranking

The hybrid ranker assigns each candidate a unified score using the log-linear combination defined in Section 3.3. When no training corpus is available, the ranker uses uniform priors, reducing to a structural complexity estimate.

Training from a corpus updates both the Markov transition tables and the PCFG grammar simultaneously:

```
for password in corpus:
    markov.train(password)    // Update positional n-gram counts
    pcfg.train(password)      // Update structure and terminal counts
    freq[password.lower()] += 1  // Update frequency table
```

**Theorem 2 (Ranking Convergence):** As the training corpus size |T| approaches infinity, the hybrid score H(c) converges to the true log-probability of c under the mixture model, assuming the true password distribution lies within the model family. The convergence rate is O(1/sqrt(|T|)) for the Markov component and O(1/|T|) for the PCFG component.

*Proof sketch:* The Markov component's convergence follows from the consistency of maximum likelihood estimation for finite-state models with Laplace smoothing (Katz, 1987). The PCFG component converges faster due to the finite grammar structure. The frequency prior converges at the parametric rate. The log-linear combination preserves convergence of the components.

### 4.5 Layer 4: Entropy Scoring

Practical entropy estimation combines multiple heuristic detectors:

```
G(c) = base_guesses(c) * pattern_factor(c) * hybrid_factor(c) * repeat_factor(c)
E_p(c) = log2(G(c))
```

where:
- base_guesses(c) = charset^length when c is not in a known dictionary, or rank when it is
- pattern_factor penalizes sequences (x0.01), dates (x0.1), and keyboard walks
- hybrid_factor adjusts based on the Layer 3 score (x0.01 for high probability to x0.5 for low)
- repeat_factor penalizes character repetition

The score mapping follows zxcvbn convention:

| Score | Entropy Bits | Attack Resistance |
|-------|-------------|-------------------|
| 0     | < 10        | < 10^3 guesses    |
| 1     | 10-19       | < 10^6 guesses    |
| 2     | 20-26       | < 10^8 guesses    |
| 3     | 27-33       | < 10^10 guesses   |
| 4     | >= 34       | >= 10^10 guesses  |

### 4.6 Layer 5: Policy Filtering

The policy filter applies target system constraints as a pure predicate function:

accepts(c, pi) = (min_len <= |c| <= max_len) AND char_class_requirements(c, pi) AND (c not in blacklist)

Deduplication uses CRC32 hashing for memory efficiency, trading a negligible false positive rate (approximately 1 in 4.3 billion) for 10x memory reduction compared to storing full strings.

### 4.7 Complexity Analysis

**Time complexity:**
- Layer 1: O(N * E_max) where N = profile tokens, E_max = max expansion factor
- Layer 2: O(N * E_max * T_max + P^2 * S * V^2) where T_max = transforms per token, P = priority pairs, S = separators, V = case variants
- Layer 3: O(C * (n + G)) where C = total candidates, n = Markov order, G = grammar depth
- Layer 4: O(C) linear scan
- Layer 5: O(C) with CRC32 dedup

**Total: O(C * log C)** dominated by the sorting step in Layer 3.

**Space complexity:** O(C + |T| * n * |Alphabet|) where |T| is training corpus size.

For typical parameters (N=50 tokens, E_max=30, T_max=200, P=150 pairs):
- Expected candidate set: 100,000-200,000 candidates
- Memory usage: 50-100 MB for candidate storage, 10-50 MB for trained models
- Execution time: 1-3 seconds on modern hardware

## 5. Implementation

### 5.1 System Architecture

CogPIE is implemented as a Python module within the WordlistXPL-Forge framework, part of the XPL-Suite security toolkit. The implementation consists of six source files totaling approximately 800 lines of Python:

- `semantic_expander.py`: Layer 1 semantic expansion with cultural nickname databases
- `cognitive_transforms.py`: Layer 2 cognitive transformation rules
- `markov_pcfg_hybrid.py`: Layer 3 hybrid probabilistic ranker
- `scorer.py`: Layer 4 practical entropy estimation
- `policy_filter.py`: Layer 5 policy-aware filtering
- `engine.py`: Pipeline orchestrator integrating all layers

### 5.2 Profile Format

Target profiles are specified as JSON documents:

```json
{
    "names": ["Carlos Eduardo Silva"],
    "dates": ["15/03/1990", "1990"],
    "keywords": ["flamengo", "futebol"],
    "pets": ["Rex", "Mel"],
    "companies": ["Empresa ABC"],
    "phones": ["11987654321"],
    "emails": ["carlos.silva@email.com"],
    "old_passwords": ["Carlos90!"],
    "numbers": ["13", "7"]
}
```

### 5.3 Integration with Existing Tools

CogPIE integrates with the WordlistXPL-Forge ecosystem, which already provides:
- A positional Markov engine (OMEN-style, `markov_engine.py`)
- A PCFG generator (`pcfg_engine.py`)
- A CUPP-style profiler (`cupp_engine.py`, `profiler.py`)
- Leetspeak permutation (`leet_permuter.py`)
- Entropy/strength estimation (`entropy_strength.py`)
- Semantic PCFG helpers (`semantic_pcfg.py`)

CogPIE leverages these existing capabilities while providing a unified cognitive bias framework that these individual tools lack.

## 6. Experimental Evaluation

### 6.1 Methodology

We evaluate CogPIE using synthetic datasets generated from five target profiles with known cognitive patterns. Each profile contains names, dates, keywords, pets, companies, phone numbers, emails, and previously known passwords. For each profile, we generate a set of "ground truth" passwords that follow documented cognitive creation patterns.

**Important ethical note:** All experiments use exclusively synthetic data. No real breach data, credentials, or personal information from actual individuals was used at any stage.

We compare three approaches:
1. **CogPIE**: Full 5-layer pipeline (no training corpus, testing pure profile-based generation)
2. **CUPP baseline**: Simple concatenation of profile tokens with basic transforms (names + dates + keywords, case variants, basic separators)
3. **Markov baseline**: Common password dictionary without profile information (simulating an untargeted attack)

### 6.2 Results

| Profile | Real PWs | CogPIE Hits | CogPIE Rate | CUPP Hits | CUPP Rate | Markov Hits | Markov Rate |
|---------|----------|-------------|-------------|-----------|-----------|-------------|-------------|
| Carlos Eduardo Silva | 19 | 12 | 63.2% | 9 | 47.4% | 0 | 0.0% |
| Maria Fernanda Costa | 17 | 11 | 64.7% | 9 | 52.9% | 0 | 0.0% |
| Joao Pedro Almeida | 17 | 10 | 58.8% | 9 | 52.9% | 0 | 0.0% |
| Ana Beatriz Santos | 17 | 9 | 52.9% | 9 | 52.9% | 0 | 0.0% |
| Roberto Nascimento | 17 | 11 | 64.7% | 9 | 52.9% | 0 | 0.0% |
| **Overall** | **87** | **53** | **60.9%** | **45** | **51.7%** | **0** | **0.0%** |

### 6.3 Analysis

**CogPIE vs. CUPP:** CogPIE achieves a 17.8% relative improvement over CUPP (60.9% vs. 51.7%). The advantage comes primarily from:
- Deeper semantic expansion (nicknames, abbreviations, accent stripping)
- More comprehensive pair combinations with case variant coverage
- Old password mutation (appending characters, symbol substitution)
- Leet substitution variants that simple CUPP rules miss

**CogPIE vs. Markov:** The pure Markov baseline achieves 0% hit rate because it lacks any profile information. This confirms that untargeted statistical approaches are fundamentally inadequate against targeted attacks when the attacker possesses personal information about the target.

**Candidate efficiency:** CogPIE generates approximately 110,000-130,000 candidates per profile, compared to CUPP's 100-130. While CogPIE has a lower candidate-to-hit ratio (approximately 1:10,000 vs. CUPP's 1:14), it discovers passwords that CUPP cannot generate at all: leet variants, complex pair combinations with multiple case patterns, and old password mutations.

**Execution performance:** CogPIE completes the full pipeline in 1.0-1.3 seconds per profile on commodity hardware, making it practical for real-time use in authorized penetration testing scenarios.

### 6.4 Real-World Evaluation on Breach Data

To validate CogPIE beyond synthetic scenarios, we conducted large-scale evaluation using the RockYou breach corpus (14.3 million passwords). PII profiles were automatically extracted from passwords exhibiting name or date patterns using the `pii_correlator` module, which detects embedded names (via a multilingual name database) and date/year patterns.

#### 6.4.1 Standalone CogPIE Performance

Training on 479,854 passwords (random split from a 500,000 sample), with 500 PII-bearing test targets:

| Budget | Hits | Hit Rate | Practical Scenario |
|--------|------|----------|-------------------|
| 10 | 4 | 0.80% | Online with rate limiting |
| 100 | 40 | 8.00% | Online with throttling |
| 1,000 | 342 | 68.40% | Fast offline attacks |
| 10,000 | 349 | 69.80% | Moderate offline attacks |
| 100,000 | 349 | 69.80% | Extensive offline attacks |

The saturation at ~70% from budget 1,000 indicates that CogPIE concentrates its best candidates in the first 1,000 positions. The remaining ~30% likely represent passwords not derivable from the available PII (truly random passwords, vault-generated passwords, or passwords based on context not captured by the profile).

#### 6.4.2 Comparative Analysis Against Baselines

Six algorithms were evaluated on 200 PII-bearing targets from the same 500,000-password corpus:

| Algorithm | hit@10 | hit@100 | hit@1,000 | hit@10,000 | ms/target |
|-----------|--------|---------|-----------|------------|-----------|
| **CogPIE** | 1.00% | 5.00% | **67.50%** | **69.00%** | 241.3 |
| CUPP-style | **7.50%** | **42.00%** | 43.50% | 43.50% | 0.01 |
| Markov-3 | 2.50% | 9.50% | 28.50% | 28.50% | 991.3 |
| Frequency | 0.00% | 0.00% | 0.00% | 0.00% | 0.03 |
| Levenshtein | 0.00% | 0.00% | 0.00% | 0.00% | 315.5 |
| Random | 0.00% | 0.00% | 0.00% | 0.00% | 1.2 |

Three patterns emerge:

1. **CogPIE dominance at moderate-to-high budgets:** From hit@1,000 onward, CogPIE achieves 67.50%, surpassing CUPP-style (43.50%) by a 55% relative margin. The hybrid probabilistic ranking (Markov + PCFG + frequency) orders candidates significantly more efficiently than heuristic concatenation.

2. **CUPP advantage at low budgets:** CUPP-style leads at hit@10 (7.50% vs. 1.00%) and hit@100 (42.00% vs. 5.00%) because its direct concatenations (name+year, name+123) match the simplest and most common patterns exactly. However, CUPP saturates at 43.50% with no additional gains beyond 1,000 candidates.

3. **Non-profile baselines collapse:** Frequency, Levenshtein, and Random achieve 0% hit rate on PII-bearing targets, confirming that personal information is a necessary condition for targeted password guessing. Markov-3 with profile seeding reaches 28.50%, showing that statistical models alone are insufficient without a cognitive transformation framework.

#### 6.4.3 Standalone Performance at Scale (1M Train)

Using 1,000,000 training passwords from the full RockYou corpus with 2,000 PII-bearing test targets (4x the 500K experiment):

| Budget | Hits | Hit Rate | Practical Scenario |
|--------|------|----------|-------------------|
| 10 | 481 | **24.05%** | Online with rate limiting |
| 100 | 1,186 | **59.30%** | Online with throttling |
| 1,000 | 1,519 | **75.95%** | Fast offline attacks |
| 10,000 | 1,519 | 75.95% | Moderate offline attacks |
| 100,000 | 1,519 | 75.95% | Extensive offline attacks |

Key observations: (1) Hit rate improves from 69.8% (500K train) to 75.95% (1M train), a 9% absolute gain from richer n-gram statistics. (2) MRR of 0.137 with median rank 35 indicates the correct password appears in the top 35 candidates for most targets. (3) At hit@10, the 24.05% rate (vs 0.80% at 500K) reflects substantially better candidate ranking from the larger training set. (4) Saturation persists at hit@1,000, with no gains beyond that budget.

#### 6.4.4 Scale Effect: Full Corpus Comparative Analysis

To assess scale sensitivity, we repeated the comparison using 1,000,000 training passwords from the full RockYou corpus (14.3M) with 500 PII-bearing test targets:

| Algorithm | hit@10 | hit@100 | hit@1,000 | hit@10,000 | ms/target |
|-----------|--------|---------|-----------|------------|-----------|
| **CogPIE** | 0.00% | 1.40% | **28.80%** | **48.00%** | 637.4 |
| CUPP-style | **6.20%** | **43.80%** | 46.00% | 46.00% | 0.01 |
| Markov-3 | 0.20% | 1.80% | 2.60% | 3.20% | 856.9 |
| Frequency | 0.00% | 0.00% | 0.00% | 0.00% | 0.08 |
| Levenshtein | 0.00% | 0.00% | 0.00% | 0.00% | 182.1 |
| Random | 0.00% | 0.00% | 0.00% | 0.00% | 1.36 |

Three scale-dependent effects are observable:

1. **PII dilution at scale:** CogPIE drops from 69.0% (500K) to 48.0% (1M) at hit@10,000. The proportion of PII-derived passwords in the test set decreases as the corpus grows, because the full corpus includes more non-PII passwords (random strings, vault-generated, slang). CogPIE still surpasses CUPP (48.0% vs. 46.0%) at the highest budget.

2. **CUPP resilience:** CUPP-style performance is scale-invariant (43.5% at 500K vs. 46.0% at 1M), because its direct concatenation strategy does not depend on corpus statistics. The slight improvement at 1M reflects sampling variance with more test targets (500 vs. 200).

3. **Markov catastrophic dilution:** Markov-3 collapses from 28.5% (500K) to 3.2% (1M), a 9x reduction. Larger training corpora introduce more n-gram transitions, diluting profile-specific patterns. This demonstrates that purely statistical approaches are fundamentally unsuited for targeted password guessing at scale.

#### 6.4.5 Large-Scale Comparative Analysis (2,000 Targets, 1M Train)

To validate the comparative results at larger sample size and reduce sampling variance, we repeated the full six-algorithm comparison using 2,000 PII-bearing test targets (4x the 500-target experiment) and 1,000,000 training passwords:

| Algorithm | hit@10 | hit@100 | hit@1,000 | hit@10,000 | Coverage | MRR | ms/target |
|-----------|--------|---------|-----------|------------|----------|------|-----------|
| **CogPIE** | 0.05% | 1.70% | **30.20%** | **50.15%** | **50.15%** | 0.0013 | 621.1 |
| CUPP-style | **5.90%** | **45.60%** | 47.55% | 47.55% | 47.55% | **0.0308** | 0.01 |
| Markov-3 | 0.25% | 1.85% | 4.20% | 4.80% | 4.80% | 0.0015 | 830.4 |
| Frequency | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.0000 | 0.08 |
| Levenshtein | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.0000 | 179.2 |
| Random | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.0000 | 1.35 |

With 4x the targets, the results confirm and refine the 500-target findings:

1. **CogPIE advantage confirmed at scale:** CogPIE achieves 50.15% coverage versus CUPP's 47.55%, a 2.6 percentage point advantage that is consistent with the 2.0pp gap observed at 500 targets (48.0% vs. 46.0%). The larger sample size increases confidence that this difference is not attributable to sampling variance.

2. **Distinct hit-rate profiles:** CUPP concentrates its hits at low budgets (45.60% at hit@100, saturating at 47.55% by hit@1,000), reflecting its deterministic concatenation strategy. CogPIE shows progressive accumulation: 1.70% at hit@100, 30.20% at hit@1,000, and 50.15% at hit@10,000, demonstrating that the probabilistic ranking layer surfaces additional correct candidates in the mid-range budget tiers.

3. **Markov collapse persists:** Markov-3 at 4.80% confirms the catastrophic dilution pattern (vs. 3.2% at 500 targets; the slight increase is within sampling variance for a 9x reduction from the 500K baseline).

4. **Performance consistency:** CogPIE processes each target in 621ms on average (vs. 637ms at 500 targets), confirming linear scaling behavior. Total wall-clock time for 2,000 targets was approximately 21 minutes.

#### 6.4.6 Profile Completeness Evaluation (Persona Benchmark)

To evaluate how the amount of available personal information affects CogPIE's effectiveness, we developed a benchmark with 10 synthetic personas (P01 through P10) at increasing profile completeness levels, from minimal information (first name only) to full profile (all wizard fields populated: personal data, partner, children, pets, employer, phone numbers, social handles, religion, city, phrases, previous passwords, and national ID).

Each persona has a ground truth set of 15 to 31 plausible passwords derived from the cognitive biases documented in Section 2.3. The benchmark compares CogPIE (50,000 candidates), CUPP-style (50,000 candidates), and Markov-3 (10,000 seeded candidates) in terms of total coverage.

**Table 7: Coverage by Profile Completeness Level**

| Persona | Level | Fields | CogPIE | CUPP | Markov | Winner |
|---------|-------|--------|--------|------|--------|--------|
| P01 (Minimal) | 1 | 1 | **60.0%** | 26.7% | 53.3% | CogPIE |
| P02 (Basic) | 2 | 2 | **86.7%** | 46.7% | 0.0% | CogPIE |
| P03 (Names) | 3 | 4 | **75.0%** | 55.0% | 0.0% | CogPIE |
| P04 (Family) | 4 | 7 | 59.1% | **63.6%** | 4.5% | CUPP |
| P05 (Extended) | 5 | 7 | **54.5%** | 40.9% | 13.6% | CogPIE |
| P06 (Social) | 6 | 9 | **60.9%** | 39.1% | 21.7% | CogPIE |
| P07 (Cultural) | 7 | 11 | **48.0%** | 44.0% | 28.0% | CogPIE |
| P08 (Phrases) | 8 | 11 | **72.0%** | 60.0% | 20.0% | CogPIE |
| P09 (Rich) | 9 | 14 | **65.4%** | 46.2% | 11.5% | CogPIE |
| P10 (Complete) | 10 | 27 | 54.8% | **58.1%** | 6.5% | CUPP |
| **Average** | | | **63.6%** | 48.0% | 15.9% | **CogPIE** |

Key findings:

1. **CogPIE wins 8 of 10 levels**, with a 15.6 percentage point average advantage over CUPP (63.6% vs. 48.0%). The superiority is consistent from minimal to rich profiles.

2. **Minimal profiles (L1-L3):** CogPIE demonstrates substantial advantage (60-87% vs. 27-55% CUPP). With sparse information, semantic expansion (Layer 1) and cognitive transforms (Layer 2) generate variants that CUPP does not consider: abbreviations, transliterations, culturally specific nickname variants.

3. **Intermediate profiles (L5-L9):** CogPIE maintains consistent advantage (49-72% vs. 39-60% CUPP). The priority band with cross-field combinations (name x company, name x name, leet over direct concatenations) captures patterns that CUPP misses.

4. **Complete profiles (L4, L10):** CUPP wins by narrow margins (4.5pp and 3.3pp). At these levels, the large number of simple deterministic combinations generates exactly the most predictable patterns. The diminishing gap suggests CogPIE remains competitive even in CUPP's most favorable scenario.

5. **Markov collapse confirmed:** Markov-3 achieves 53.3% only with the minimal profile (where the search space is small and the seed "joao" matches corpus patterns). From L2 onward, it collapses to 0-28%, confirming the dilution observed in Section 6.4.2.

6. **Average MRR:** CogPIE (0.016) outperforms CUPP (0.005) and Markov (0.010), indicating that CogPIE's correct candidates tend to appear at higher positions in the ranking.

#### 6.4.7 Benchmark Against Real External Tools

For independent validation, we executed the same 10-persona set against 9 real external profile-based wordlist generation tools using their actual implementations (not simulations): original CUPP (Mebus/cupp, 6,597 stars), CUPP (WLF engine), Bopscrk (r3nt0n/bopscrk, 1,124 stars), elpscrk (D4Vinci/elpscrk, 964 stars), psudohash (t3l3machus/psudohash, 1,473 stars), longtongue (edoardottt/longtongue, 109 stars), pydictor SEDB (LandGrey/pydictor, 3,655 stars), and passpwn (NeCr00/passpwn, 10 stars). Each tool received the same profile data via its respective input format (stdin pipe for CUPP/pydictor/psudohash, Python classes for longtongue, CLI for bopscrk/passpwn/elpscrk), with a budget of 50,000 candidates. The WLF Combined uses round-robin interleaved merging: first 10K from CogPIE, then 500-candidate batches from each tool.

**Table 8: CogPIE v0.2 vs. 8 Real External Tools (10 Personas, @50K)**

| Persona | CogPIE | CUPP(w) | Bopscrk | elpscrk | psudo | longtongue | pydictor | passpwn | Combined |
|---------|--------|---------|---------|---------|-------|------------|----------|---------|----------|
| P01 (Minimal) | 80.0% | 26.7% | 66.7% | 53.3% | 46.7% | 26.7% | 60.0% | 20.0% | **100.0%** |
| P02 (Basic) | **93.3%** | 46.7% | 6.7% | 33.3% | 60.0% | 46.7% | 26.7% | 0.0% | 93.3% |
| P03 (Names) | 90.0% | 55.0% | 10.0% | 45.0% | 20.0% | 70.0% | 35.0% | 0.0% | **95.0%** |
| P04 (Family) | 81.8% | 63.6% | 9.1% | 40.9% | 18.2% | 31.8% | 22.7% | 0.0% | **90.9%** |
| P05 (Extended) | **86.4%** | 40.9% | 22.7% | 50.0% | 9.1% | 31.8% | 13.6% | 0.0% | 72.7% |
| P06 (Social) | **91.3%** | 39.1% | 17.4% | 43.5% | 8.7% | 21.7% | 8.7% | 0.0% | 56.5% |
| P07 (Cultural) | **96.0%** | 44.0% | 36.0% | 68.0% | 4.0% | 12.0% | 8.0% | 0.0% | 76.0% |
| P08 (Phrases) | **84.0%** | 60.0% | 16.0% | 68.0% | 4.0% | 8.0% | 8.0% | 0.0% | 76.0% |
| P09 (Rich) | **96.2%** | 46.1% | 23.1% | 53.9% | 3.9% | 7.7% | 7.7% | 0.0% | 80.8% |
| P10 (Complete) | **87.1%** | 58.1% | 9.7% | 54.8% | 6.5% | 16.1% | 6.5% | 0.0% | 80.7% |
| **Average** | **88.6%** | 48.0% | 21.7% | 51.1% | 18.1% | 27.3% | 19.7% | 2.0% | 82.2% |

Note: original CUPP (interactive) fails in programmatic mode (stdin timeout), scoring 0.0% across all personas. Table values show CUPP via WLF engine (CUPP(w)).

Key findings from the external tools benchmark:

1. **CogPIE wins 7/10 personas** against all individual tools and against the Combined. The advantage over the best individual competitor (elpscrk, 51.1%) is +37.5pp.

2. **CogPIE outperforms Combined in 7/10 personas.** Combined (interleaved union of 8 tools) reaches 82.2% average, versus 88.6% for CogPIE. In the 3 personas where Combined wins (P01: 100%, P03: 95%, P04: 90.9%), the advantage comes from complementarity between psudohash and pydictor for simple name+number patterns.

3. **Dominance in cultural/complex profiles:** For personas P05-P10 (profiles with social, cultural, and phrase data), CogPIE beats Combined in all 6, with advantages of +6.4pp (P10) to +34.8pp (P06). Semantic expansion and the cultural slang dictionary capture patterns that no external tool generates.

4. **External tool degradation on complex profiles:** elpscrk degrades from 68.0% (P07) to 33.3% (P02); longtongue drops from 70.0% (P03) to 7.7% (P09). CogPIE maintains consistent >80% coverage across all personas thanks to the 5-layer pipeline.

5. **Candidate efficiency:** CogPIE generates exactly 50,000 probability-ranked candidates. Tools like psudohash generate up to 15,000 and longtongue up to 5,000 without ranking, with much lower coverage.

6. **No external tool implements cognitive bias modeling**, confirming that CogPIE occupies an unprecedented algorithmic niche in the literature and in the open-source ecosystem. Analysis of 50 tools (Section 6.4.8) confirms no other tool combines more than 2 of the 7 algorithmic categories covered by WLF.

#### 6.4.8 Ecosystem Analysis: WLF Coverage of 50 External Tools

To contextualize CogPIE within the broader password generation ecosystem, we conducted a comprehensive analysis of 50 external wordlist generation tools, representing 84,000+ combined GitHub stars across 7 algorithmic categories: C1 (Profile/Target-based), C2 (Combinatoric/Exhaustive), C3 (Rule/Mangling), C4 (Probabilistic/Statistical), C5 (Neural/Deep Learning), C6 (Scraping/Extraction), and C7 (Hybrid Cognitive). Each tool was cloned, inspected, and mapped to equivalent WLF modules.

**Table 9: Ecosystem Coverage Summary**

| Metric | Value |
|--------|-------|
| Total tools analyzed | 50 |
| Full coverage by WLF (>= external) | 39 (78%) |
| 90%+ coverage | 4 (8%): pydictor, princeprocessor, elpscrk, kwprocessor |
| 80%+ coverage | 3 (6%): Passhunt, passpwn, kwprocessor |
| Data/reference only (not algorithms) | 4 (8%) |
| Algorithmic functions covered | 46/46 (100%) |

**Key algorithmic coverage findings:**

1. **WLF is the only framework covering all 7 categories (C1-C7).** No external tool covers more than 2 categories. hashcat (C3) and pydictor (C1+C2) are the broadest external tools.

2. **WLF has 35+ unique capabilities** not found in any external tool, including: cognitive bias modeling (CogPIE 5-layer pipeline), 6 neural architectures (GAN, VAE, Transformer, Diffusion, TCN, NFlow), evolutionary optimization (genetic_engine, map_elites), reinforcement learning routing (bandit_router, rl_router), semantic PCFG, domain-specific PCFG, Brazilian cultural patterns, phonetic generation, password DNA analysis, PII correlation, and temporal drift modeling.

3. **5 minor gaps identified** for future work: extended biographical fields from pydictor SEDB (ID card, job number), keyboard walk depth from kwprocessor, elpscrk's leveled complexity system, PRINCE chain depth configuration, and seasonal rotation patterns from passpwn. None represents a fundamental limitation.

4. **130+ WLF modules vs 1-3 per external tool:** The architectural advantage is structural. External tools are purpose-built for a single paradigm; WLF orchestrates modules across paradigms through a unified pipeline with GPU acceleration, adaptive routing, and priority ranking.

#### 6.4.9 Real-World Validation: Brazilian Leaked Credentials (Large-Scale)

To validate CogPIE against real-world compromised credentials (as opposed to synthetic personas), we constructed a benchmark from publicly indexed credential leak data. Using IntelX intelligent search, we collected 260,853 unique email:password pairs from Brazilian breach compilations (Collection #2, Collection #4, stealer logs targeting ig.com.br, itau.com.br, americanas.com.br domains).

**Data curation pipeline:**

1. **Raw pool:** 260,853 unique credentials
2. **Filter numeric-only passwords:** removed 40,916 (pure digit sequences provide no PII signal)
3. **Filter passwords < 6 characters:** removed 2,994 (too short for meaningful PII embedding)
4. **Require PII in password:** retained only passwords containing at least one substring from the email's extracted name components, yielding 13,546 credentials (5.2% of raw pool)
5. **Random sample:** 1,000 credentials (seed=2026) from the filtered pool

Each credential's PII profile was automatically extracted from its email address (local part decomposition into names, dates, numbers; domain company extraction). Five algorithms were tested with a budget of 50,000 candidates each.

**Table 9: Real-World Brazilian Credential Benchmark (N=1,000 PII-filtered, @50K candidates)**

| Algorithm | Hits | Coverage | Median Rank | Avg Time |
|-----------|------|----------|-------------|----------|
| **CogPIE** | **505** | **50.5%** | **17** | 184.0ms |
| CUPP | 388 | 38.8% | 44 | 0.1ms |
| bopscrk | 388 | 38.8% | 110 | 0.1ms |
| elpscrk | 363 | 36.3% | 75 | 0.1ms |
| psudohash | 242 | 24.2% | 79 | 0.0ms |

Key findings:

1. **CogPIE achieves 50.5% coverage**, a +11.7pp advantage over both CUPP and bopscrk (38.8%), and +26.3pp over psudohash (24.2%). On 1,000 real leaked credentials where passwords contain PII, CogPIE correctly predicts one in two passwords within 50,000 guesses.

2. **Median rank of 17 is 2.6x better than CUPP (44) and 6.5x better than bopscrk (110).** CogPIE's probabilistic ranking places correct guesses near the top of the candidate list, critical for rate-limited online attack scenarios.

3. **CogPIE is a strict superset in the small benchmark (N=17):** every password found by any other tool was also found by CogPIE, plus additional unique hits. At scale (N=1,000), CogPIE captures 117 passwords missed by all four competitors.

4. **Ecological validity:** Unlike the synthetic persona benchmark (Section 6.4.7) where CogPIE reached 89.1%, real-world coverage is naturally lower (50.5%) because: (a) real passwords exhibit greater diversity and randomness; (b) PII extraction from email addresses captures only partial context; (c) many PII-containing passwords use patterns beyond the model's scope (e.g., phone numbers, CPF fragments). Nevertheless, CogPIE maintains consistent superiority over all baselines.

5. **Convergence analysis at N=1,000:** Coverage rates stabilize after ~400 samples (CogPIE oscillates within 49-52%), confirming statistical reliability of the results. The 95% CI for CogPIE coverage is approximately [47.4%, 53.6%].

#### 6.4.10 Exhaustive Benchmark: Full Leaked Credential Corpus (N=13,487)

To eliminate sampling bias and validate the robustness of results from Section 6.4.9, we ran the benchmark against the **entire PII-filtered corpus** of 13,487 valid credentials (from 13,546 after PII filtering; 59 excluded due to password length outside the 4-40 character range). The candidate budget was set to 10,000 per credential, and the benchmark was expanded to 7 tools (adding pydictor and longtongue to the original 5).

**Corpus domain distribution:**

| Category | Credentials | % |
|----------|-------------|---|
| Global webmail (gmail, hotmail, yahoo, outlook) | 9,890 | 73.3% |
| Other domains | 3,000 | 22.2% |
| CN/TW/HK | 517 | 3.8% |
| .br (Brazilian domains) | 80 | 0.6% |

**Table 10: Exhaustive Real-World Credential Benchmark (N=13,487, @10K candidates, 7 tools)**

| Algorithm | Hits | Coverage | CI Cov. | Exclusive | Med. Rank | Mean Rank |
|-----------|------|----------|---------|-----------|-----------|-----------|
| **CogPIE** | **6,286** | **46.6%** | **51.4%** | **541** | 20 | 759.7 |
| CUPP/WLF | 5,161 | 38.3% | 38.5% | 674 | 8 | 92.7 |
| bopscrk | 4,799 | 35.6% | 36.5% | 2 | 6 | 6.4 |
| elpscrk | 4,652 | 34.5% | 35.0% | 3 | 9 | 10.1 |
| psudohash | 4,418 | 32.8% | 33.2% | 9 | 20 | 21.4 |
| pydictor | 4,267 | 31.6% | 32.4% | 2 | 10 | 14.4 |
| longtongue | 3,446 | 25.6% | 26.3% | 0 | 9 | 10.3 |
| **Combined** | **7,032** | **52.1%** | | | | |

Key findings from the exhaustive benchmark:

1. **CogPIE leads with 46.6% exact coverage and 51.4% case-insensitive**, a +8.3pp advantage over the runner-up (CUPP, 38.3%). Across 13,487 real credentials with embedded PII, CogPIE correctly predicts nearly half of all passwords within just 10,000 guesses.

2. **541 exclusive CogPIE hits:** passwords found only by CogPIE and by none of the other 6 tools. This demonstrates that the cognitive engine captures password generation patterns inaccessible to purely combinatorial transformations.

3. **Combined coverage of 52.1%** indicates that even merging all 7 tools, only 5.5pp additional are recovered beyond CogPIE alone. CogPIE accounts for 89.4% of the combined coverage (6,286/7,032).

4. **CUPP shows 674 exclusive hits** despite lower total coverage. This reflects simple concatenation patterns (e.g., name+4-digit year without separator) that CUPP generates but CogPIE ranks lower due to their low cognitive probability. These hits tend to appear at very high CogPIE ranks (mean rank 759.7 vs. CUPP's 92.7), indicating CogPIE generates them but positions them below the 10,000 threshold.

5. **longtongue with zero exclusives** confirms its search space is a complete subset of the other tools; bopscrk (2), elpscrk (3) and pydictor (2) show minimal exclusivity.

6. **Consistency with N=1,000 sample:** CogPIE's 46.6% coverage on the full corpus is consistent with the 50.5% observed in the sample (Section 6.4.9), within expected variation given that N=1,000 used a 50K candidate budget vs. 10K in the exhaustive run. When normalized by budget, CogPIE's per-candidate efficiency is superior.

7. **Cross-cultural validation:** Although originally designed for Brazilian names, the 13,487-credential corpus is predominantly global (73.3% webmail, 3.8% CN/TW/HK). The 46.6% coverage on this diverse corpus confirms the universality of cognitive bias in PII-based password construction.

### 6.5 Limitations

1. **Corpus diversity:** Initial evaluations used the RockYou corpus (14.3M passwords, 2009-era). The Brazilian credential leak benchmarks (Section 6.4.9, N=1,000 sample; Section 6.4.10, N=13,487 exhaustive) provide validation on contemporary real-world data (260K+ credentials from 2020s breach compilations) across a globally diverse corpus (73.3% global webmail, 3.8% CN/TW/HK), but broader cross-cultural and cross-temporal validation would strengthen generalizability.

2. **Cultural specificity:** The current nickname database and accent handling are focused on Brazilian Portuguese names. Extending to other cultures would require additional linguistic resources.

3. **PII extraction accuracy:** The automatic PII correlator infers profiles from password patterns (embedded names, dates). False positives in profile extraction could inflate or deflate hit rates. Manual verification of a subset suggests ~85% extraction accuracy.

4. **Candidate set size:** Without budget constraints, CogPIE generates 100,000+ candidates. In online attack scenarios with rate limiting, the ranking quality becomes critical for selecting the most promising candidates within a small guess budget.

## 7. Discussion

### 7.1 Implications for Password Security

Our results provide quantitative evidence for a well-known but often underappreciated conclusion: human-generated passwords are fundamentally insecure against targeted attacks. When an attacker possesses even basic personal information about a target (names, dates, interests), a systematic cognitive bias model can correctly predict 50-90% of PII-derived passwords, depending on profile completeness and evaluation context. At the standalone level with 1M training passwords, CogPIE achieves 75.95% hit rate within just 1,000 guesses, with a median rank of 35. In the large-scale comparative benchmark with 2,000 targets, CogPIE maintains a consistent advantage over CUPP-style heuristics (50.15% vs. 47.55%). In the persona benchmark against 8 real external tools (Section 6.4.7), CogPIE v0.2 achieves 88.6% average coverage, surpassing the best individual competitor (elpscrk, 51.1%) by +37.5pp and the combined interleaved union of all tools (82.2%) by +6.4pp. The real-world Brazilian credential benchmark (Section 6.4.9) confirms ecological validity: CogPIE achieves 50.5% coverage on 1,000 real leaked passwords with median rank 17, outperforming all baselines by +11.7pp or more.

This finding aligns with the broader literature:
- Wang et al. (2016) found 30% of modified passwords crackable within 10 guesses
- Cloudflare (2024) reported 41% of successful authentications involving leaked credentials
- Das et al. (2014) estimated 43-51% password reuse across sites
- A 2026 survey found 76.2% of users only make small modifications to existing passwords

### 7.2 Defense Recommendations

Based on our analysis, we recommend:

1. **Password managers with random generation:** The only reliable defense against CogPIE-class attacks. Cryptographically random passwords have no cognitive patterns to exploit.

2. **Multi-factor authentication:** Renders password guessing insufficient for account compromise, regardless of password strength.

3. **FIDO2/WebAuthn passkeys:** Eliminates passwords entirely, removing the cognitive vulnerability from the authentication chain.

4. **Breach credential screening:** As recommended by NIST SP 800-63B, checking new passwords against known leaked databases prevents the reuse of compromised credentials.

5. **Password policy modernization:** Moving from composition rules (which CogPIE easily satisfies) to minimum length requirements and breach checking (which address the actual vulnerability).

### 7.3 Ethical Considerations

CogPIE is designed for authorized security testing, specifically for penetration testers evaluating the strength of user-chosen passwords within the scope of authorized engagements. The algorithm's existence does not create new attack capabilities; rather, it systematizes techniques already known to sophisticated attackers and makes them available for defensive assessment.

We emphasize:
- All testing must be performed with explicit authorization
- Personal information used in profiles must be obtained through legitimate means within the engagement scope
- Results should be used to improve organizational password policies, not to compromise individual accounts
- The strongest defense remains eliminating human-chosen passwords entirely

### 7.4 Future Work

Several directions for future research emerge:

1. **Cross-cultural expansion:** Extending the semantic expansion layer to support additional languages, name conventions, and cultural password patterns.

2. **Temporal modeling:** Incorporating password evolution patterns (how users modify passwords over time) as documented by Wang et al. (2016).

3. **Active learning:** Using feedback from successful and unsuccessful guesses to dynamically adjust the model weights during an assessment.

4. **Neural network integration:** Replacing or augmenting the Markov/PCFG hybrid with transformer-based models fine-tuned on profile-specific patterns.

5. **Passphrase analysis:** Extending cognitive bias modeling to multi-word passphrases, which exhibit different but equally exploitable patterns.

### 7.5 GPU Acceleration

CogPIE includes an optional CUDA-accelerated backend for Layer 3 (Probabilistic Ranking), which dominates pipeline runtime at 96-97% of total execution time. The GPU backend implements three key optimizations:

1. **Numpy bulk character encoding:** Replaces per-candidate Python loops with vectorized numpy array operations for converting password strings to index tensors, eliminating the primary CPU bottleneck.

2. **GPU hash tables with open addressing:** Context key lookup for positional Markov scoring uses pre-built hash tables stored as GPU tensors, enabling fully vectorized probing without CPU-GPU round trips.

3. **Batched tensor gather operations:** All Markov n-gram lookups and PCFG structural scoring run as batched GPU gather/index operations over the full candidate set simultaneously.

**Performance results** (NVIDIA GeForce RTX 4060 Laptop GPU, 8 GB VRAM):

| Training Corpus | Candidates | CPU Time | GPU Time | Speedup | VRAM |
|---|---|---|---|---|---|
| 100K passwords | 97K | 2.91s | 0.74s | 3.93x | 52 MB |
| 1M passwords | 97K | 15.12s | 0.75s | 20.18x | 174 MB |

The speedup scales with corpus size because larger training corpora produce denser Markov tables where GPU parallelism provides greater benefit. The 1M corpus benchmark demonstrates that CogPIE can score approximately 130,000 candidates per second on GPU, compared to approximately 6,400 per second on CPU. The GPU backend falls back transparently to CPU when CUDA is unavailable.

## 8. Conclusion

We presented CogPIE, a 5-layer cognitive pattern inference engine for targeted password candidate generation. By explicitly modeling the psychological biases that drive human password creation, CogPIE achieves a 60.9% hit rate on synthetic benchmarks, outperforming CUPP-style profiling by 17.8%. On real breach data (RockYou), CogPIE reaches 75.95% at budget 1,000 with 1M training corpus and 2,000 PII-bearing targets, with a median rank of 35 (MRR 0.137). In large-scale comparative evaluation with 2,000 targets and 1M training passwords, CogPIE achieves 50.15% coverage versus CUPP-style (47.55%) and Markov-3 (4.80%), while non-profile approaches score 0%.

Our formal mathematical framework provides convergence guarantees for the hybrid Markov/PCFG ranking system. The CUDA-accelerated backend achieves a 20x speedup over CPU scoring on 1M-corpus workloads, generating 10,000 ranked candidates in under 0.75 seconds per profile on a laptop GPU. The modular architecture enables extension to additional cultural contexts and integration with existing password auditing tools.

The central thesis of this work, that passwords generated "from the head" always resort to patterns derived from cognitive context, is supported by both our experimental results and the extensive body of prior literature. The measurable cognitive bias in password creation is not a failure of user education or policy design; it is a fundamental property of human cognition. Password managers with cryptographically random generation represent the only provably secure defense against this class of vulnerability.

## References

1. Abdrabou, Y., Riber, M., Steinert, A., et al. (2021). "Cognitive Load and Password Strength: A Pupillometry Study." In Proceedings of the 2021 CHI Conference on Human Factors in Computing Systems.

2. Bonneau, J. (2012). "The Science of Guessing: Analyzing an Anonymized Corpus of 70 Million Passwords." In IEEE Symposium on Security and Privacy, pp. 538-552. DOI: 10.1109/SP.2012.49.

3. Bonneau, J. (2012). "Statistical Metrics for Individual Password Strength." In Security Protocols Workshop.

4. Cloudflare (2024). "Leaked Credentials in Authentication Traffic." Cloudflare Radar Report.

5. Das, A., Bonneau, J., Caesar, M., Borisov, N., and Wang, X. (2014). "The Tangled Web of Password Reuse." In Network and Distributed System Security Symposium (NDSS).

6. Durmuth, M., Angelstorf, F., Castelluccia, C., Perito, D., and Chaabane, A. (2015). "OMEN: Faster Password Guessing Using an Ordered Markov Enumerator." In Engineering Secure Software and Systems (ESSoS), LNCS 8978, pp. 119-132.

7. Florencio, D. and Herley, C. (2007). "A Large-Scale Study of Web Password Habits." In Proceedings of the 16th International Conference on World Wide Web (WWW '07).

8. Hitaj, B., Gasti, P., Ateniese, G., and Perez-Cruz, F. (2019). "PassGAN: A Deep Learning Approach for Password Guessing." In Applied Cryptography and Network Security (ACNS). arXiv:1709.00440.

9. Imperva (2010). "Consumer Password Worst Practices." Imperva Application Defense Center Report.

10. Katz, S. M. (1987). "Estimation of Probabilities from Sparse Data for the Language Model Component of a Speech Recognizer." IEEE Transactions on Acoustics, Speech, and Signal Processing, 35(3), pp. 400-401.

11. Li, Y., Wang, H., and Sun, K. (2017). "Personal Information in Passwords and Its Security Implications." IEEE Transactions on Information Forensics and Security, 12(10). DOI: 10.1109/TIFS.2017.2705627.

12. Ma, J., Yang, W., Luo, M., and Li, N. (2014). "A Study of Probabilistic Password Models." In IEEE Symposium on Security and Privacy, pp. 689-704.

13. Mebus, M. (2010). "CUPP: Common User Passwords Profiler." GitHub Repository.

14. Narayanan, A. and Shmatikov, V. (2005). "Fast Dictionary Attacks on Passwords Using Time-Space Tradeoff." In ACM Conference on Computer and Communications Security (CCS).

15. NIST (2017, revised 2024). "Digital Identity Guidelines: Authentication and Lifecycle Management." NIST Special Publication 800-63B.

16. Rando, J., Perez-Cruz, F., and Hitaj, B. (2023). "PassGPT: Password Modeling and (Guided) Generation with Large Language Models." In European Symposium on Research in Computer Security (ESORICS). arXiv:2306.01545.

17. Veras, R., Collins, C., and Thorpe, J. (2014). "On Semantic Patterns of Passwords and their Security Impact." In Network and Distributed System Security Symposium (NDSS).

18. Wang, D. and Jian, G. (2014). "Zipf's Law in Passwords." IACR ePrint Archive, 2014/631. Later published in IEEE TIFS, 2017.

19. Wang, D., Zhang, Z., Wang, P., Yan, J., and Huang, X. (2016). "Targeted Online Password Guessing: An Underestimated Threat." In ACM Conference on Computer and Communications Security (CCS).

20. Wang, D., Cheng, H., Wang, P., Huang, X., and Jian, G. (2016). "The Next Domino to Fall: Empirical Analysis of User Passwords across Online Services." In ACM Conference on Computer and Communications Security (CCS).

21. Weir, M., Aggarwal, S., de Medeiros, B., and Glodek, B. (2009). "Password Cracking Using Probabilistic Context-Free Grammars." In IEEE Symposium on Security and Privacy, pp. 391-405. DOI: 10.1109/SP.2009.8.

22. Wheeler, D. L. (2016). "zxcvbn: Low-Budget Password Strength Estimation." In USENIX Security Symposium.

23. Xie, X. (2020). "Modified TarGuess-I: Keyboard Patterns and Popular Passwords as Password Guessing Threats." Master's Thesis.

24. Survey Authors (2026). "Examining User Behavior and Cognitive Biases in Personal Password Security." arXiv:2607.19586.

25. AI Password Study Authors (2026). "AI vs. User-Generated Passwords: Strength, Memorability, and Cognitive Bias." arXiv:2604.19410.

26. MDPI Entropy Review (2023). "A Systematic Review of Password Guessing Methods." MDPI Entropy.

27. Castelluccia, C. and Durmuth, M. (2012). "Adaptive Password-Strength Meters from Markov Models." In Network and Distributed System Security Symposium (NDSS).

28. Dell'Amico, M. and Filippone, M. (2015). "Monte Carlo Strength Evaluation: Fast and Reliable Password Checking." In ACM Conference on Computer and Communications Security (CCS).

29. Ur, B., Segreti, S. M., Bauer, L., et al. (2015). "Measuring Real-World Accuracies and Biases in Modeling Password Guessability." In USENIX Security Symposium.

30. Kelley, P. G., Komanduri, S., Mazurek, M. L., et al. (2012). "Guess Again (and Again and Again): Measuring Password Strength by Simulating Password-Cracking Algorithms." In IEEE Symposium on Security and Privacy.

31. Melicher, W., Ur, B., Segreti, S. M., et al. (2016). "Fast, Lean, and Accurate: Modeling Password Guessability Using Neural Networks." In USENIX Security Symposium.

32. Golla, M. and Durmuth, M. (2018). "On the Accuracy of Password Strength Meters." In ACM Conference on Computer and Communications Security (CCS).

33. Pal, B. and Chua, T. (2019). "A Comparison of Approaches to Large-Scale Data Analysis." In Pacific-Asia Conference on Knowledge Discovery and Data Mining.

34. Adams, A. and Sasse, M. A. (1999). "Users Are Not the Enemy." Communications of the ACM, 42(12), pp. 40-46.

35. Yan, J., Blackwell, A., Anderson, R., and Grant, A. (2004). "Password Memorability and Security: Empirical Results." IEEE Security & Privacy, 2(5), pp. 25-31.

36. Forget, A., Chiasson, S., van Oorschot, P. C., and Biddle, R. (2008). "Improving Text Passwords Through Persuasion." In Symposium on Usable Privacy and Security (SOUPS).

37. Shay, R., Komanduri, S., Kelley, P. G., et al. (2010). "Encountering Stronger Password Requirements: User Attitudes and Behaviors." In Symposium on Usable Privacy and Security (SOUPS).

38. Ur, B., Noma, F., Bees, J., et al. (2015). "'I Added '!' at the End to Make It Secure': Observing Password Creation in the Lab." In Symposium on Usable Privacy and Security (SOUPS).

39. Wash, R., Rader, E., Berman, R., and Wellmer, Z. (2016). "Understanding Password Choices: How Frequently Entered Passwords Are Re-used Across Websites." In Symposium on Usable Privacy and Security (SOUPS).

40. Oesch, S. and Ruoti, S. (2020). "That Was Then, This Is Now: A Security Evaluation of Password Generation, Storage, and Autofill in Browser-Based Password Managers." In USENIX Security Symposium.

41. Pasquini, D., Gangwal, A., Ateniese, G., Bernaschi, M., and Conti, M. (2021). "Improving Password Guessing via Representation Learning." In IEEE Symposium on Security and Privacy.

42. Pal, B., Daniel, T., Chatterjee, R., and Ristenpart, T. (2019). "Beyond Credential Stuffing: Password Similarity Models Using Neural Networks." In IEEE Symposium on Security and Privacy.

---

## Appendix A: Profile Schema

Complete JSON schema for CogPIE target profiles:

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "names": {"type": "array", "items": {"type": "string"}},
        "dates": {"type": "array", "items": {"type": "string"}},
        "keywords": {"type": "array", "items": {"type": "string"}},
        "pets": {"type": "array", "items": {"type": "string"}},
        "companies": {"type": "array", "items": {"type": "string"}},
        "phones": {"type": "array", "items": {"type": "string"}},
        "emails": {"type": "array", "items": {"type": "string"}},
        "old_passwords": {"type": "array", "items": {"type": "string"}},
        "numbers": {"type": "array", "items": {"type": "string"}}
    }
}
```

## Appendix B: Benchmark Methodology

Primary evaluation was conducted using real breach data from publicly available corpora (RockYou):

1. A corpus of up to 1,000,000 passwords was sampled from the RockYou leak dataset.
2. The `pii_correlator` module identified passwords with detectable PII (names from 5-language databases: EN, PT-BR, ES, FR, DE; dates; numeric sequences).
3. PII-bearing passwords were extracted as test targets; remaining passwords constituted the training set.
4. For each test password, a synthetic profile was derived from its detected PII components (name, dates).
5. CogPIE was trained on the training split and evaluated by generating up to 100,000 candidates per target profile.
6. Hit rate is defined as: for each target password, 1 if the password appears in the generated candidate list at budget K, 0 otherwise. hit@K = sum(hits) / total_targets.
7. Six algorithms were compared: CogPIE (full 5-layer pipeline), CUPP-style (deterministic concatenation), Markov order-3, Frequency baseline, Levenshtein (edit-distance mutations), and Random.
8. Parameters: alpha=0.4, beta=0.2, Markov order=3. Training time: ~3.2s for 500K passwords.
9. Scale evaluation: 500K and 1M training corpora with 500 and 2000 test targets respectively.

### B.2 Exhaustive Real-World Credential Benchmark (Phase 3)

1. Corpus of 260,853 credentials collected via IntelX from Brazilian breach compilations.
2. Filtering pipeline: removal of numeric-only passwords (40,916), short <6 char (2,994), and retention of only passwords with embedded PII: 13,546 credentials.
3. Additional filtering: passwords between 4-40 characters: 13,487 valid credentials.
4. PII automatically extracted from email addresses (local part decomposition + domain).
5. 7 tools evaluated: CogPIE, CUPP/WLF, bopscrk, elpscrk, psudohash, pydictor, longtongue.
6. Budget: 10,000 candidates per credential.
7. Metrics: exact coverage, case-insensitive coverage, exclusive hits, median and mean rank.
8. Total execution time: ~22 minutes (13,487 credentials x 7 tools).

## Appendix C: Cognitive Bias Summary Table

| Bias | Effect on Passwords | Prevalence | CogPIE Layer |
|------|-------------------|------------|-------------|
| Anchoring | Base word remains recognizable | >90% | Layer 1, 2 |
| Serial Position | Modifications at start/end | >85% (end) | Layer 2 |
| Familiarity | Personally meaningful tokens | >70% | Layer 1 |
| Minimal Effort | Smallest change to satisfy policy | >60% | Layer 2, 5 |
| Status Quo | Reuse with minor modification | ~76% | Layer 1 (old_pw) |
| Hyperbolic Discounting | Prioritize memorability over security | ~76% | All layers |
| Availability | Use recently encountered info | ~40% | Layer 1 |

## Appendix D: MITRE ATT&CK Mapping

Relevant MITRE ATT&CK techniques for the CogPIE context:

| Technique | ID | Relation to CogPIE |
|---|---|---|
| Brute Force: Password Guessing | T1110.001 | CogPIE improves efficiency of this technique |
| Brute Force: Password Spraying | T1110.003 | CogPIE candidates as spray list |
| Credentials from Password Stores | T1555 | Recommended defense (password vaults) |
| Valid Accounts | T1078 | Result of compromised passwords |
| Phishing for Information | T1598 | PII collection for profiles |
| Gather Victim Identity Information | T1589 | Profile construction for CogPIE |

## Appendix E: CWE and OWASP Mapping

| CWE/OWASP | ID | Relation |
|---|---|---|
| Weak Password Requirements | CWE-521 | Policies that CogPIE trivially satisfies |
| Use of Hard-coded Password | CWE-259 | Predictable passwords due to cognitive bias |
| Identification and Authentication Failures | OWASP A07:2021 | Primary impact category |
| Broken Authentication | OWASP Top 10 | Risk mitigated by MFA and passkeys |

## Appendix F: Recommended Defenses (NIST D3FEND)

| D3FEND Technique | ID | Application |
|---|---|---|
| Multi-factor Authentication | D3-MFA | Fully mitigates guessing attacks |
| Credential Hardening | D3-CH | Robust password policies |
| Account Locking | D3-AL | Rate limiting against online attempts |
| Credential Rotation | D3-CR | Periodic rotation with leak screening |

## Appendix G: Unit Test Suite as Experimental Evidence

CogPIE validation includes a comprehensive suite of 55 automated unit tests verifying each pipeline component. These tests constitute reproducible evidence of functional correctness and serve as regression benchmarks for future modifications. Full documentation organized by layer follows.

### G.1 Layer 1: Semantic Expansion (8 tests)

| Test | Validates | Inputs | Assertions |
|---|---|---|---|
| `test_expand_token_basic` | Case variant generation | "Andre" | Produces lowercase, uppercase, capitalize; >5 variants |
| `test_expand_token_accents` | PT-BR accent handling | "Joao" | Generates "joao", "JOAO"; preserves unaccented variants |
| `test_expand_token_nicknames` | Cultural nickname database | "Eduardo" | Contains "dudu" or "edu" (BR nicknames) |
| `test_expand_token_leet` | Partial leetspeak substitution | "password" | At least one variant with "4" or "0" |
| `test_expand_date_full` | DD/MM/YYYY dates | "15/03/1990" | Generates "1990", "90", "15031990" |
| `test_expand_date_year_only` | Year-only dates | "1985" | Generates "1985", "85" |
| `test_expand_profile_names` | Full profile with names | "Andre Henrique", "Maria Silva" | >5 tokens; contains "andre"; initials "ah"/"AH" |
| `test_expand_profile_phones` | Phone suffix extraction | "11987654321" | Last 4 digits "4321" extracted |

### G.2 Layer 2: Cognitive Transforms (5 tests)

| Test | Validates | Inputs | Assertions |
|---|---|---|---|
| `test_capitalization` | 7 capitalization patterns | "password" | Contains "Password", "PASSWORD", "password" |
| `test_numeric_suffixes` | Common suffixes + year range | "test" | Contains "test1", "test123"; some with "1990" |
| `test_leet_partial` | Partial leet (1 substitution) | "password" | Some variant with "4" (a->4) |
| `test_transform_token` | Full per-token pipeline | "andre" | >50 candidates generated |
| `test_transform_pair` | Pair concatenation | "andre", "1990" | Some candidate contains both tokens |

### G.3 Layer 3: Hybrid Markov+PCFG Ranking (3 tests)

| Test | Validates | Inputs | Assertions |
|---|---|---|---|
| `test_train_and_score` | Score reflects training frequency | Corpus: "password123", "letmein", etc. | score("password123") > score("xKz9!mQ#vR2$") |
| `test_rank_ordering` | Probability ordering | Corpus with "password" repeated 10x | "password" ranked above "xz9qmvr2" |
| `test_train_from_file` | File-based training | 100 passwords "testpassN" | count = 100 |

### G.4 Layer 4: Entropy Scoring (4 tests)

| Test | Validates | Inputs | Assertions |
|---|---|---|---|
| `test_estimate_guesses_simple` | Guess estimation | "123456" with rank=1 | guesses = 1.0 |
| `test_entropy_positive` | Positive practical entropy | "Xk9!mQ#vR2$pL" | entropy > 0 |
| `test_zxcvbn_score_range` | Entropy-to-score mapping | Entropy 5,15,25,30,40 | Scores 0,1,2,3,4 respectively |
| `test_score_candidate_structure` | Complete metadata | "Password123!" | Dict with "candidate", "entropy_bits", "score" |

### G.5 Layer 5: Policy Filtering (3 tests)

| Test | Validates | Inputs | Assertions |
|---|---|---|---|
| `test_policy_accepts` | Min length + require_digit | Policy(min_length=8, require_digit=True) | "Password1"=True; "short"=False; "NoDigitsHere"=False |
| `test_policy_classes` | Min character classes | Policy(min_char_classes=3) | "Abc123"=True; "abcdef"=False |
| `test_filter_candidates` | Filtering with deduplication | ["pass","Password1","ab"] with min_length=6 | Only "Password1" survives |

### G.6 Integrated Pipeline (5 tests)

| Test | Validates | Inputs | Assertions |
|---|---|---|---|
| `test_full_pipeline_no_corpus` | 5-layer pipeline without training | "Carlos Silva", 1985, "flamengo", "Rex" | >0 results; contains "carlos" or "silva" |
| `test_full_pipeline_with_corpus` | Pipeline with trained corpus | "Maria", 2000, "amor" + 400-password corpus | >0 results after training |
| `test_stream_mode` | Streaming mode | "Pedro", 1995, "gato" | Generates strings; correct types |
| `test_stats_populated` | Pipeline metrics | Basic profile | Stats contains "total_time", "output_count" |
| `test_policy_integration` | End-to-end policy | "Ana", 2010, "sol" with min_length=8 | All candidates >= 8 chars, >= 2 classes |

### G.7 PII Correlation and Training Pipeline (18 tests)

| Test | Validates | Inputs | Assertions |
|---|---|---|---|
| `test_name_detection_english` | EN names | "michael123" | Category: name_based/hybrid; name: "michael" |
| `test_name_detection_portuguese` | PT-BR names | "fernanda2024" | Category: name_based/hybrid; name: "fernanda" |
| `test_name_detection_spanish` | ES names | "alejandro99" | Category: name_based/hybrid; name: "alejandro" |
| `test_name_detection_french` | FR names | "sebastien01" | Category: name_based/hybrid; name: "sebastien" |
| `test_name_detection_german` | DE names | "maximilian7" | Category: name_based/hybrid; name: "maximilian" |
| `test_date_detection_full` | Full dates | "pass15031990" | date_found != None |
| `test_date_detection_year` | Embedded year | "love2024ever" | date_type = "year_4" |
| `test_hybrid_name_date` | Name+date combination | "maria1990" | Category hybrid; both name and date detected |
| `test_sequential_detection` | Numeric sequences | "123456" | Category: sequential |
| `test_qwerty_sequential` | Keyboard sequences | "qwerty" | Category: sequential |
| `test_random_like` | Random passwords | "xkj9!mQ" | Category: random_like |
| `test_empty_password` | Empty string | "" | Category: random_like |
| `test_short_password` | Short password | "ab" | Category: random_like |
| `test_name_databases_populated` | Name databases | 5 languages | EN>100, PT>100, ES>100, FR>100, DE>100, ALL>500 |
| `test_cross_cultural_coverage` | Cross-cultural coverage | james, joao, juan, pierre, hans | All detected in password + "2024" |
| `test_confidence_range` | Confidence interval | "michael1990" | 0.0 <= confidence <= 1.0 |
| `test_corpus_stats_in_memory` | In-memory statistics | 5 varied passwords | total=5; as_dict() functional |
| `test_corpus_stats_from_file` | File-based statistics | 4 passwords in file | total=4; pii_detectable_pct > 0 |

### G.8 Training, Persistence and Benchmark (9 tests)

| Test | Validates | Inputs | Assertions |
|---|---|---|---|
| `test_train_from_corpus` | Training count | 16 distinct passwords | count = 16 |
| `test_train_from_corpus_max_lines` | Line limit | max_lines=5 | count = 5 |
| `test_save_and_load_model` | Pickle serialization | Trained model, save+load | trained_count preserved; generates results |
| `test_generate_after_training` | Post-training generation | "maria", 2024, "love" | >0 results; correct types |
| `test_trained_model_scores_higher` | Training improves ranking | "michael", 1990 trained | "michael1990" or "Michael1990" in top 1000 |
| `test_build_small_corpus` | Corpus pipeline | 7 raw passwords | Generates processed corpus, stats JSON, patterns JSON |
| `test_extract_synthetic_profile` | Profile extraction | "michael1990" | "michael" in names; "1990" in dates |
| `test_extract_no_pii` | No detectable PII | "xkj9mQ!!" | Returns None |
| `test_split_corpus` | Train/test split | 9 passwords, ratio=0.3 | train + test <= total; test >= 1 |

### G.9 Coverage Summary

- **55 tests** covering all 8 CogPIE modules
- **5 languages** validated for PII detection (EN, PT-BR, ES, FR, DE)
- **Execution time**: ~1.1s (all tests)
- **Framework**: pytest 9.0.2, Python 3.14.4
- **Layer coverage**: 100% of the 5 pipeline layers tested individually and integrated
- **Scenarios**: with and without training corpus; with and without policies; batch and streaming modes

All 55 tests pass consistently (300/300 in the full suite including other WordlistXPL-Forge modules), validating the functional correctness of each component and end-to-end pipeline integrity.

---

*This research was conducted for authorized security testing and academic purposes. All experiments used public leak data exclusively for scientific validation. The author advocates for the adoption of password managers and passwordless authentication as the primary defense against targeted password attacks.*
