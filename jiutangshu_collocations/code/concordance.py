"""Show passages where the target and each collocate occur together (KWIC).

Run from anywhere (segment.py must have run; collocates.py preferred):

    python code/concordance.py

Reads:  output/sentences.txt
        output/sentence_index.csv   (optional, if present)
        output/collocates_window5.csv   (only to pick defaults)
Writes: output/kwic.html

Edit COLLOCATES below to choose what to inspect, or leave it empty to take
the top collocates from the window-5 run automatically.
"""

from __future__ import annotations

import csv
import html as html_escape
from collections import defaultdict
from pathlib import Path

from qhchina.analytics import kwic

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SENTENCES_IN = PROJECT_ROOT / "output" / "sentences.txt"
INDEX_IN = PROJECT_ROOT / "output" / "sentence_index.csv"
DEFAULT_CSV = PROJECT_ROOT / "output" / "collocates_window5.csv"
OUT_PATH = PROJECT_ROOT / "output" / "kwic.html"

TARGET = "钱"
HORIZON = 10
MAX_PER_COLLOCATE = 10

# Leave empty to auto-fill from output/collocates_window5.csv.
COLLOCATES: list[str] = []


def load_sentences():
    if not SENTENCES_IN.exists():
        raise SystemExit(
            f"missing {SENTENCES_IN}; run `python code/segment.py` first."
        )
    return [line.split() for line in SENTENCES_IN.read_text(encoding="utf-8").splitlines()
            if line.split()]


def load_chapters():
    """Map 0-based sentence index -> '卷XXX title' using sentence_index.csv."""
    chapters: dict[int, str] = {}
    if not INDEX_IN.exists():
        return chapters
    with INDEX_IN.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            number = row.get("chapter_no", "").strip()
            title = row.get("chapter_title", "").strip()
            label = f"卷{number} {title}".strip()
            chapters[int(row["sentence_id"]) - 1] = label
    return chapters


def resolve_collocates() -> list[str]:
    if COLLOCATES:
        return COLLOCATES
    import pandas as pd

    candidates = [DEFAULT_CSV,
                  DEFAULT_CSV.with_name("collocates_window10.csv"),
                  DEFAULT_CSV.with_name("collocates_sentence.csv")]
    for path in candidates:
        if not path.exists():
            continue
        try:
            frame = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            continue
        if "collocate" in frame.columns and not frame.empty:
            return list(frame["collocate"].head(MAX_PER_COLLOCATE))
    return []


def main() -> int:
    sentences = load_sentences()
    chapters = load_chapters()
    collocates = resolve_collocates()
    if not collocates:
        raise SystemExit("no collocates given and no output/collocates_window5.csv found")

    print(f"[info] {len(sentences):,} sentences; collocates: {collocates}")

    lines = kwic(sentences, target=TARGET, horizon=HORIZON,
                 separator=" ", return_type="list")

    by_collocate: dict[str, list[dict]] = defaultdict(list)
    for line in lines:
        context = set(line["left_tokens"]) | set(line["right_tokens"])
        for collocate in collocates:
            if collocate in context and len(by_collocate[collocate]) < MAX_PER_COLLOCATE:
                by_collocate[collocate].append(line)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    parts = [
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>",
        f"<title>KWIC · {TARGET}</title>",
        "<style>body{font-family:-apple-system,system-ui,sans-serif;margin:2rem}",
        "h2{margin-top:2rem;font-size:1.1rem}table{border-collapse:collapse;width:100%;font-size:.9rem}",
        "th,td{border:1px solid #8884;padding:.35rem .5rem;vertical-align:top;text-align:left}",
        "th{background:#8881}td.kwic{white-space:nowrap}mark{background:#f8d66d}</style></head><body>",
        f"<h1>KWIC · {html_escape.escape(TARGET)} (horizon {HORIZON})</h1>",
    ]

    for collocate in collocates:
        rows = by_collocate.get(collocate, [])
        parts.append(f"<h2>{html_escape.escape(collocate)} "
                     f"<small>({len(rows)} passages)</small></h2>")
        parts.append("<table><thead><tr><th>卷</th><th>left</th><th>node</th>"
                     "<th>right</th></tr></thead><tbody>")
        for row in rows:
            chapter = chapters.get(row["doc_index"], "")
            left = html_escape.escape(row["left"])
            right = html_escape.escape(row["right"])
            node = html_escape.escape(row["node"])
            parts.append(
                f"<tr><td>{html_escape.escape(chapter)}</td>"
                f"<td class='kwic'>{left}</td>"
                f"<td class='kwic'><mark>{node}</mark></td>"
                f"<td class='kwic'>{right}</td></tr>"
            )
        parts.append("</tbody></table>")

    parts.append("</body></html>")
    OUT_PATH.write_text("".join(parts), encoding="utf-8")
    print(f"[info] wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
