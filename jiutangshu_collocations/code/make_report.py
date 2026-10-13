"""Build a single sortable HTML page from the collocation CSVs.

Run from anywhere (collocates.py must have run first):

    python code/make_report.py

Reads:  output/collocates_*.csv
Writes: output/results.html

The page has a dropdown to switch between the runs (window 5, window 10,
sentence). Click any column header to sort by it, so you can compare the
ranking by log_likelihood with the ranking by log_dice.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "output"
REPORT_PATH = OUT_DIR / "results.html"

LABELS = {
    "window5": "Window · horizon 5",
    "window10": "Window · horizon 10",
    "sentence": "Sentence",
}

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Collocates</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: -apple-system, system-ui, sans-serif; margin: 2rem; }
  h1 { font-size: 1.3rem; }
  select { font-size: 1rem; padding: .3rem; margin-bottom: 1rem; }
  table { border-collapse: collapse; width: 100%; font-size: .9rem; }
  th, td { border: 1px solid #8884; padding: .35rem .5rem; text-align: left; }
  th { cursor: pointer; user-select: none; background: #8881; position: sticky; top: 0; }
  th::after { content: ""; }
  th.sort-asc::after { content: " \\2191"; }
  th.sort-desc::after { content: " \\2193"; }
  tr:nth-child(even) { background: #8881; }
  .wrap { overflow-x: auto; }
</style>
</head>
<body>
<h1>Collocates of __TARGET__</h1>
<select id="run"></select>
<div class="wrap"><table id="table"></table></div>
<script>
const DATA = __DATA__;
const runSelect = document.getElementById("run");
const table = document.getElementById("table");
let sortKey = null, sortDir = -1;

Object.keys(DATA).forEach(key => {
  const opt = document.createElement("option");
  opt.value = key; opt.textContent = DATA[key].label;
  runSelect.appendChild(opt);
});

function sortRows(rows) {
  if (sortKey === null) return rows;
  const isNum = rows.length && typeof rows[0][sortKey] === "number";
  return rows.slice().sort((a, b) => {
    const x = a[sortKey], y = b[sortKey];
    if (x === null) return 1;
    if (y === null) return -1;
    if (isNum) return (x - y) * sortDir;
    return String(x).localeCompare(String(y)) * sortDir;
  });
}

function render() {
  const entry = DATA[runSelect.value];
  const rows = sortRows(entry.rows);
  const cols = entry.columns;
  let html = "<thead><tr>";
  cols.forEach(c => {
    const cls = c === sortKey ? (sortDir < 0 ? "sort-desc" : "sort-asc") : "";
    html += `<th class="${cls}" data-col="${c}">${c}</th>`;
  });
  html += "</tr></thead><tbody>";
  rows.forEach(r => {
    html += "<tr>";
    cols.forEach(c => {
      let v = r[c];
      if (typeof v === "number" && !Number.isInteger(v)) v = v.toFixed(4);
      html += `<td>${v === null ? "" : v}</td>`;
    });
    html += "</tr>";
  });
  html += "</tbody>";
  table.innerHTML = html;
  table.querySelectorAll("th").forEach(th => {
    th.addEventListener("click", () => {
      const col = th.dataset.col;
      if (col === sortKey) { sortDir *= -1; }
      else { sortKey = col; sortDir = -1; }
      render();
    });
  });
}

runSelect.addEventListener("change", render);
render();
</script>
</body>
</html>
"""


def main() -> int:
    csv_files = sorted(OUT_DIR.glob("collocates_*.csv"))
    if not csv_files:
        raise SystemExit(
            f"no collocates_*.csv in {OUT_DIR}; run `python code/collocates.py` first."
        )

    runs = {}
    for path in csv_files:
        key = path.stem.replace("collocates_", "")
        try:
            frame = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            print(f"[warn] {path.name} is empty; skipping.")
            continue
        frame = frame.where(pd.notnull(frame), None)
        runs[key] = {
            "label": LABELS.get(key, key),
            "columns": list(frame.columns),
            "rows": frame.to_dict(orient="records"),
        }
        print(f"[info] {key}: {len(frame):,} rows, columns={list(frame.columns)}")

    if not runs:
        raise SystemExit("no non-empty collocate CSVs found; nothing to report.")

    html = (TEMPLATE
            .replace("__DATA__", json.dumps(runs, ensure_ascii=False))
            .replace("__TARGET__", "钱"))
    REPORT_PATH.write_text(html, encoding="utf-8")
    print(f"[info] wrote report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
