# Comparação de Algoritmos Matemáticos em Ferramentas de Geração de Wordlists

**Andre Henrique de Oliveira** (@mrhenrike)
Uniao Geek Security Research

---

## 1. Introdução

Este documento apresenta uma análise comparativa dos algoritmos matemáticos utilizados pelas principais ferramentas de geração de wordlists, categorizando-as por paradigma algorítmico e técnica matemática central. O objetivo é posicionar o CogPIE e o WordlistXPL-Forge no panorama das ferramentas existentes, identificando lacunas e vantagens competitivas.

A análise cobre 25+ ferramentas, organizadas em 6 paradigmas algorítmicos fundamentais.

---

## 2. Taxonomia de Paradigmas Algorítmicos

### 2.1 Paradigma Combinatório/Enumerativo

Gera candidatos por enumeração exaustiva de combinações e permutações sobre um alfabeto ou conjunto de strings.

**Técnica matemática:** Produto cartesiano, permutações sem repetição, combinações com repetição.

**Complexidade:** O(|Σ|^n) onde |Σ| é o tamanho do alfabeto e n o comprimento, crescimento exponencial.

### 2.2 Paradigma Baseado em Regras (Mangling)

Aplica transformações determinísticas (regras) sobre uma wordlist base: toggle case, append, prepend, insert, delete, substitute, duplicate.

**Técnica matemática:** Funções de transformação compostas, cada regra é uma função f: String -> String aplicada em cadeia.

**Complexidade:** O(W * R) onde W é a wordlist base e R o número de regras.

### 2.3 Paradigma Probabilístico

Modela a distribuição de probabilidade de senhas reais e gera candidatos em ordem decrescente de probabilidade.

**Subclasses:**
- **Markov:** P(c_i | c_{i-1}, ..., c_{i-n}) com n-gramas posicionais
- **PCFG:** Gramáticas livres de contexto probabilísticas que decompõem senhas em classes terminais (L=letra, D=digito, S=simbolo) com probabilidades de produção
- **Neural:** Redes neurais (GAN, GPT, VAE, TCN) treinadas em corpus de senhas para geração sequencial

### 2.4 Paradigma Direcionado/Perfil

Utiliza informação pessoal identificável (PII) do alvo para gerar candidatos específicos via concatenação e mutação de tokens pessoais.

**Técnica matemática:** Concatenação cartesiana de campos PII, com regras de transformação (leet, case, sufixos).

### 2.5 Paradigma de Extração/Scraping

Extrai palavras de fontes externas (websites, documentos, APIs) para construir wordlists contextuais.

**Técnica matemática:** Tokenização, frequência de termos (TF), filtragem por comprimento e tipo.

### 2.6 Paradigma Híbrido Cognitivo

Combina múltiplos paradigmas: expansão semântica, transformações baseadas em vieses cognitivos documentados, ranking probabilístico e filtragem por política.

**Técnica matemática:** Pipeline multi-camada integrando semântica, psicologia cognitiva e estatística probabilística.

---

## 3. Tabela Comparativa: Top 25+ Ferramentas de Geração de Wordlists

