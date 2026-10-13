"""Find collocates of a target word in the segmented 舊唐書·食貨志 corpus.

Run from anywhere (segment.py must have run first):

    python code/collocates.py

Reads:  output/sentences.txt
Writes: output/collocates_window5.csv
        output/collocates_window10.csv
        output/collocates_sentence.csv
Prints: the top 20 rows of each run.

The three runs answer the same question under three definitions of "near":
a 5-word window, a 10-word window, and the whole sentence.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from qhchina import load_stopwords
from qhchina.analytics import find_collocates

# Used only when a run returns no rows, so the CSV still has a readable header.
EMPTY_COLUMNS = ["target", "collocate", "exp_local", "obs_local", "ratio_local",
                 "obs_global", "p_value", "log_likelihood", "log_dice",
                 "adjusted_p_value"]

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SENTENCES_IN = PROJECT_ROOT / "output" / "sentences.txt"
OUT_DIR = PROJECT_ROOT / "output"

TARGET = "钱"  # simplified characters, matching sentences.txt
MEASURES = ["log_likelihood", "log_dice"]
CORRECTION = "fdr_bh"
TOP_N = 20

RUNS = [
    ("window5", {"method": "window", "horizon": 5}),
    ("window10", {"method": "window", "horizon": 10}),
    ("sentence", {"method": "sentence"}),
]


def load_sentences():
    if not SENTENCES_IN.exists():
        raise SystemExit(
            f"missing {SENTENCES_IN}; run `python code/segment.py` first."
        )
    sentences = []
    for line in SENTENCES_IN.read_text(encoding="utf-8").splitlines():
        tokens = line.split()
        if tokens:
            sentences.append(tokens)
    return sentences


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sentences = load_sentences()
    print(f"[info] {len(sentences):,} sentences loaded")

    stopwords = load_stopwords("zh_cl_sim")
    print(f"[info] loaded {len(stopwords):,} classical-Chinese stopwords")

    filters = {
        "stopwords": stopwords,
        # Classical Chinese: keep single-character collocates (賦、租、雜、橫…),
        # so the minimum is 1, not 2. See project README for why.
        "min_word_length": 1,
        "min_obs_local": 3,
        "max_adjusted_p": 0.05,
    }

    for name, options in RUNS:
        label = options["method"] if options["method"] == "sentence" else \
            f"{options['method']} horizon={options['horizon']}"
        print(f"\n=== {name} ({label}) ===")

        frame = find_collocates(
            sentences,
            target_words=TARGET,
            measures=MEASURES,
            filters=filters,
            correction=CORRECTION,
            sort_by="log_dice",
            ascending=False,
            **options,
        )

        if frame.empty and not len(frame.columns):
            frame = pd.DataFrame(columns=EMPTY_COLUMNS)

        out_path = OUT_DIR / f"collocates_{name}.csv"
        frame.to_csv(out_path, index=False, encoding="utf-8")
        print(f"[info] {len(frame):,} collocates -> {out_path}")

        columns = [c for c in ["collocate", "obs_local", "obs_global",
                               "ratio_local", "log_likelihood", "log_dice",
                               "adjusted_p_value"] if c in frame.columns]
        print("top {} by log_dice:".format(TOP_N))
        print(frame[columns].head(TOP_N).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
