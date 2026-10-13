# The "Company" of 錢 in the 舊唐書·食貨志

Assignment 1 (DHG 502). A collocation study of how the *Jiu Tangshu*'s
"Treatise on Food and Money" represents money.

## Research question

How do the words that keep company with **錢** ("coin", "money") frame it in the
舊唐書·食貨志 — as a ruler's instrument to be controlled, or as the site of
illicit profit and disorder? And does that framing change when "near" is defined
as a 5-word window, a 10-word window, or the whole sentence?

## Source

- **Text.** *舊唐書* 卷四十八（志第二十八·食貨上）and 卷四十九（志第二十九·食貨下),
  the "Treatise on Food and Money" (*Shihuo zhi*).
- **Where I got it.** Downloaded from Chinese Wikisource:
  - https://zh.wikisource.org/wiki/舊唐書/卷48
  - https://zh.wikisource.org/wiki/舊唐書/卷49
- **Citation.** 劉昫 et al., comps., *舊唐書*, completed 945 CE. Standard
  scholarly edition: 中華書局, Beijing, 1975. Digital text: Chinese Wikisource.
- **Rights.** The underlying work is in the **public domain** (945). The
  Wikisource transcription and punctuation are offered under **CC BY-SA 4.0**
  (and GFDL); attribute Wikisource if you redistribute it. The pages carry
  `{{textquality|25%}}`, i.e. **unproofread** — cross-check readings against
  ctext.org or a 中華書局/百衲本 edition before quoting.
- **Size.** 22,297 characters excluding whitespace (卷48 = 13,196; 卷49 = 9,101);
  871 sentences, 10,403 tokens after segmentation.
- **Which part, and how selected.** I used the **two complete juan** of the
  食貨志 (卷48 + 卷49). There was no sampling: both juan were downloaded whole and
  cleaned to traditional characters, UTF-8. The treatise is the one place where
  the Tang state discusses money, taxation, and monopoly together.

`data/舊唐書食貨志.txt` is that plain-text source. The two `.wikitext` files are
the unmodified downloads, kept for provenance.

**Why the compilation matters.** The *Jiu Tangshu* was compiled in 945 by
stitching Tang *veritable records* and *national history* together; much of what
it says about money comes in the **voice of officials' memorials**, not the
compilers' prose. The collocates therefore reflect Tang policy discourse.

## How the text was prepared

1. **Download.** 卷48 and 卷49 were taken from Chinese Wikisource; the raw
   `.wikitext` files are kept in `data/` for provenance.
2. **Clean.** They were combined into one traditional-character UTF-8 plain-text
   file, `data/舊唐書食貨志.txt`.
3. **Convert.** The whole text was converted traditional → simplified with
   `opencc` (`t2s`), because jieba segments simplified text more reliably. The
   target is therefore written **钱** (not 錢) before segmentation.
4. **User dictionary.** `userdict.txt` lists the terms the question depends on so
   jieba keeps them whole: 開元通寶、惡錢、鑄錢、行用、見錢、鉛錫、兩稅 (plus the
   persons named in the treatise).
5. **Stopwords.** Classical-Chinese stopwords are removed with
   `load_stopwords("zh_cl_sim")` from `qhchina`.
6. **Sentences.** The text is split on 。！？； and sentences with fewer than five
   words are dropped; each remaining sentence is tagged with its juan (48 or 49).
7. **Eye check.** `segment.py` prints 20 random sentences containing the target so
   the segmentation can be inspected by hand.

**Residual problems.** Segmentation is not perfect: some personal names and rare
compounds still split (for example 第五琦, 乾封泉寶). I kept `min_word_length=1`
so single-character words are not lost, and I report the caliber of the target
below.

## Repository layout

```text
jiutangshu_collocations/
├── README.md
├── AI-USE.md
├── requirements.txt
├── report.md                     the report (same text as the PDF)
├── userdict.txt                  jieba user dictionary (simplified)
├── data/                         sources, plain-text UTF-8
│   ├── 舊唐書食貨志.txt           卷48–49, cleaned to traditional UTF-8
│   ├── 舊唐書食貨志.卷48.wikitext  unmodified download (provenance)
│   └── 舊唐書食貨志.卷49.wikitext
├── code/
│   ├── segment.py                source → output/sentences.txt (+ chapter index)
│   ├── collocates.py             three runs → output/collocates_*.csv
│   ├── make_report.py            output/results.html (dropdown + sortable)
│   └── concordance.py            output/kwic.html (back to the passages)
└── output/
    ├── sentences.txt             generated, one sentence per line
    ├── sentence_index.csv        generated, juan number/title per line
    ├── collocates_window5.csv    collocation results, one file per run
    ├── collocates_window10.csv
    ├── collocates_sentence.csv
    ├── results.html              compare the three runs
    └── kwic.html                 concordance lines for the collocates
```

