# AI-USE

## Tools and models used

- **opencode** (command-line coding assistant), model **deepseek-v4.1-flash**
  (OpenCode Go). Used for code and troubleshooting.

## Tasks for which AI was used

1. **Code.** Helping to write and debug the four Python scripts that prepare the
   text and run the analysis: `code/segment.py`, `code/collocates.py`,
   `code/make_report.py`, `code/concordance.py`. These follow the Week 4 workflow
   (`find_collocates`, `load_stopwords`, `kwic` from `qhchina`).
2. **Troubleshooting.** Fixing path and environment problems (opencc
   traditional→simplified conversion, the jieba user dictionary, reading
   `sentences.txt`).
3. **Language and formatting.** Editing and translating report sentences between
   Chinese and English, and typesetting the report as a PDF.
4. **Background.** Locating a scholarly work (Tan Mei Ah, *Journal of Chinese
   Studies* 64 [2017]) to cite.

The historical question, the choice of target word, the reading of the
collocations, and the final wording are the student's own; every claim was
checked against the source.

## Representative prompts and session excerpts

- *"Write a Python script `segment.py` that loads the source text, converts it to
  simplified Chinese with opencc, uses a jieba user dictionary, splits it into
  sentences, keeps sentences with at least 5 words, and saves `sentences.txt`
  plus a chapter index."*
- *"Using `sentences.txt`, write `collocates.py` that finds collocates of 钱 with
  `find_collocates` from `qhchina.analytics`, removes classical-Chinese
  stopwords, sets `min_word_length=1`, `min_obs_local=3`, adds
  `log_likelihood` and `logDice`, corrects with `fdr_bh`, and runs window ±5,
  window ±10, and sentence, saving one CSV per run."*
- *"Build one HTML page (`results.html`) that reads the CSVs and lets me switch
  between runs and sort by any column."*
- *"Build `kwic.html` showing passages where 钱 and each collocate occur
  together."*
- Editing prompts: *"make this sentence simpler and more direct"*, *"keep the
  Chinese quotations untranslated"*.

## Important changes I made to the AI output

- Set `min_word_length` to **1** (a minimum of 2 would drop single-character
  classical words such as 鑄、新、銅、輕).
- Added the money terms to `userdict.txt` (開元通寶、惡錢、鑄錢、行用、見錢、鉛錫、
  兩稅) so jieba would not split them.
- Counted **only the standalone 钱 token** (90), not the 钱 inside compounds.
- Ran the analysis **three times** and based the interpretation on comparing them.

## How I checked the output

- Re-ran the whole pipeline (`segment.py → collocates.py → make_report.py →
  concordance.py`) and confirmed it reproduces the CSVs and HTML pages.
- Eyeballed the 20 random segmented sentences printed by `segment.py`.
- Verified the counts (90 standalone tokens; 275 occurrences of `錢`; 231 in juan
  48 vs 44 in juan 49).
- Cross-checked every Chinese quotation against 舊唐書 卷48 and its rights and
  provenance on Wikisource.
- Compared the significance ranking with the strength ranking in
  `output/results.html`.
