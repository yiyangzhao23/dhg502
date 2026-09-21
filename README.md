# 明史 Text Analysis — DHG502 workflow check

**Name:** Ci Ci · **Course:** DHG502

**What I did:** I used opencode (running the **GLM-5.3-Flash** model) to write
and run a Python script that downloads the plain-text 明史 from the Kanripo
project and reports its most frequent characters, word-like bigrams, the
treacherous officials named in the 奸臣傳, official titles, and how key terms are
distributed across the text, and I published the results as a web page.

## Citation

> 張廷玉 et al. 《明史》 (*History of the Ming*). 1739. Plain-text transcription,
> Kanripo Digital Archive, KR2a0038.
> <https://github.com/kanripo/KR2a0038> (accessed 21 September 2026).

## The source

The **明史** (*Mingshi*, History of the Ming), the official history of the Ming
dynasty (1368–1644) compiled under the Qing and finished in 1739. The plain text
used here is the **Kanripo** transcription `KR2a0038`
(<https://github.com/kanripo/KR2a0038>), 548 UTF-8 text files, about 3.15 million
CJK characters.

The source is downloaded by the script and kept in the git-ignored `data/`
directory; only the derived results are committed.

## Analyses

| # | Analysis | What it shows |
|---|---|---|
| 1 | Most frequent characters | The basic texture of the language (之, 十, 以, 年 …) |
| 2 | Most frequent bigrams | Word-like pairs, a stand-in for words without a tokeniser (御史, 尚書, 洪武 …) |
| 3 | Treacherous officials | How often each 奸臣 named in the 卷三百八 奸臣傳 is mentioned |
| 4 | Other named people | Emperors and famous figures for comparison |
| 5 | Official titles | 尚書, 侍郎, 巡撫, 太監 … |
| 6 | Distribution across the text | Each key term counted in ten equal blocks in reading order |
| 7 | Distribution by section | Counts in 本紀 / 志 / 表 / 列傳 |

## Files

- `analyze_mingshi.py` — the analysis script (standard library only)
- `mingshi-results.txt` — the plain-text report
- `mingshi-results.html` — the results as a web page
- `index.html` — the same page, so GitHub Pages can serve it at the repository root
- `opencode.json` — sets GLM-5.3-Flash as the model (contains no secret)

## Run it

```bash
python3 analyze_mingshi.py            # downloads data/ on first run
python3 analyze_mingshi.py --no-download   # reuse an existing data/ directory
```

## Model and API key

The model is called through opencode. Register at <https://keyreg.qhchina.org>
with the class code and your email to get an OpenRouter API key, then store it
**outside the repository**:

```bash
opencode auth login        # choose OpenRouter, paste the key
```

In a Codespace, set it as an environment variable instead:

```bash
export OPENROUTER_API_KEY=...   # or add it as a Codespaces secret
```

The key is never written to a file in this repository. `.gitignore` also blocks
`.env`, `*.key`, and `secrets*`.

## Prompt used

> Here is a plain-text historical source, the 明史 (Mingshi) from the Kanripo
> project. Suggest several ways to analyse it, then write a Python script that
> computes the most frequent characters and bigrams, counts the treacherous
> officials 奸臣 named in the Ming History's 奸臣傳, and shows how a few key
> people and official titles are distributed across the text. Write the results
> as both a .txt file and a small .html page.

## Limits and judgment

- **Bigrams are not words.** Written Chinese has no spaces, so a real tokeniser
  is needed before "words" can be counted exactly. Bigrams are a transparent
  approximation.
- **Variant glyphs.** The Four Treasuries text behind Kanripo writes 内 far more
  often than standard 內; without merging variants, 內閣 looks almost absent
  (4 hits instead of 302). The script folds a list of common variants — useful
  but not exhaustive.
- **Substring counting.** Each term is an exact substring, so a name inside a
  longer name is also counted. Read the numbers as indications, not a census.
