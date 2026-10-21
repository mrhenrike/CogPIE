# CogPIE GPU Comparison Benchmark

Corpus: ./corpus/rockyou_full/processed_corpus.txt
Train: 1,000,000 | Test: 2,000 | GPU: cuda

| Algorithm | Coverage | MRR | hit@10 | hit@100 | hit@1000 | hit@10000 | ms/target |
|---|---|---|---|---|---|---|---|
| CogPIE | 50.1% | 0.0013 | 0.05% | 1.70% | 30.20% | 50.15% | 621.1 |
| Markov-3 | 4.8% | 0.0015 | 0.25% | 1.85% | 4.20% | 4.80% | 830.4 |
| Frequency | 0.0% | 0.0000 | 0.00% | 0.00% | 0.00% | 0.00% | 0.1 |
| Levenshtein | 0.0% | 0.0000 | 0.00% | 0.00% | 0.00% | 0.00% | 179.2 |
| CUPP-style | 47.5% | 0.0308 | 5.90% | 45.60% | 47.55% | 47.55% | 0.0 |
| Random | 0.0% | 0.0000 | 0.00% | 0.00% | 0.00% | 0.00% | 1.4 |