| # | Ferramenta | Repositório | Paradigma | Técnica Matemática Central | Linguagem | Pontos Fortes | Limitações | Tamanho Típico |
|---|-----------|-------------|-----------|---------------------------|-----------|---------------|------------|----------------|
| 1 | **crunch** | sourceforge/crunch | Combinatório | Permutação/combinação exaustiva sobre alfabeto com padrões de posição fixa | C | Rápido, controle total de charset e comprimento, suporta padrões com placeholders | Explosão exponencial, sem inteligência, sem priorização | 10^6 a 10^12+ |
| 2 | **maskprocessor** | hashcat/maskprocessor | Combinatório | Enumeração por máscara posicional (?u?l?l?l?d?d) | C | Integração nativa com hashcat, rápido, controle preciso por posição | Sem priorização, espaço cresce exponencialmente | 10^6 a 10^10+ |
| 3 | **CUPP (cupp.py)** | Mebus/cupp | Direcionado | Concatenação direta de campos PII + sufixos + separadores, produto cartesiano limitado | Python | Rápido (ms), intuitivo, alta taxa em cenários simples (hit@100 ~44%) | Regras fixas, sem priorização, satura em ~47% | 10^2 a 10^4 |
| 4 | **bopscrk** | r3nt0n/bopscrk | Direcionado | Concatenação de perfil + transformações (leet, case) configuráveis + módulo de letras de músicas (lyricpass) | Python | Transforms customizáveis via config, exclusão de já testados, módulo lyrics | Baseado em CUPP, sem ranking probabilístico | 10^3 a 10^5 |
| 5 | **BEWGor** | berzerk0/BEWGor | Direcionado | Concatenação biográfica (extensão de CUPP) com mais campos de entrada e regras de mutação | Python 2 | Mais campos que CUPP (data nascimento, apelidos, pets) | Python 2 only, sem manutenção, sem priorização | 10^2 a 10^4 |
| 6 | **pydictor** | LandGrey/pydictor | Regras + Direcionado | Motor de regras com charsets base, comprimento, prefixo/sufixo, filtros regex e encode | Python | Filtros avançados (regex, encoding), pipeline integrável | Sem modelo probabilístico, regras manuais | 10^4 a 10^8 |
| 7 | **Mentalist** | sc0tfree/mentalist | Regras (cadeia) | Chain model: Base Words -> Nodes de transformação (Case, Substitution, Append, Prepend) com exportação para regras hashcat/JtR | Python (GUI) | Interface gráfica, exporta como regras hashcat/JtR, cadeia visual | GUI only (sem CLI real), sem ranking, compatibilidade parcial | 10^4 a 10^7 |
| 8 | **rsmangler** | digininja/RSMangler | Regras (mangling) | Permutações e manipulações sobre wordlist: case toggle, reverse, double, leet, append/prepend numbers e symbols | Ruby | Similar a JtR rules com extras, pipeline unix | Sem priorização, wordlist-dependent, Ruby runtime | 10^4 a 10^6 |
| 9 | **John the Ripper (rules)** | openwall/john | Regras (mangling) | Motor de regras determinísticas: 50+ operações de mangling (toggle, insert, delete, overstrike, purge, etc.) | C | Padrão da indústria, 50+ operações, GPU via OpenCL, enorme base de regras comunitárias | Sem inteligência, explosão combinatória com muitas regras | 10^6 a 10^10+ |
| 10 | **Hashcat (rule engine)** | hashcat/hashcat | Regras (mangling) | Motor de regras: 40+ funções (case, rotate, duplicate, truncate, insert, replace, etc.) com GPU nativo | C/OpenCL | GPU nativo (10^9+ hash/s), regras compostas, integração com todas as ferramentas hashcat | Sem geração autônoma, requer wordlist base | 10^6 a 10^10+ |
| 11 | **PRINCE** | hashcat/princeprocessor | Combinatório (cadeia) | PRobability INfinite Chained Elements: concatenação de 1 a N palavras de um dicionário, ordered by frequency | C | Combinator avançado de única wordlist, eficaz "out of the box", controle de comprimento | Uma wordlist apenas, sem PII, sem modelo probabilístico real | 10^6 a 10^9 |
| 12 | **kwprocessor** | hashcat/kwprocessor | Combinatório (topológico) | Keyboard walk: enumeração de caminhos adjacentes em mapa de teclado configurável (QWERTY, AZERTY, etc.) | C | Único para padrões de teclado (qwerty, 1qaz2wsx), configurável, MIT | Específico para keyboard walks, não gera outros tipos | 10^3 a 10^6 |
| 13 | **OMEN** | RUB-SysSec/OMEN | Probabilístico (Markov) | Cadeias de Markov posicionais com n-gramas discretizados em níveis de probabilidade, enumeração ordered | C | >40% em 90M tentativas, 8x mais eficiente que JtR Markov, ordered by probability | Não usa PII, collapse com escala, comprimento fixo por run | 10^6 a 10^10 |
| 14 | **PCFG Cracker** | lakiw/pcfg_cracker | Probabilístico (PCFG) | Gramáticas livres de contexto probabilísticas: decomposição L^nD^mS^k com probabilidades aprendidas de corpus | Python | Captura estrutura macro, ordenação inerente, extensível com novas terminais | Granularidade limitada, caro computacionalmente, codebase instável | 10^6 a 10^9 |
| 15 | **Personal-PCFG** | (Li et al., 2017) | Probabilístico + Direcionado | PCFG estendida com 6 tipos de PII (nome, nascimento, email, telefone, conta, doc) como terminais gramaticais | Academico | Integra PII na gramática PCFG, fundamentação formal | Número fixo de tipos PII, sem expansão semantica, sem publicação completa | 10^4 a 10^7 |
| 16 | **TarGuess** | (Wang et al., 2016) | Probabilístico + Direcionado | 7 modelos matemáticos combinando PII com probabilidades condicionais para adivinhação online direcionada | Academico | Fundamentação formal, 7 modelos especializados, 142% melhor que predecessores em 100 tentativas | Implementação não publica completa, otimizado para online (poucos tentativas) | 10^1 a 10^3 |
| 17 | **PassGAN** | brannondorsey/PassGAN | Probabilístico (Neural) | Rede Adversarial Generativa (GAN): gerador G(z) vs discriminador D(x) treinados em corpus de senhas | Python/TF | Aprende padrões latentes, gera senhas inéditas, complementa dicionários | Custo GPU, lento, caixa-preta, sem PII, difícil auditoria | 10^6 a 10^8 |
| 18 | **PassGPT** | javirandor/passgpt | Probabilístico (Neural) | Transformer GPT-2 treinado em corpus de senhas, geração autoregressiva caractere a caractere | Python/PyTorch | ~20% mais senhas inéditas que PassGAN, geração guiada por constraints | Custo GPU alto, treinamento lento, sem PII | 10^6 a 10^8 |
| 19 | **PagPassGPT** | (2024) | Probabilístico (Neural) | Pattern-guided transformer: GPT com padrões estruturais PCFG como guia de geração | Academico | Combina PCFG + GPT, supera PassGAN/PassGPT em benchmarks | Custo computacional extremo, academico | 10^6 a 10^8 |
| 20 | **CeWL** | digininja/CeWL | Extração/Scraping | Web spider + tokenização: extrai palavras únicas de páginas HTML, PDFs, docs e coleta emails | Ruby | Contextual ao alvo, extrai de múltiplos formatos, coleta metadata | Depende do conteúdo web do alvo, sem mutações, sem ranking | 10^2 a 10^5 |
| 21 | **gorilla** | d4rckh/gorilla | Direcionado + Regras | Geração direcionada com regras de mutação (case, leet, append numbers) | Go | Rápido (Go), simples | Funcionalidade limitada comparada a CUPP/bopscrk | 10^2 a 10^4 |
| 22 | **lyricpass** | initstring/lyricpass | Extração | Scraping de letras de músicas de APIs online, tokenização e mutação de frases e palavras-chave | Python | Fonte criativa de tokens pessoais (músicas favoritas) | Depende de API externa, corpus limitado | 10^2 a 10^4 |
| 23 | **elpscrk** | D4Vinci/elpscrk | Direcionado + Estatístico | Wordlist inteligente baseada em profiling, permutações e estatísticas de padrões comuns | Python | Mais inteligente que CUPP, usa estatísticas | Menos popular, documentação limitada | 10^3 a 10^5 |
| 24 | **ttpassgen** | tp7309/TTPassGen | Combinatório + Regras | Enumeração com regras flexíveis: append, prepend, insert com posições e comprimentos variáveis | Python | Regras flexíveis com sintaxe DSL, combinável | Sem priorização, regras manuais | 10^4 a 10^8 |
| 25 | **Weakpass Generator** | weakpass.com | Combinatório + Probabilístico | Geração baseada em wordlists massivas pré-compiladas + regras de alta cobertura | Web | Coleções gigantes (>100GB), regras otimizadas por experiência | Não direcionado, download pesado, sem PII | 10^9 a 10^12 |

