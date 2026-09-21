#!/usr/bin/env python3
"""Analyse the Mingshi 明史 (History of the Ming).

This script downloads the plain-text 明史 from the Kanripo project
(https://github.com/kanripo/KR2a0038), cleans the Kanripo markup, and writes
two deliverables:

  * mingshi-results.txt   a plain-text report
  * mingshi-results.html  the same results as a small web page
    (a copy is also written to index.html for GitHub Pages)

Analyses
--------
1. Top single characters.
2. Top bigrams (two adjacent characters) as a dependency-free stand-in for
   "words": classical Chinese is written without spaces, so a real word
   tokeniser is needed before "words" can be counted exactly.
3. Targeted counts for official titles and for the treacherous officials
   奸臣 named in the 明史 卷三百八 奸臣傳.
4. Distribution: each key term is counted in ten roughly equal blocks of the
   text in reading order, and by the four structural sections
   本紀 (annals), 志 (treatises), 表 (tables), 列傳 (biographies).

Only the Python standard library is used, so it runs anywhere.
"""

import argparse
import collections
import glob
import html
import json
import os
import re
import sys
import unicodedata
import urllib.request
from concurrent.futures import ThreadPoolExecutor

KANRIPO_REPO = "kanripo/KR2a0038"
RAW_URL = "https://raw.githubusercontent.com/{repo}/master/{name}"
API_URL = "https://api.github.com/repos/{repo}/contents/"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Characters used to define "text": CJK Unified Ideographs, Extension A and B.
CJK_RE = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\U00020000-\U0002FFFF]+")

# The Kanripo transcription follows a Four Treasuries (四庫全書) edition and
# therefore mixes variant glyphs: e.g. it writes 内 (U+5185) far more often than
# the standard 內 (U+5167). Without merging them, a search for 內閣 finds almost
# nothing. Each variant below is mapped to the standard traditional form.
VARIANT_MAP = {
    "内": "內", "温": "溫", "敎": "教", "户": "戶", "髙": "高", "冦": "寇",
    "姦": "奸", "爲": "為", "畧": "略", "峯": "峰", "羣": "群", "强": "強",
    "眞": "真", "毎": "每", "舎": "舍", "収": "收", "曽": "曾", "説": "說",
    "経": "經", "絶": "絕", "净": "淨", "减": "減", "凉": "涼", "况": "況",
    "凑": "湊", "禄": "祿", "顕": "顯", "産": "產", "顔": "顏", "賔": "賓",
    "寳": "寶", "嵗": "歲", "卽": "即", "旣": "既", "槪": "概", "啓": "啟",
    "効": "效", "敍": "敘", "潜": "潛", "却": "卻",
}
_VARIANT_TABLE = str.maketrans(VARIANT_MAP)

# Officials listed in the 明史 卷三百八 奸臣傳 (列傳第一百九十六).
JIANCHEN = [
    "胡惟庸", "陳寧", "陳瑛", "馬麟", "嚴嵩", "趙文華",
    "鄢懋卿", "周延儒", "溫體仁", "馬士英", "阮大鋮",
]

# Other frequently named people, for comparison.
PEOPLE = [
    "太祖", "成祖", "張居正", "魏忠賢", "王守仁", "于謙",
    "海瑞", "劉基", "李自成", "張獻忠",
]

OFFICES = [
    "尚書", "侍郎", "大學士", "都御史", "御史", "給事中", "總兵",
    "都督", "巡撫", "巡按", "布政使", "按察使", "知府", "知縣",
    "太監", "內閣", "首輔", "將軍",
]

# Terms whose distribution across the text we track.
DISTRIBUTION_TERMS = ["太祖", "成祖", "嚴嵩", "魏忠賢", "張居正", "太監", "尚書", "巡撫"]

SECTIONS = ["本紀", "志", "表", "列傳"]


def download(data_dir=DATA_DIR):
    """Fetch the Kanripo text files into ``data_dir`` (skipping files already there)."""
    os.makedirs(data_dir, exist_ok=True)
    with urllib.request.urlopen(API_URL.format(repo=KANRIPO_REPO), timeout=60) as resp:
        listing = json.load(resp)
    names = sorted(item["name"] for item in listing if item["name"].endswith(".txt"))
    if not names:
        raise RuntimeError("Kanripo listing returned no .txt files")

    def fetch(name):
        dest = os.path.join(data_dir, name)
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            return
        with urllib.request.urlopen(RAW_URL.format(repo=KANRIPO_REPO, name=name), timeout=60) as r:
            data = r.read()
        with open(dest, "wb") as fh:
            fh.write(data)

    with ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(fetch, names))
    return names


