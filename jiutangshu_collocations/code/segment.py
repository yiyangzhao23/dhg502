"""Segment 舊唐書食貨志.txt into sentences for collocation analysis.

Run from anywhere:

    python code/segment.py

Reads:  data/舊唐書食貨志.txt   (classical Chinese, traditional, UTF-8)
        userdict.txt            (jieba user dictionary, simplified)
Writes: output/sentences.txt        (one sentence per line, space separated)
        output/sentence_index.csv   (only if the source marks 卷)
Prints: 20 random segmented sentences containing a target word, for eyeballing.
"""

from __future__ import annotations

import csv
import random
import re
import sys
from pathlib import Path

import jieba

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_TEXT = PROJECT_ROOT / "data" / "舊唐書食貨志.txt"
USERDICT = PROJECT_ROOT / "userdict.txt"
OUT_DIR = PROJECT_ROOT / "output"
SENTENCES_OUT = OUT_DIR / "sentences.txt"
INDEX_OUT = OUT_DIR / "sentence_index.csv"

MIN_WORDS = 5
TARGET_WORDS = ["钱"]

SENTENCE_END = "。！？；!?;"
CHAPTER_RE = re.compile(r"^\s*卷\s*[第]?\s*([0-9一二三四五六七八九十百千零〇两]+)\s*(.*)$")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
PUNCT = set("。，、；：！？「」『』（）《》〈〉【】·—…“”‘’〇　 \t\r\n0123456789"
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
            ",.;:!?()[]{}<>\"'`~@#$%^&*_+=|\\/-")


def load_converter():
    """Return an opencc traditional->simplified converter, or identity."""
    try:
        from opencc import OpenCC

        return OpenCC("t2s").convert
    except Exception as exc:  # pragma: no cover - depends on environment
        print(f"[warn] opencc unavailable ({exc}); skipping conversion.", file=sys.stderr)
        return lambda text: text


def is_chapter_header(line: str):
    """Return (number, title) if the line starts a 卷, else None."""
    match = CHAPTER_RE.match(line)
    if not match:
        return None
    number, rest = match.group(1), match.group(2).strip()
    title = rest.strip("　 .0123456789")
    return number, title


def extract_complete(buffer: str):
    """Split off complete sentences; return (complete, remainder).

    The remainder is the text after the last sentence-ending punctuation, so a
    sentence wrapped across two lines is reassembled before being tokenized.
    """
    parts = re.split(f"[{re.escape(SENTENCE_END)}]+", buffer)
    remainder = parts[-1]
    complete = [p.strip() for p in parts[:-1] if p.strip()]
    return complete, remainder


def tokenize(sentence: str):
    """Tokenize with jieba and keep only tokens containing a CJK character."""
    tokens = []
    for token in jieba.cut(sentence):
        token = token.strip()
        if not token or token in PUNCT or not CJK_RE.search(token):
            continue
        tokens.append(token)
    return tokens


def main() -> int:
    if not RAW_TEXT.exists():
        print(f"[error] missing source text: {RAW_TEXT}", file=sys.stderr)
        print("        place 舊唐書食貨志.txt in data/ and re-run.", file=sys.stderr)
        return 1

    converter = load_converter()
    if USERDICT.exists():
        jieba.load_userdict(str(USERDICT))
        print(f"[info] loaded user dictionary: {USERDICT}")
    else:
        print(f"[warn] no user dictionary at {USERDICT}; names may be split.",
              file=sys.stderr)

    raw = RAW_TEXT.read_text(encoding="utf-8-sig")
    simplified = converter(raw)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    sentences: list[str] = []
    index_rows: list[dict] = []
    current_number, current_title = "", ""
    saw_chapter = False

    def emit(sentence: str) -> None:
        tokens = tokenize(sentence)
        if len(tokens) < MIN_WORDS:
            return
        sentences.append(" ".join(tokens))
        index_rows.append({
            "sentence_id": len(sentences),
            "chapter_no": current_number,
            "chapter_title": current_title,
        })

    buffer = ""
    for line in simplified.splitlines():
        header = is_chapter_header(line)
        if header is not None:
            complete, remainder = extract_complete(buffer)
            for sentence in complete:
                emit(sentence)
            if remainder.strip():
                emit(remainder)
            buffer = ""
            saw_chapter = True
            current_number, current_title = header
            # The rest of a 卷 line is its title, not prose: discard it.
            line = ""

        complete, buffer = extract_complete(buffer + line)
        for sentence in complete:
            emit(sentence)

    if buffer.strip():
        emit(buffer)

    SENTENCES_OUT.write_text("\n".join(sentences) + "\n", encoding="utf-8")

    if saw_chapter:
        with INDEX_OUT.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=["sentence_id", "chapter_no", "chapter_title"])
            writer.writeheader()
            writer.writerows(index_rows)
        print(f"[info] wrote chapter index: {INDEX_OUT}")

    print(f"[info] wrote {len(sentences):,} sentences to {SENTENCES_OUT}")

    hits = [s for s in sentences if any(t in s for t in TARGET_WORDS)]
    sample = random.sample(hits, min(20, len(hits)))
    print(f"\n[check] {len(hits):,} sentences contain {TARGET_WORDS}; "
          f"showing {len(sample)} at random:\n")
    for sentence in sample:
        print("  " + sentence)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
