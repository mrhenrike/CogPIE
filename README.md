# CogPIE: Cognitive Pattern Inference Engine

A hybrid multi-layer password generation engine that exploits cognitive biases in human password creation. CogPIE combines semantic expansion, cognitive transforms, Markov+PCFG hybrid ranking, entropy scoring, and policy filtering to predict PII-derived passwords with high accuracy.

## Architecture

CogPIE implements a 5-layer pipeline:

1. **Semantic Expander**: Generates base candidates from profile data (names, dates, keywords, pets, companies)
2. **Cognitive Transforms**: Applies psychologically-motivated transformations (leetspeak, case variations, suffix patterns, anchoring bias)
3. **Markov+PCFG Hybrid Ranker**: Scores candidates using a trained character-level Markov model combined with PCFG structural templates
4. **Entropy Scorer**: Filters and re-ranks based on entropy thresholds
5. **Policy Filter**: Applies password policy constraints (length, complexity requirements)

## Key Results

| Corpus | Training Size | Coverage (hit@10K) | hit@1K | MRR | Median Rank |
|--------|--------------|-------------------|--------|------|-------------|
| RockYou (standalone) | 1M | 75.95% | 75.95% | 0.137 | 35 |
| Brazilian (wlist_brasil + melissa) | 13.1M | 99.50% | 66.45% | 0.003 | 618 |
| Medium (5 sources) | 41M | 98.70% | 92.75% | 0.030 | 179 |
| RockYou (comparative) | 1M | 50.15% | 30.20% | 0.001 | N/A |

### Comparative Analysis (2,000 targets, 1M training)

| Algorithm | hit@100 | hit@1K | Coverage | MRR |
|-----------|---------|--------|----------|------|
| **CogPIE** | 1.70% | **30.20%** | **50.15%** | 0.0013 |
| CUPP-style | **45.60%** | 47.55% | 47.55% | **0.0308** |
| Markov-3 | 1.85% | 4.20% | 4.80% | 0.0015 |

CogPIE surpasses CUPP at budget >= 1,000 guesses. Markov collapses catastrophically at scale (28.5% -> 4.8%).

## GPU Acceleration

CUDA backend with 20x speedup on RTX 4060 (1M corpus):
- CPU: 15.12s/profile
- GPU: 0.75s/profile (174 MB VRAM)

## Project Structure

```
cogpie/              # Core engine modules (10 .py files)
tests/               # Unit tests and benchmarks (28+ tests)
tools/               # Benchmark and evaluation scripts (8 tools)
benchmark/           # All benchmark results (JSON + tables)
docs/research/       # Academic paper (EN + PT-BR, HTML + Markdown)
```

## Usage

```python
from cogpie.engine import CogPIEEngine

engine = CogPIEEngine(use_gpu=True)

# Train on a password corpus
with open("corpus.txt") as f:
    for line in f:
        engine.ranker.train(line.strip())

# Generate candidates for a profile
profile = {
    "names": ["joao"],
    "dates": ["1990", "0315"],
    "keywords": ["flamengo"],
    "pets": ["rex"],
    "companies": ["acme"],
    "phones": [],
    "emails": ["joao@example.com"],
    "old_passwords": ["joao123"],
    "numbers": ["42"],
}
candidates = engine.generate(profile, max_candidates=10000)
for password, score in candidates[:10]:
    print(f"{password}: {score:.4f}")
```

## Research Paper

The full academic paper is available in `docs/research/cogpie-paper/`:
- **English**: `cogpie-paper.md` / `cogpie-paper.html`
- **Portuguese (BR)**: `cogpie-paper-pt-br.md` / `cogpie-paper-pt-br.html`

42 references, MITRE ATT&CK/CWE/OWASP/NIST D3FEND mappings, 55 unit tests as experimental evidence.

## Requirements

- Python >= 3.10
- PyTorch >= 2.0 (optional, for GPU acceleration)
- CUDA-capable GPU (optional, falls back to CPU)

## Author

Andre Henrique de Oliveira (@mrhenrike) / Uniao Geek

## License

Private research. All rights reserved.
