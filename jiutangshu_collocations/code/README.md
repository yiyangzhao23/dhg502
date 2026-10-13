# Code

Four scripts; run them in this order from the repository root.

| script | what it does |
| --- | --- |
| `segment.py` | reads `data/舊唐書食貨志.txt`, converts traditional → simplified with opencc, segments with jieba (using `userdict.txt`), splits into sentences, writes `output/sentences.txt` and `output/sentence_index.csv`, and prints 20 random sentences for eyeballing. |
| `collocates.py` | reads `output/sentences.txt`, finds collocates of `钱` with `qhchina.analytics.find_collocates` under three definitions of "near" (window ±5, window ±10, sentence), and writes one CSV per run to `output/`. |
| `make_report.py` | reads the CSVs and builds `output/results.html`, a page with a dropdown to switch runs and sortable columns. |
| `concordance.py` | reads `output/sentences.txt` and builds `output/kwic.html`, the concordance lines for the collocates discussed. |

Settings (target, windows, filters, measures) are documented in the top-level
`README.md` and in each script.
