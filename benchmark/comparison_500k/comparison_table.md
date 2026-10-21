# CogPIE Comparison Benchmark

Corpus: ./corpus/rockyou/processed_corpus.txt
Train: 499,564 | Test: 200

| Algorithm | hit@10 | hit@100 | hit@1000 | hit@10000 | Avg ms/target |
|---|---|---|---|---|---|
| CogPIE | 1.00% | 5.00% | 67.50% | 69.00% | 241.3 |
| Markov-3 | 2.50% | 9.50% | 28.50% | 28.50% | 991.3 |
| Frequency | 0.00% | 0.00% | 0.00% | 0.00% | 0.0 |
| Levenshtein | 0.00% | 0.00% | 0.00% | 0.00% | 315.5 |
| CUPP-style | 7.50% | 42.00% | 43.50% | 43.50% | 0.0 |
| Random | 0.00% | 0.00% | 0.00% | 0.00% | 1.2 |
