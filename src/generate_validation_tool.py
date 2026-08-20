"""
Regenerates src/validation_tool.html from the current contents of
data/validation/*.csv.

Why this exists as a script rather than a hand-edited HTML file: the tool
embeds a snapshot of the sample rows AND whatever annotations already exist
in the CSVs, so re-running this after any change to the samples (or to pick
up manual edits made directly in the CSVs) regenerates a tool that reflects
reality instead of drifting out of sync with it.

Run from the project root:
    python -m src.generate_validation_tool
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.config import VALIDATION_DATA_DIR, PROJECT_ROOT

OUTPUT_PATH = PROJECT_ROOT / "src" / "validation_tool.html"

# Matches the priority order written in 04_validation.ipynb: money-affecting
# categories first, then app_performance (newly broadened rules, unchecked),
# then everything else. The tool queue follows this so time-limited sessions
# annotate the highest-value rows first.
PRIORITY_ORDER = [
    "unexplained_deduction",
    "transaction_failed_balance_deducted",
    "app_performance",
]


def _normalize_correct(value) -> str:
    """Map whatever is currently in a 'correct' cell to the tool's vocabulary.

    Only '1'/'1.0' and '0'/'0.0' count as real annotations. Anything else
    (blank, NaN, '?', stray text) is treated as not-yet-annotated rather than
    silently coerced into a judgment nobody actually made.
    """
    if pd.isna(value):
        return ""
    s = str(value).strip().lower()
    if s in ("1", "1.0"):
        return "1"
    if s in ("0", "0.0"):
        return "0"
    if s == "unsure":
        return "unsure"
    return ""


def _normalize_actual_issue(value) -> str:
    if pd.isna(value):
        return ""
    s = str(value).strip()
    return s


def _load_precision_samples() -> dict:
    samples = {}
    for csv_path in sorted(VALIDATION_DATA_DIR.glob("precision_*.csv")):
        category = csv_path.stem.replace("precision_", "")
        df = pd.read_csv(csv_path)
        rows = []
        for _, r in df.iterrows():
            rows.append({
                "review_id": r["review_id"],
                "rating": int(r["rating"]),
                "review_text": str(r["review_text"]),
                "seed_correct": _normalize_correct(r.get("correct", "")),
            })
        samples[category] = rows
    return samples


def _load_recall_sample() -> list:
    path = VALIDATION_DATA_DIR / "recall_gap_sample.csv"
    if not path.exists():
        return []
    df = pd.read_csv(path)
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "review_id": r["review_id"],
            "rating": int(r["rating"]),
            "review_text": str(r["review_text"]),
            "seed_actual_issue": _normalize_actual_issue(r.get("actual_issue", "")),
        })
    return rows


# Category definitions shown in the tool's info box. Kept here (not read from
# issue_classification.py) since that module defines regex patterns, not
# human-readable descriptions — duplicating a short definition string is
# simpler than parsing docstrings out of the classifier.
DEFINITIONS = {
    "transaction_failed_balance_deducted": "QRIS/transfer/top-up reported as failed, but balance is still deducted and not refunded.",
    "indicator_light_stuck": "The in-app payment-readiness indicator (red/green/blue light) gets stuck or is slow to change, blocking or delaying QRIS scans.",
    "unexplained_deduction": "Balance decreases with no matching entry in mutasi (transaction history), not tied to a specific attempted transaction.",
    "face_verification_failure": "Face/biometric verification (login, registration, OTP) repeatedly fails, especially on older phones.",
    "login_otp_access": "Cannot log in, or OTP/access process is broken or overly burdensome (SIM swap, pulsa-dependent OTP).",
    "app_performance": "App is slow, errors out, crashes, or won't open/can't be accessed — general technical malfunction not clearly tied to QRIS/indicator.",
    "maintenance_downtime": "Scheduled maintenance at inconvenient times (often unannounced), blocking transactions.",
    "customer_service": "CS/branch/call-center complaints go unresolved, unreachable, or get looped without response.",
    "ui_ux_regression": "Post-update interface changes reduce usability (lost features, confusing layout).",
    "device_compatibility": "App reports device/version incompatibility, can't install/update.",
}


def build_data_payload() -> dict:
    precision = _load_precision_samples()
    recall = _load_recall_sample()

    remaining = [c for c in precision if c not in PRIORITY_ORDER]
    category_list = [c for c in PRIORITY_ORDER if c in precision] + sorted(remaining)

    return {
        "precision": {
            cat: {"definition": DEFINITIONS.get(cat, ""), "rows": rows}
            for cat, rows in precision.items()
        },
        "recall": recall,
        "category_list": category_list,
    }


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Issue Classifier — Manual Validation</title>
<style>
  :root {
    --ink: #1a1a1a;
    --paper: #faf9f6;
    --line: #ddd8ce;
    --accent: #b23a2e;
    --accent-soft: #e8c9c4;
    --good: #3a6b4c;
    --good-soft: #cfe3d6;
    --muted: #8a8378;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--paper);
    color: var(--ink);
    font-family: "Georgia", "Iowan Old Style", serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    min-height: 100vh;
    padding: 24px 16px 60px;
  }
  .wrap { width: 100%; max-width: 640px; }
  h1 {
    font-size: 15px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-weight: 600;
    color: var(--muted);
    text-align: center;
    margin: 0 0 4px;
  }
  .subtitle {
    text-align: center;
    font-size: 13px;
    color: var(--muted);
    margin-bottom: 20px;
    font-family: -apple-system, sans-serif;
  }
  .storage-note {
    text-align: center;
    font-size: 11px;
    color: var(--muted);
    font-family: -apple-system, sans-serif;
    margin: -12px 0 18px;
  }
  select {
    width: 100%;
    padding: 10px 12px;
    font-size: 14px;
    font-family: -apple-system, sans-serif;
    border: 1px solid var(--line);
    border-radius: 6px;
    background: white;
    color: var(--ink);
    margin-bottom: 14px;
  }
  .defbox {
    background: white;
    border: 1px solid var(--line);
    border-left: 3px solid var(--accent);
    border-radius: 4px;
    padding: 12px 14px;
    font-size: 13px;
    line-height: 1.5;
    color: #444;
    margin-bottom: 18px;
    font-family: -apple-system, sans-serif;
  }
  .defbox b { color: var(--ink); }
  .progress-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-family: -apple-system, sans-serif;
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 8px;
  }
  .progress-bar {
    height: 4px;
    background: var(--line);
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 20px;
  }
  .progress-fill {
    height: 100%;
    background: var(--good);
    transition: width 0.2s ease;
  }
  .card {
    background: white;
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 28px 26px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }
  .rating {
    display: inline-block;
    font-family: -apple-system, sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.04em;
    color: white;
    background: var(--muted);
    padding: 3px 9px;
    border-radius: 20px;
    margin-bottom: 14px;
  }
  .review-text {
    font-size: 18px;
    line-height: 1.65;
    color: var(--ink);
    min-height: 90px;
  }
  .btn-row {
    display: flex;
    gap: 10px;
    margin-top: 24px;
    flex-wrap: wrap;
  }
  button {
    font-family: -apple-system, sans-serif;
    font-size: 14px;
    font-weight: 600;
    padding: 12px 18px;
    border-radius: 8px;
    border: 1.5px solid var(--line);
    background: white;
    color: var(--ink);
    cursor: pointer;
    transition: all 0.12s ease;
    flex: 1;
    min-width: 100px;
  }
  button:hover { border-color: var(--muted); }
  .btn-correct { border-color: var(--good); color: var(--good); }
  .btn-correct:hover, .btn-correct.active { background: var(--good-soft); }
  .btn-wrong { border-color: var(--accent); color: var(--accent); }
  .btn-wrong:hover, .btn-wrong.active { background: var(--accent-soft); }
  .btn-unsure { color: var(--muted); flex: 0 0 100%; margin-top: 2px; font-weight: 500; font-size: 13px; padding: 8px; }
  select.issue-picker {
    width: 100%;
    padding: 12px;
    font-size: 14px;
    font-weight: 600;
    border: 1.5px solid var(--line);
    border-radius: 8px;
    margin-top: 22px;
    font-family: -apple-system, sans-serif;
  }
  .nav-row {
    display: flex;
    justify-content: space-between;
    margin-top: 18px;
    font-family: -apple-system, sans-serif;
  }
  .nav-btn {
    background: none;
    border: none;
    color: var(--muted);
    font-size: 13px;
    font-weight: 500;
    padding: 6px 4px;
    flex: 0 0 auto;
    min-width: 0;
  }
  .nav-btn:hover { color: var(--ink); }
  .hint {
    text-align: center;
    font-family: -apple-system, sans-serif;
    font-size: 11px;
    color: var(--muted);
    margin-top: 10px;
  }
  .footer-row {
    display: flex;
    gap: 10px;
    margin-top: 28px;
  }
  .footer-btn {
    flex: 1;
    background: var(--ink);
    color: white;
    border: none;
    font-family: -apple-system, sans-serif;
    font-weight: 600;
    font-size: 13px;
    padding: 12px;
    border-radius: 8px;
    cursor: pointer;
  }
  .footer-btn.secondary {
    background: white;
    color: var(--ink);
    border: 1.5px solid var(--line);
  }
  .done-banner {
    text-align: center;
    font-family: -apple-system, sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: var(--good);
    padding: 10px;
    background: var(--good-soft);
    border-radius: 8px;
    margin-bottom: 14px;
    display: none;
  }
  .warn-banner {
    text-align: center;
    font-family: -apple-system, sans-serif;
    font-size: 12px;
    font-weight: 600;
    color: var(--accent);
    padding: 10px;
    background: var(--accent-soft);
    border-radius: 8px;
    margin-bottom: 14px;
    display: none;
  }
</style>
</head>
<body>
<div class="wrap">
  <h1>Issue Classifier Validation</h1>
  <div class="subtitle" id="modeLabel">Precision check</div>
  <div class="storage-note" id="storageNote"></div>

  <select id="categorySelect"></select>

  <div class="defbox" id="defBox"></div>

  <div class="done-banner" id="doneBanner">All rows in this set are annotated. Export when ready.</div>

  <div class="progress-row">
    <span id="progressText"></span>
    <span id="progressCount"></span>
  </div>
  <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>

  <div class="card">
    <div class="rating" id="ratingTag"></div>
    <div class="review-text" id="reviewText"></div>

    <div id="precisionButtons" class="btn-row" style="display:none;">
      <button class="btn-correct" id="btnCorrect" onclick="answer('1')">&#x2713; Correct <span style="opacity:.5;font-weight:400">(1)</span></button>
      <button class="btn-wrong" id="btnWrong" onclick="answer('0')">&#x2717; Wrong <span style="opacity:.5;font-weight:400">(0)</span></button>
      <button class="btn-unsure" id="btnUnsure" onclick="answer('unsure')">? Unsure — flag for later review <span style="opacity:.5;font-weight:400">(U)</span></button>
    </div>

    <div id="recallPicker" style="display:none;">
      <select class="issue-picker" id="issueSelect" onchange="answerFromPicker()">
        <option value="">— select what this review is actually about —</option>
      </select>
    </div>
  </div>

  <div class="nav-row">
    <button class="nav-btn" onclick="prevRow()">&larr; Previous</button>
    <span class="hint" id="jumpHint"></span>
    <button class="nav-btn" onclick="nextRow()">Next &rarr;</button>
  </div>

  <div class="footer-row">
    <button class="footer-btn secondary" onclick="exportCurrent()">Export this category's CSV</button>
    <button class="footer-btn" onclick="exportAll()">Export all as CSV files</button>
  </div>
  <div class="hint">Progress saves automatically to this browser (localStorage). Keyboard: 1 / 0 / U for precision, &larr; &rarr; to navigate. Exported CSVs go to your Downloads folder — move them into data/validation/ to replace the originals.</div>
</div>

<script>
const DATA = __DATA_JSON__;
const STORAGE_PREFIX = 'bca_validation:';

let currentSet = DATA.category_list[0];
let currentIndex = 0;
let answers = {}; // in-memory cache, keyed by set name -> {review_id: value}

const catSelect = document.getElementById('categorySelect');
const defBox = document.getElementById('defBox');
const modeLabel = document.getElementById('modeLabel');
const precisionButtons = document.getElementById('precisionButtons');
const recallPicker = document.getElementById('recallPicker');
const issueSelect = document.getElementById('issueSelect');
const storageNote = document.getElementById('storageNote');

// localStorage is per-browser-profile and per-origin. For a file opened via
// file://, that's effectively "this file, in this browser, on this machine" -
// it will NOT sync across browsers or machines. Export regularly.
let storageWorks = true;
try {
  const testKey = '__storage_test__';
  window.localStorage.setItem(testKey, '1');
  window.localStorage.removeItem(testKey);
} catch (e) {
  storageWorks = false;
}
storageNote.textContent = storageWorks
  ? 'Progress auto-saves in this browser only. Export CSVs to keep a permanent copy.'
  : 'Warning: this browser is blocking local storage (private/incognito mode?). Progress will NOT persist across reloads — export after every session.';

function buildCategoryOptions() {
  catSelect.innerHTML = '';
  for (const cat of DATA.category_list) {
    const n = DATA.precision[cat].rows.length;
    const opt = document.createElement('option');
    opt.value = cat;
    opt.textContent = `Precision — ${cat} (${n} rows)`;
    catSelect.appendChild(opt);
  }
  const recallOpt = document.createElement('option');
  recallOpt.value = '__recall__';
  recallOpt.textContent = `Recall / coverage gap sample (${DATA.recall.length} rows)`;
  catSelect.appendChild(recallOpt);

  issueSelect.innerHTML = '<option value="">— select what this review is actually about —</option>';
  for (const cat of DATA.category_list) {
    const opt = document.createElement('option');
    opt.value = cat;
    opt.textContent = cat;
    issueSelect.appendChild(opt);
  }
  const noneOpt = document.createElement('option');
  noneOpt.value = 'none';
  noneOpt.textContent = 'none (genuine one-off, no real category)';
  issueSelect.appendChild(noneOpt);
}

function getCurrentRows() {
  if (currentSet === '__recall__') return DATA.recall;
  return DATA.precision[currentSet].rows;
}

// Builds the starting answer set for a category/set: whatever was already
// annotated in the CSV (seed_correct / seed_actual_issue) unless this browser
// already has its own localStorage copy, in which case the browser copy wins
// (it's presumed more recent than the seed baked in at generation time).
function loadAnswers(setKey) {
  const storageKey = STORAGE_PREFIX + setKey;
  if (storageWorks) {
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (raw !== null) return JSON.parse(raw);
    } catch (e) { /* fall through to seed */ }
  }
  const seeded = {};
  const rows = setKey === '__recall__' ? DATA.recall : DATA.precision[setKey].rows;
  for (const row of rows) {
    const seedVal = setKey === '__recall__' ? row.seed_actual_issue : row.seed_correct;
    if (seedVal) seeded[row.review_id] = seedVal;
  }
  return seeded;
}

function saveAnswer(setKey, reviewId, value) {
  if (!answers[setKey]) answers[setKey] = {};
  answers[setKey][reviewId] = value;
  if (storageWorks) {
    try {
      window.localStorage.setItem(STORAGE_PREFIX + setKey, JSON.stringify(answers[setKey]));
    } catch (e) {
      console.error('localStorage save failed', e);
    }
  }
}

function render() {
  const rows = getCurrentRows();
  if (rows.length === 0) {
    document.getElementById('reviewText').textContent = 'No rows in this sample.';
    return;
  }
  if (currentIndex >= rows.length) currentIndex = rows.length - 1;
  if (currentIndex < 0) currentIndex = 0;

  const row = rows[currentIndex];
  document.getElementById('ratingTag').textContent = `${row.rating}\u2605 review`;
  document.getElementById('reviewText').textContent = row.review_text;

  if (!answers[currentSet]) answers[currentSet] = loadAnswers(currentSet);
  const existing = answers[currentSet][row.review_id];

  if (currentSet === '__recall__') {
    modeLabel.textContent = 'Recall / coverage gap check';
    defBox.innerHTML = '<b>Task:</b> this review was NOT tagged with any issue by the classifier. Does it actually describe one of the 10 known issues (a real miss), or is it a genuine one-off / vague complaint (select "none")?';
    precisionButtons.style.display = 'none';
    recallPicker.style.display = 'block';
    issueSelect.value = existing || '';
  } else {
    modeLabel.textContent = 'Precision check';
    defBox.innerHTML = `<b>${currentSet}</b> — ${DATA.precision[currentSet].definition}`;
    precisionButtons.style.display = 'flex';
    recallPicker.style.display = 'none';
    document.getElementById('btnCorrect').classList.toggle('active', existing === '1');
    document.getElementById('btnWrong').classList.toggle('active', existing === '0');
    document.getElementById('btnUnsure').classList.toggle('active', existing === 'unsure');
  }

  const answeredCount = Object.keys(answers[currentSet] || {}).length;
  document.getElementById('progressText').textContent = `Row ${currentIndex + 1} of ${rows.length}`;
  document.getElementById('progressCount').textContent = `${answeredCount} / ${rows.length} annotated`;
  document.getElementById('progressFill').style.width = `${(answeredCount / rows.length) * 100}%`;
  document.getElementById('doneBanner').style.display = (answeredCount >= rows.length) ? 'block' : 'none';
}

function answer(value) {
  const rows = getCurrentRows();
  const row = rows[currentIndex];
  saveAnswer(currentSet, row.review_id, value);
  render();
  setTimeout(() => { if (currentIndex < rows.length - 1) { currentIndex++; render(); } }, 180);
}

function answerFromPicker() {
  const rows = getCurrentRows();
  const row = rows[currentIndex];
  const value = issueSelect.value;
  if (!value) return;
  saveAnswer(currentSet, row.review_id, value);
  render();
  setTimeout(() => { if (currentIndex < rows.length - 1) { currentIndex++; render(); } }, 180);
}

function nextRow() {
  const rows = getCurrentRows();
  if (currentIndex < rows.length - 1) { currentIndex++; render(); }
}
function prevRow() {
  if (currentIndex > 0) { currentIndex--; render(); }
}

catSelect.addEventListener('change', () => {
  currentSet = catSelect.value;
  currentIndex = 0;
  answers[currentSet] = loadAnswers(currentSet);
  render();
});

document.addEventListener('keydown', (e) => {
  const tag = (e.target && e.target.tagName) || '';
  if (tag === 'SELECT') return; // don't hijack keys while a dropdown has focus
  if (currentSet !== '__recall__') {
    if (e.key === '1') answer('1');
    else if (e.key === '0') answer('0');
    else if (e.key.toLowerCase() === 'u') answer('unsure');
  }
  if (e.key === 'ArrowRight') nextRow();
  else if (e.key === 'ArrowLeft') prevRow();
});

function toCSV(rows, setKey, valueColName) {
  const header = ['review_id', 'rating', 'review_text', valueColName];
  const lines = [header.join(',')];
  const ans = answers[setKey] || {};
  for (const row of rows) {
    const val = ans[row.review_id] || '';
    const escapedText = '"' + String(row.review_text).replace(/"/g, '""') + '"';
    lines.push([row.review_id, row.rating, escapedText, val].join(','));
  }
  return lines.join('\n');
}

function downloadCSV(content, filename) {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function exportCurrent() {
  const rows = getCurrentRows();
  if (currentSet === '__recall__') {
    downloadCSV(toCSV(rows, '__recall__', 'actual_issue'), 'recall_gap_sample.csv');
  } else {
    downloadCSV(toCSV(rows, currentSet, 'correct'), `precision_${currentSet}.csv`);
  }
}

function exportAll() {
  let delay = 0;
  for (const cat of DATA.category_list) {
    if (!answers[cat]) answers[cat] = loadAnswers(cat);
    setTimeout(() => {
      downloadCSV(toCSV(DATA.precision[cat].rows, cat, 'correct'), `precision_${cat}.csv`);
    }, delay);
    delay += 200;
  }
  if (!answers['__recall__']) answers['__recall__'] = loadAnswers('__recall__');
  setTimeout(() => {
    downloadCSV(toCSV(DATA.recall, '__recall__', 'actual_issue'), 'recall_gap_sample.csv');
  }, delay);
}

(function init() {
  buildCategoryOptions();
  answers[currentSet] = loadAnswers(currentSet);
  render();
})();
</script>
</body>
</html>
"""


def main() -> None:
    payload = build_data_payload()
    html = HTML_TEMPLATE.replace("__DATA_JSON__", json.dumps(payload, ensure_ascii=False))
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({len(html):,} chars)")
    total_seeded = sum(
        1 for cat_rows in payload["precision"].values()
        for r in cat_rows["rows"] if r["seed_correct"]
    )
    total_rows = sum(len(c["rows"]) for c in payload["precision"].values())
    print(f"Precision rows: {total_seeded}/{total_rows} already annotated (carried over from CSVs)")


if __name__ == "__main__":
    main()