## Setup

```bash
python3 -m pip install -r requirements.txt
```

(installs `jieba`, `opencc-python-reimplemented`, `qhchina`)

## Run

The source is already at `data/舊唐書食貨志.txt`. Run in order:

```bash
python3 code/segment.py       # convert to simplified, segment, index the juan
python3 code/collocates.py    # window5, window10, sentence -> output/*.csv
python3 code/make_report.py   # output/results.html
python3 code/concordance.py   # output/kwic.html
```

`segment.py` also prints 20 random sentences containing the target, so you can
check segmentation by eye.

## Settings, and why

- **Target:** `钱` (the simplified form; the source is converted from traditional
  before segmentation).
- **Three definitions of "near":** window ±5, window ±10, sentence. A single
  window is not enough — the definition changes what you find.
- **`min_word_length=1`:** in classical Chinese many content words are single
  characters (鑄、新、銅、輕); a minimum of 2 would drop them.
- **`min_obs_local=3`:** a collocation must co-occur with the target at least
  three times to count.
- **`max_adjusted_p=0.05` with `fdr_bh`:** several hundred candidate collocates
  are tested at once, so the p-values are corrected for multiple testing.
- **Measures:** `log_likelihood` (significance — is the association real?) and
  `logDice` (strength — how tightly are the two words bound?).

## The statistics in brief (for a historian)

**Contingency table.** Every item (here, a window around the target, or a
sentence) is sorted by two questions: does the target appear, and does the
collocate appear? That gives four cells; cell *a* is the number of times the two
appear together (the observed frequency, `obs_local`). The point is that the
table also records the times they appear separately and never meet — which is
what separates a genuine collocation from two common words that keep bumping
into each other.

**p-value.** Assuming the two words are unrelated, the p-value is the chance of
seeing this table, or one even more extreme. A small p means the co-occurrence is
hard to explain by chance. But a p-value measures how *sure* we are, not how
*strong* the link is, and it does not show causation. In a larger corpus many
pairs become significant, so significance alone cannot rank collocates.

**Significance vs. strength.** `log_likelihood` is a significance measure (is it
real?); `logDice` is a strength measure (how tight?). Two coins make the
difference concrete: a coin flipped 10 times with 9 heads is strongly biased but
rests on little evidence; one flipped 100,000 times with 51,000 heads is weakly
biased but rests on overwhelming evidence. In this project, `新` has the highest
`log_likelihood` in the ±5 run but a middling `log_dice`, while `并` has a high
`log_dice` and a low `log_likelihood` — a common function word: statistically
present, historically thin.

## Results at a glance

| run | rows | top by logDice |
| --- | --- | --- |
| window5 | 10 | 新, 铸, 并, 乾元, 旧, 恶钱, 开元通宝, 时价, 好, 贱 |
| window10 | 14 | 铸, 并, 新, 旧, 乾元, 恶钱, 十文, 轻, 一当, … |
| sentence | 14 | 铸, 并, 新, 旧, 乾元, 六年, 铜, 十文, 新钱, 轻, 一当, 重, 开元通宝, 时价 |

The collocates fall into three groups: **official minting** (铸、新、开元通宝、
行用), **disorder / depreciation** (旧、恶钱、铜、铅锡), and the **valuation
debate** (轻、重、一当、时价).

## Notes on segmentation

- 錢 is a bound morpheme: it also sits inside 鑄錢、惡錢、見錢、兩稅錢. Only the
  **standalone** token is counted (90 in this corpus); `錢` occurs 275 times in
  total, 231 of them in juan 48.
- Edit `userdict.txt` (simplified) if names or terms split.

## Regenerating

`output/sentences.txt`, `sentence_index.csv`, the CSVs, and the HTML pages are
all regenerable from `data/` with the four scripts; the scripts are the record.