def clean(raw):
    """Strip Kanripo markup and normalise character variants.

    Removes metadata comments, <pb:...> tags, paragraph marks and indentation.
    NFKC folds CJK compatibility ideographs to their unified forms; VARIANT_MAP
    folds the remaining Four Treasuries variant glyphs to standard forms.
    """
    lines = [line for line in raw.splitlines() if not line.startswith("#")]
    text = "\n".join(lines)
    text = re.sub(r"<[^>]+>", "", text)      # page-break tags such as <pb:KR2a0038_...>
    text = text.replace("\u00b6", "")         # Kanripo line-break marker ¶
    text = text.replace("\u3000", "")         # ideographic space used for indentation
    text = unicodedata.normalize("NFKC", text)
    return text.translate(_VARIANT_TABLE)


def cjk_runs(text):
    """Return the runs of consecutive CJK characters in ``text``."""
    return CJK_RE.findall(text)


def classify_section(text):
    """Classify a juan file as 本紀 / 志 / 表 / 列傳 using its opening heading."""
    head = text[:400]
    best = None
    for section in SECTIONS:
        idx = head.find(section)
        if idx != -1 and (best is None or idx < best[1]):
            best = (section, idx)
    return best[0] if best else "其他"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=DATA_DIR)
    parser.add_argument("--no-download", action="store_true",
                        help="fail instead of downloading missing source files")
    args = parser.parse_args()

    have = glob.glob(os.path.join(args.data_dir, "KR2a0038_*.txt"))
    if not have and not args.no_download:
        print("Downloading 明史 from Kanripo ...", file=sys.stderr)
        download(args.data_dir)
        have = glob.glob(os.path.join(args.data_dir, "KR2a0038_*.txt"))
    if not have:
        raise SystemExit("No source files found; run without --no-download first.")

    files = sorted(glob.glob(os.path.join(args.data_dir, "KR2a0038_*.txt")))
    docs = []  # (name, cleaned_text, section)
    char_counts = collections.Counter()
    bigram_counts = collections.Counter()
    total_len = 0

    for path in files:
        with open(path, encoding="utf-8") as fh:
            text = clean(fh.read())
        section = classify_section(text)
        docs.append((os.path.basename(path), text, section))
        total_len += len(text)
        for run in cjk_runs(text):
            char_counts.update(run)
            for i in range(len(run) - 1):
                bigram_counts[run[i:i + 2]] += 1

    # ---- distribution across ten equal-length blocks -----------------------
    term_blocks = {term: [0] * 10 for term in DISTRIBUTION_TERMS}
    offset = 0
    for _, text, _ in docs:
        for term in DISTRIBUTION_TERMS:
            for match in re.finditer(re.escape(term), text):
                pos = offset + match.start()
                block = min(9, int(pos * 10 / max(total_len, 1)))
                term_blocks[term][block] += 1
        offset += len(text)

    # ---- per-section counts ------------------------------------------------
    section_chars = collections.Counter()
    section_terms = {term: collections.Counter() for term in DISTRIBUTION_TERMS}
    for _, text, section in docs:
        section_chars[section] += len(text)
        for term in DISTRIBUTION_TERMS:
            section_terms[term][section] += text.count(term)

    def mention_counts(terms):
        return [(t, sum(doc_text.count(t) for _, doc_text, _ in docs)) for t in terms]

    jianchen = mention_counts(JIANCHEN)
    people = mention_counts(PEOPLE)
    offices = mention_counts(OFFICES)

    top_chars = char_counts.most_common(30)
    top_bigrams = bigram_counts.most_common(30)

    context = {
        "total_chars": total_len,
        "num_files": len(files),
        "top_chars": top_chars,
        "top_bigrams": top_bigrams,
        "jianchen": jianchen,
        "people": people,
        "offices": offices,
        "term_blocks": term_blocks,
        "section_chars": section_chars,
        "section_terms": section_terms,
        "distribution_terms": DISTRIBUTION_TERMS,
        "sections": SECTIONS,
    }

    txt = render_txt(context)
    with open("mingshi-results.txt", "w", encoding="utf-8") as fh:
        fh.write(txt)

    page = render_html(context)
    for name in ("mingshi-results.html", "index.html"):
        with open(name, "w", encoding="utf-8") as fh:
            fh.write(page)

    print(f"Read {len(files)} files, {total_len:,} characters.")
    print("Wrote mingshi-results.txt, mingshi-results.html, index.html")


