# CogPIE GPU Comparison Benchmark

Corpus: ./corpus/rockyou_full/processed_corpus.txt
Train: 1,000,000 | Test: 500 | GPU: cuda

| Algorithm | Coverage | MRR | hit@10 | hit@100 | hit@1000 | hit@10000 | ms/target |
|---|---|---|---|---|---|---|---|
| CogPIE | 48.0% | 0.0011 | 0.00% | 1.40% | 28.80% | 48.00% | 637.4 |
| Markov-3 | 3.2% | 0.0008 | 0.20% | 1.80% | 2.60% | 3.20% | 856.9 |
| Frequency | 0.0% | 0.0000 | 0.00% | 0.00% | 0.00% | 0.00% | 0.1 |
| Levenshtein | 0.0% | 0.0000 | 0.00% | 0.00% | 0.00% | 0.00% | 182.1 |
| CUPP-style | 46.0% | 0.0273 | 6.20% | 43.80% | 46.00% | 46.00% | 0.0 |
| Random | 0.0% | 0.0000 | 0.00% | 0.00% | 0.00% | 0.00% | 1.4 |