---

## 4. Mapeamento de Algoritmos Matemáticos por Ferramenta

### 4.1 Ferramentas Combinatórias Puras

| Ferramenta | Fórmula de Espaço | Técnica |
|-----------|-------------------|---------|
| crunch | \|Σ\|^min + \|Σ\|^(min+1) + ... + \|Σ\|^max | Enumeração exaustiva |
| maskprocessor | Π(i=1..n) \|Σ_i\| (produto dos charsets por posição) | Produto cartesiano posicional |
| kwprocessor | Σ(walks de comprimento k no grafo de adjacência do teclado) | Busca em grafo de adjacência |
| PRINCE | Σ(k=1..N) C(W,k) * k! (combinações de k palavras) | Combinação ordenada de palavras |

### 4.2 Ferramentas de Regras/Mangling

| Ferramenta | Composição de Regras | Técnica |
|-----------|---------------------|---------|
| JtR rules | f_n(...f_2(f_1(w))...) para cada w na wordlist | Composição funcional sequencial |
| Hashcat rules | Mesma composição, com GPU paralelo | Composição funcional + GPU |
| Mentalist | chain(Base -> Node_1 -> Node_2 -> ... -> Node_k) | Cadeia de transformações visuais |
| rsmangler | union(f_1(w), f_2(w), ..., f_m(w)) para cada w | Aplicação independente + união |