def render_txt(c):
    out = []
    out.append("明史 (History of the Ming) — text analysis")
    out.append("=" * 48)
    out.append(f"Source: Kanripo KR2a0038 (transcription of the Ming History, 332 juan)")
    out.append(f"Files analysed: {c['num_files']}   Characters: {c['total_chars']:,}")
    out.append("")
    out.append("Method")
    out.append("-" * 48)
    out.append("Kanripo markup (# comments, <pb:...> page tags, paragraph marks and")
    out.append("indentation) was removed; punctuation was dropped, leaving CJK")
    out.append("characters only. Formal and variant glyphs were merged (e.g. the")
    out.append("Four Treasuries text writes 内 far more often than standard 內, so")
    out.append("both are counted as 內); this map is useful but not exhaustive.")
    out.append("\"Bigrams\" are pairs of adjacent characters and stand in for words,")
    out.append("since written Chinese has no spaces.")
    out.append("")

    def table(title, rows, total=None):
        out.append(title)
        out.append("-" * 48)
        width = max((len(k) for k, _ in rows), default=1)
        for key, n in rows:
            if total:
                pct = f"  ({n / total * 100:5.2f}%)"
            else:
                pct = ""
            out.append(f"{key:<{width}}  {n:>8,}{pct}")
        out.append("")

    table("1. Most frequent characters", c["top_chars"], c["total_chars"])
    table("2. Most frequent bigrams (word-like pairs)", c["top_bigrams"])
    table("3. Treacherous officials named in the 奸臣傳 (卷三百八)", c["jianchen"])
    table("4. Other frequently named people", c["people"])
    table("5. Official titles", c["offices"])

    out.append("6. Distribution across the text (ten equal blocks, in reading order)")
    out.append("-" * 48)
    header = "term      " + "".join(f"{i + 1:>7}" for i in range(10))
    out.append(header)
    for term in c["distribution_terms"]:
        row = f"{term:<10}" + "".join(f"{n:>7}" for n in c["term_blocks"][term])
        out.append(row)
    out.append("")
    out.append("7. Distribution by section")
    out.append("-" * 48)
    total = c["total_chars"]
    for section in c["sections"]:
        n = c["section_chars"].get(section, 0)
        out.append(f"{section:<6} {n:>10,} chars  ({n / total * 100:5.2f}%)")
    out.append("")
    out.append("term      " + "".join(f"{s:>8}" for s in c["sections"]))
    for term in c["distribution_terms"]:
        row = f"{term:<10}" + "".join(f"{c['section_terms'][term].get(s, 0):>8}" for s in c["sections"])
        out.append(row)
    out.append("")
    out.append("Note: counts are exact substring counts, so a name inside a longer")
    out.append("name is also counted. Read them as indications, not as a census.")
    return "\n".join(out) + "\n"


def _bar(value, maximum):
    width = int(value / maximum * 100) if maximum else 0
    return f'<span class="bar" style="width:{width}%"></span>'


def _rows(rows, total=None):
    if not rows:
        return "<tr><td colspan=3>(none)</td></tr>"
    maximum = max(n for _, n in rows)
    cells = []
    for key, n in rows:
        pct = f"<span class='pct'>{n / total * 100:.2f}%</span>" if total else ""
        cells.append(
            f"<tr><td class='k'>{html.escape(key)}</td>"
            f"<td class='n'>{n:,}{pct}</td>"
            f"<td class='c'>{_bar(n, maximum)}</td></tr>"
        )
    return "".join(cells)