### 4.3 Ferramentas Probabilísticas

| Ferramenta | Modelo Matemático | Ordenação |
|-----------|------------------|-----------|
| OMEN | P(pw) = P(c_1\|pos=1) * Π P(c_i\|c_{i-n..i-1}, pos) | Níveis de log-prob discretizados |
| PCFG | P(pw) = P(S->L^a D^b S^c) * P(alpha) * P(digits) * P(symbols) | Prob. decrescente por produção |
| PassGAN | G(z): z~N(0,1) -> candidato, treinado adversarialmente | Sem ordenação inerente |
| PassGPT | P(c_i\|c_1..c_{i-1}): autoregressive transformer | Probabilidade decrescente via sampling |

### 4.4 Ferramentas Direcionadas

| Ferramenta | Campos PII | Técnica de Combinação |
|-----------|-----------|----------------------|
| CUPP | nome, partner, pet, empresa, data, keywords (12 campos) | Concatenação cartesiana: word+num+suffix |
| bopscrk | Similar a CUPP + lyrics + transforms customizáveis | Concatenação + leet/case configurável |
| BEWGor | Extensão de CUPP com mais campos biográficos | Concatenação biográfica estendida |
| TarGuess | nome, nascimento, email, telefone, sister password | 7 modelos probabilísticos condicionais |
| Personal-PCFG | nome, nascimento, email, telefone, conta, doc ID | PCFG com terminais PII |

---

## 5. Posicionamento do CogPIE

### 5.1 Classe Algorítmica: Híbrido Cognitivo

O CogPIE é o único algoritmo na taxonomia que implementa um pipeline de 5 camadas integrando:

1. **Expansão Semântica** (não presente em nenhuma outra ferramenta): gera variantes culturalmente específicas (apelidos brasileiros, transliterações, abreviações) a partir de tokens PII
2. **Transformações Cognitivas** (parcialmente em CUPP/bopscrk como regras fixas): aplica regras derivadas de vieses cognitivos documentados na literatura
3. **Ranking Markov+PCFG** (presente separadamente em OMEN e PCFG Cracker): combina probabilidades de n-gramas posicionais com decomposição estrutural
4. **Scoring de Entropia** (presente no zxcvbn, mas não como componente de geração): estima adivinhabilidade prática
5. **Filtragem por Política** (parcialmente em PCFG Cracker): garante conformidade com políticas do sistema alvo

### 5.2 Diferenciação Chave

| Característica | CUPP | OMEN | PCFG | PassGPT | TarGuess | CogPIE |
|---------------|------|------|------|---------|----------|--------|
| Usa PII | Sim | Nao | Nao | Nao | Sim | Sim |
| Ranking probabilístico | Nao | Sim | Sim | Sim | Sim | Sim |
| Vieses cognitivos modelados | Nao | Nao | Nao | Nao | Parcial | Sim |
| Expansão semântica | Nao | Nao | Nao | Nao | Nao | Sim |
| Adaptação cultural | Nao | Nao | Nao | Nao | Nao | Sim |
| GPU acceleration | N/A | Nao | Nao | Sim | N/A | Sim |
| Filtragem por política | Nao | Nao | Parcial | Nao | Nao | Sim |
| Open source | Sim | Sim | Sim | Sim | Parcial | Sim |

### 5.3 Lacunas que o CogPIE Preenche

1. **CUPP gera sem priorizar:** todas as combinações são tratadas igualmente. CogPIE prioriza pela probabilidade estimada.
2. **OMEN/PCFG não usam PII:** geradores probabilísticos puros ignoram informação pessoal. CogPIE combina ambos.
3. **PassGAN/PassGPT são caixa-preta:** sem auditabilidade ou interpretação dos candidatos. CogPIE é determinístico e auditável.
4. **TarGuess é acadêmico e para online:** otimizado para poucos tentativas, sem implementação publica completa. CogPIE é open source e escala para 100K+ candidatos.
5. **Nenhuma ferramenta modela vieses cognitivos explicitamente:** o CogPIE é o primeiro a formalizar ancoragem, posição serial, desconto hiperbólico e familiaridade como camada computacional.

---

## 6. Posicionamento do WordlistXPL-Forge

O WordlistXPL-Forge integra implementações de múltiplos paradigmas em um único framework:

### 6.1 Motores Implementados

| Motor WLF | Paradigma Equivalente | Ferramentas Externas Equivalentes |
|-----------|----------------------|----------------------------------|
| `cupp_engine.py` | Direcionado | CUPP, BEWGor |
| `bopscrk_engine.py` | Direcionado + Lyrics | bopscrk |
| `markov_engine.py` | Probabilístico (Markov) | OMEN |
| `pcfg_engine.py` | Probabilístico (PCFG) | PCFG Cracker (Weir) |
| `prince_engine.py` | Combinatório (cadeia) | princeprocessor |
| `rsmangler_engine.py` | Regras (mangling) | RSMangler |
| `charset_gen.py` | Combinatório | crunch |
| `kwalk_gen.py` | Combinatório (topológico) | kwprocessor |
| `leet_permuter.py` | Regras (substituição) | Hashcat rules (leet subset) |
| `keyword_mutations.py` | Regras + Direcionado | pydictor |
| `osint_perm.py` | Direcionado (OSINT) | Nenhum equivalente direto |
| `gan_engine.py` | Probabilístico (Neural/GAN) | PassGAN |
| `transformer_engine.py` | Probabilístico (Neural/Transformer) | PassGPT |
| `vae_engine.py` | Probabilístico (Neural/VAE) | VAEPass |
| `diffusion_engine.py` | Probabilístico (Neural/Diffusion) | Nenhum equivalente direto |
| `tcn_engine.py` | Probabilístico (Neural/TCN) | Nenhum equivalente direto |
| `neural_engine.py` | Probabilístico (Neural) | PassGAN (wrapper) |
| `genetic_engine.py` | Metaheurístico | Nenhum equivalente direto |
| `semantic_pcfg.py` | PCFG + Semântico | Personal-PCFG (Li et al.) |
| `domain_pcfg.py` | PCFG + Domínio | Nenhum equivalente direto |
| `phonetic_engine.py` | Fonético | Nenhum equivalente direto |
| `profiler.py` | Wizard interativo de PII | CUPP interactive + extensões |
| `corp_profiler.py` | Direcionado corporativo | Nenhum equivalente direto |
| `br_deep_engine.py` | Cultural brasileiro | Nenhum equivalente direto |
| `web_scraper.py` / `target_spider.py` | Extração/Scraping | CeWL |
| `seclists_trainer.py` | Corpus training | Nenhum equivalente direto |
| `anomaly_scorer.py` | Scoring estatístico | zxcvbn (parcial) |
| `coverage_analyzer.py` | Avaliação de cobertura | Nenhum equivalente direto |
| `bandit_router.py` / `rl_router.py` | Routing adaptativo (RL/Bandit) | Nenhum equivalente direto |
| `map_elites.py` | Metaheurístico (QD) | Nenhum equivalente direto |
| CogPIE (integrado) | Híbrido Cognitivo | CogPIE standalone |