def render_html(c):
    total = c["total_chars"]
    blocks_head = "".join(f"<th>{i + 1}</th>" for i in range(10))
    block_rows = ""
    for term in c["distribution_terms"]:
        vals = c["term_blocks"][term]
        mx = max(vals) or 1
        tds = "".join(
            f"<td style='background:rgba(180,30,30,{v / mx * 0.85:.2f})'>{v or ''}</td>"
            for v in vals
        )
        block_rows += f"<tr><th class='k'>{html.escape(term)}</th>{tds}</tr>"

    section_rows = ""
    for section in c["sections"]:
        n = c["section_chars"].get(section, 0)
        section_rows += (
            f"<tr><td class='k'>{html.escape(section)}</td>"
            f"<td class='n'>{n:,} <span class='pct'>{n / total * 100:.2f}%</span></td>"
            f"<td class='c'>{_bar(n, max(c['section_chars'].values()))}</td></tr>"
        )

    term_section_head = "".join(f"<th>{html.escape(s)}</th>" for s in c["sections"])
    term_section_rows = ""
    for term in c["distribution_terms"]:
        tds = "".join(
            f"<td>{c['section_terms'][term].get(s, 0)}</td>" for s in c["sections"]
        )
        term_section_rows += f"<tr><th class='k'>{html.escape(term)}</th>{tds}</tr>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>明史 — Text Analysis</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ font-family: -apple-system, "Helvetica Neue", Arial, "PingFang SC", sans-serif;
         max-width: 900px; margin: 0 auto; padding: 1.5rem; line-height: 1.55; color: #1c1c1c; }}
  h1 {{ font-size: 1.6rem; margin-bottom: .2rem; }}
  h2 {{ font-size: 1.15rem; margin-top: 2rem; border-bottom: 2px solid #eee; padding-bottom: .3rem; }}
  .meta {{ color: #666; font-size: .9rem; }}
  table {{ border-collapse: collapse; width: 100%; margin: .8rem 0; font-size: .92rem; }}
  th, td {{ text-align: left; padding: .3rem .5rem; border-bottom: 1px solid #eee; }}
  td.n, th.k {{ white-space: nowrap; font-variant-numeric: tabular-nums; }}
  td.n {{ text-align: right; }}
  .pct {{ color: #888; margin-left: .4rem; }}
  .c {{ width: 45%; }}
  .bar {{ display: inline-block; height: .7rem; background: #b41e1e; border-radius: 3px; min-width: 1px; }}
  .dist {{ table-layout: fixed; }}
  .dist td, .dist th {{ text-align: center; border: 1px solid #f0f0f0; }}
  .dist th.k {{ text-align: left; }}
  code {{ background: #f5f5f5; padding: .1rem .3rem; border-radius: 3px; }}
  footer {{ margin-top: 2.5rem; color: #777; font-size: .85rem; }}
</style>
</head>
<body>
<h1>明史 — Text Analysis</h1>
<p class="meta">Source: Kanripo <code>KR2a0038</code>, a transcription of the
<i>Mingshi</i> 明史 (History of the Ming, 332 juan).<br>
Files analysed: {c['num_files']} &middot; Characters: {total:,}</p>

<h2>Method</h2>
<p>Kanripo markup (metadata comments, <code>&lt;pb:...&gt;</code> page tags, paragraph
marks and indentation) was removed and punctuation dropped, leaving CJK characters.
Formal and variant glyphs were merged (the Four Treasuries text writes 内 far more
often than standard 內, so both count as 內); this map is useful but not exhaustive.
"Bigrams" are pairs of adjacent characters and stand in for words, because written
Chinese has no spaces and a real word tokeniser is needed to count words exactly.</p>

<h2>1. Most frequent characters</h2>
<table><thead><tr><th>Character</th><th>Count</th><th></th></tr></thead>
<tbody>{_rows(c['top_chars'], total)}</tbody></table>

<h2>2. Most frequent bigrams (word-like pairs)</h2>
<table><thead><tr><th>Bigram</th><th>Count</th><th></th></tr></thead>
<tbody>{_rows(c['top_bigrams'])}</tbody></table>

<h2>3. Treacherous officials named in the 奸臣傳 (卷三百八)</h2>
<table><thead><tr><th>Name</th><th>Count</th><th></th></tr></thead>
<tbody>{_rows(c['jianchen'])}</tbody></table>

<h2>4. Other frequently named people</h2>
<table><thead><tr><th>Name</th><th>Count</th><th></th></tr></thead>
<tbody>{_rows(c['people'])}</tbody></table>

<h2>5. Official titles</h2>
<table><thead><tr><th>Title</th><th>Count</th><th></th></tr></thead>
<tbody>{_rows(c['offices'])}</tbody></table>

<h2>6. Distribution across the text</h2>
<p class="meta">Ten roughly equal blocks in reading order; darker means more mentions.</p>
<table class="dist"><thead><tr><th></th>{blocks_head}</tr></thead>
<tbody>{block_rows}</tbody></table>

<h2>7. Distribution by section</h2>
<table><thead><tr><th>Section</th><th>Chars</th><th></th></tr></thead>
<tbody>{section_rows}</tbody></table>
<table><thead><tr><th>Term</th>{term_section_head}</tr></thead>
<tbody>{term_section_rows}</tbody></table>

<footer>Counts are exact substring counts, so a name inside a longer name is
also counted. Read them as indications, not as a census.
Generated by <code>analyze_mingshi.py</code>.</footer>
</body>
</html>
"""


if __name__ == "__main__":
    main()