### 6.2 Cobertura Algorítmica Comparativa

| Paradigma | crunch | CUPP | JtR | Hashcat | OMEN | PCFG | PassGAN | WLF |
|-----------|--------|------|-----|---------|------|------|---------|-----|
| Combinatório | **Sim** | Parcial | Parcial | **Sim** | Nao | Nao | Nao | **Sim** |
| Regras/Mangling | Nao | Nao | **Sim** | **Sim** | Nao | Nao | Nao | **Sim** |
| Markov | Nao | Nao | Parcial | Nao | **Sim** | Nao | Nao | **Sim** |
| PCFG | Nao | Nao | Nao | Nao | Nao | **Sim** | Nao | **Sim** |
| Neural (GAN/GPT/VAE) | Nao | Nao | Nao | Nao | Nao | Nao | **Sim** | **Sim** |
| Direcionado (PII) | Nao | **Sim** | Nao | Nao | Nao | Nao | Nao | **Sim** |
| Keyboard Walk | Nao | Nao | Nao | Nao | Nao | Nao | Nao | **Sim** |
| Extração/Scraping | Nao | Nao | Nao | Nao | Nao | Nao | Nao | **Sim** |
| Fonético | Nao | Nao | Nao | Nao | Nao | Nao | Nao | **Sim** |
| Genético/Evolutivo | Nao | Nao | Nao | Nao | Nao | Nao | Nao | **Sim** |
| Cognitivo (CogPIE) | Nao | Nao | Nao | Nao | Nao | Nao | Nao | **Sim** |

**Conclusão:** WordlistXPL-Forge é a única ferramenta que implementa todos os 11 paradigmas algorítmicos identificados, integrando-os em um pipeline unificado com profiling interativo, routing adaptativo e benchmark automatizado.

---

## 7. Referências

1. Weir, M., Aggarwal, S., de Medeiros, B., Glodek, B. (2009). "Password Cracking Using Probabilistic Context-Free Grammars." IEEE S&P, pp. 391-405.
2. Durmuth, M., et al. (2015). "OMEN: Faster Password Guessing Using an Ordered Markov Enumerator." ESSoS 2015.
3. Ma, J., et al. (2014). "A Study of Probabilistic Password Models." IEEE S&P.
4. Hitaj, B., et al. (2019). "PassGAN: A Deep Learning Approach for Password Guessing."
5. Rando, J., et al. (2023). "PassGPT: Password Modeling and (Guided) Generation with Large Language Models."
6. Wang, D., et al. (2016). "Targeted Online Password Guessing: An Underestimated Threat." ACM CCS, pp. 1242-1254.
7. Li, Y., Wang, H., Sun, K. (2017). "Personal Information in Passwords and Its Security Implications." IEEE TIFS 12(10).
8. Mebus, M. (2010). "CUPP: Common User Passwords Profiler."
9. Narayanan, A., Shmatikov, V. (2005). "Fast Dictionary Attacks on Passwords Using Time-Space Tradeoff."
10. Wheeler, D. (2016). "zxcvbn: Low-Budget Password Strength Estimation."
11. PagPassGPT (2024). "Pattern Guided Password Guessing via Generative Pretrained Transformer." arXiv:2404.04886.
12. SOPG (2024). "Search-based Ordered Password Generation of Autoregressive Neural Networks." arXiv:2403.09954.
