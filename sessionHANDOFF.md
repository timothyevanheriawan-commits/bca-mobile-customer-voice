# Session Handoff — bca-mobile-customer-voice

**Date:** 2026-08-21 (session 4, Claude — regex fix)
**Status:** Targeted precision fix for `app_performance` and
`unexplained_deduction`, the two categories flagged `needs_regex_fix` in
every session since Round 6. UI was NOT touched this session — Timothy's
own read was that the redesign is decent and the regex is the real problem,
so this session stayed precision-only per his call.

## What happened this session

Read every false positive by hand in `data/validation/precision_app_performance.csv`
(12 of 30) and `data/validation/precision_unexplained_deduction.csv` (9 of
30) before writing any new pattern — same discipline as every prior round.

**`unexplained_deduction` (0.700 -> re-scored 1.000 against the same
annotations, see caveat below):** the Round 6 exclude only recognized
`gagal` as the "this describes a specific failed transaction attempt"
signal, and required the literal spelling `transaksi`. Two things slipped
through: (1) transposition typos (`tramsaksi`, `tarnsaksi`) never matched
the literal word, and (2) reviews using `gangguan` or `pending` instead of
`gagal` as the failure word weren't covered at all. Dropped the `transaksi`
requirement entirely and widened the failure-word set to
`gagal|gangguan|pending`, checked directly against a deduction word within
a 120-char window. Verified this doesn't touch any of the 21 confirmed true
positives in the sample — none of them use those three words near a
deduction word.

**`app_performance` (0.600 -> re-scored 0.750 against the same
annotations):** four separate false-positive patterns, of which three were
fixed:
- "can't open the app" caused by an old/unsupported device is
  `device_compatibility`'s story, not a generic performance one — added an
  exclude for `versi lama` / `hp jadul` / `ga support` context.
- A named transaction type failing with the balance deducted belongs to
  `transaction_failed_balance_deducted` / `unexplained_deduction`, not a
  standalone performance complaint — added the same qris/transfer +
  kepotong exclude pattern used on the other side.
- Two negation misses: `"ga pake lemot (lagi)"` means NO LONGER laggy (a
  positive review), and `"jangan lemot ya"` is a closing wish, not a
  description of an active problem. Both bare-keyword matches couldn't
  tell affirmation from negation or wish from complaint.

**Deliberately NOT fixed — real ambiguity, not a missed pattern:** several
of the remaining false positives mention the indicator light (`lampu` /
`indikator` / `sinyal` + a color) alongside a generic trigger word like
`lemot` or `gangguan`. I built an exclude for this and then checked it
against the sample's confirmed TRUE positives before keeping it — and it
would have flipped at least 3 real true positives to false negatives (e.g.
`"Sekarang BCA mobile sering eror, indikator merah terus..."`, correct=1,
uses the exact same vocabulary shape as the false positives). There's no
regex-visible difference between those two cases in this sample. Left as
residual noise rather than force a rule that trades false positives for
false negatives — same practice as the single-row edge cases left alone in
earlier rounds (see module docstring). `app_performance` landing at 0.75
instead of clearing 0.80 is a direct consequence of leaving this alone; a
larger annotated sample might reveal a real distinguishing feature, this
one (n=30) doesn't show one.

## Important caveat on the numbers above — read before trusting them

The 1.000 / 0.750 figures are the new classifier re-scored against the
**existing** annotated samples (same reviews Timothy already read and
judged) — not a fresh independent sample. This is a legitimate sanity
check (same move Round 6 made, and the same one its own handoff entry
flagged as less trustworthy than a fresh draw). Concretely:

- The two `precision_app_performance.csv` / `precision_unexplained_deduction.csv`
  files as they stood at the start of this session (0.600 / 0.700, the
  numbers behind the `needs_regex_fix` stamps in the screenshots) are now
  archived as `precision_app_performance_r2.csv` / `precision_unexplained_deduction_r2.csv`.
- **New, unannotated 30-row samples were drawn from the freshly
  reclassified dataset and written to the primary `precision_app_performance.csv`
  / `precision_unexplained_deduction.csv` paths** (`correct` column blank),
  using the existing `sample_for_precision()` — same mechanism the codebase
  already uses for every prior round.
- I did not fill in the `correct` column on the new primary files myself —
  that's real annotation judgment on real customer text and isn't mine to
  invent. `validation_status_table()` will read these as `unvalidated`
  (0 annotated rows) until they're actually annotated, so the Methodology
  page will currently show a step backward in status for both categories
  (from `needs_regex_fix` to `unvalidated`) even though the underlying
  regex genuinely improved. This is the honest state, not a bug — same
  caution the previous handoff itself argued for ("re-run
  `validation_status_table()` immediately after ... before writing it into
  a handoff as final").

**Next step for these two categories:** annotate the 30 fresh rows in each
primary `precision_*.csv` (1 = correctly tagged, 0 = wrong), then reload
Methodology to get the real post-fix precision number.

## Also regenerated this session

- `data/processed/bca_mobile_reviews_classified.csv` — re-run through
  `classify_dataframe()` with the updated rules. Mention counts shifted as
  expected from removed false positives: `app_performance` 688 -> 641,
  `unexplained_deduction` 174 -> 95. Every other category's classification
  logic is untouched — spot-checked all other categories' existing
  precision samples for any accidental TP/FP shift; none found.
- Notebooks (`03_issue_classification.ipynb`, `04_validation.ipynb`,
  `05_prioritization.ipynb`) were **not** re-executed this session — they
  still reflect the pre-Round-7 state. Re-run them before trusting their
  printed output over the CSVs.

## What I did not touch

- No UI/theme changes.
- No changes to any category's rules other than `app_performance` and
  `unexplained_deduction`.
- Recall (the unclassified-negative gap) — out of scope this round, same
  as prior sessions.

---

**Date:** 2026-08-21 (session 3)
**Status:** Full UI/UX redesign — "Customer Intelligence Console" direction,
replacing the earlier "field report" theme. Dashboard is visually verified
in a real browser this time (screenshots + interactive filter checks), not
just AppTest. **The two `needs_regex_fix` categories from the previous
session (`app_performance`, `unexplained_deduction`) are still unfixed —
this session was UI-only and deliberately did not touch classification
logic.** See the previous entry below for that context; nothing about it
changed.

## What happened this session

Rebuilt the visual design system end to end, per a design brief targeting a
"modern banking intelligence dashboard × Voice of Customer platform" feel
instead of the previous warm-paper "field report" look.

**Design system (`app/utils/theme.py`, full rewrite):**
- Cool-neutral palette (`#F5F7FA` bg / `#0A4FA3` + `#1677D2` blues) replacing
  the warm beige/navy field-report theme.
- Inter for all UI text; IBM Plex Mono pulled back to data/timestamps/
  precision numbers only (was applied globally before — the single biggest
  "generic Streamlit project" tell called out in the brief).
- Semantic red/amber/green reserved strictly for severity, trend, and
  validation confidence — nothing else uses them decoratively.
- New shared HTML fragment builders (`page_header`, `tag`, `metric_row`,
  `signal_banner`, `pipeline_flow`) so every page pulls markup from one
  place instead of writing one-off inline HTML per component.
- `app/utils/formatting.py` now derives its color maps from `theme.COLORS`
  instead of duplicating hex values.

**App shell (`app/dashboard.py`):** compact sidebar identity block (mark +
wordmark + "Customer Intelligence" eyebrow) above the nav list, dataset
status ("● Analysis ready · 5,000 reviews") below it — real data, not
invented metrics.

**Pages, in priority order per the brief:**
1. `issue_explorer.py` — rebuilt as an evidence-record view: compact metric
   strip, `st.segmented_control` for rating/sort filters (was
   multiselect + radio), review cards with a rating-severity-colored left
   rail instead of plain white boxes.
2. `overview.py` — added a dominant "top priority signal" banner above the
   KPI row, driven directly off `priority_df.iloc[0]` so it can't drift out
   of sync with the table below it. Priority table restyled with pill tags.
3. `trends.py` — restyled chart chrome and trend-direction rows onto the
   new tokens, transparent chart backgrounds instead of boxed white panels.
4. `methodology.py` — added a horizontal pipeline-flow diagram (Reviews →
   Preprocessing → Classification → Issue signals → Prioritization) above
   the existing written pipeline explanation, as the page's signature
   element.

## Two real bugs found by actually looking at it (not just AppTest)

AppTest and a headless smoke test both passed cleanly, but neither one
catches rendering bugs — only Python exceptions. Screenshotting each page
in a real headless browser surfaced two things AppTest missed entirely:

1. **`st.segmented_control` selected state was Streamlit's default red**,
   not the theme's blue — my first CSS pass targeted
   `[data-testid="stSegmentedControl"] label`, which doesn't exist in this
   Streamlit version (1.62 renders segmented control through
   `[data-testid="stButtonGroup"]` with `button[data-selected="true"]`).
   Same root issue on the multiselect tags in Trends: `[data-baseweb="tag"]`
   is gone too — Streamlit 1.62 moved multiselect off BaseWeb onto
   react-aria, so the real hook is
   `[data-testid="stMultiSelectTagsContainer"] span[data-tag]`. If you're on
   a different Streamlit version, re-inspect the DOM before assuming these
   selectors still match — this library's internal markup is not stable
   across versions and doesn't show up in any changelog most people read.
2. **A literal `</div>` was leaking into every Issue Explorer review card.**
   Root cause, best I could pin down without server-side access to
   Streamlit's client-side markdown renderer: multi-line, deeply-indented
   triple-quoted HTML strings passed to `st.markdown()` get misread as a
   markdown indented code block once real (arbitrary, uncontrolled) review
   text is interpolated in — the same pattern rendered fine elsewhere
   (`signal_banner`, `pipeline_flow`) as long as the interpolated content
   was our own controlled strings. Fixed by rebuilding every dynamic HTML
   fragment as a single unindented line (no embedded newlines at all) and
   HTML-escaping `review_text` before interpolating it. **If you add any
   new `st.markdown(..., unsafe_allow_html=True)` call anywhere in this
   app, follow that same single-line pattern, especially if real review
   text or any other uncontrolled string is going into it** — it's cheap
   insurance against the same bug reappearing somewhere new.

Both are fixed and re-verified with real screenshots (before/after) and one
round of clicking through the Issue Explorer filters interactively (not
just loading the page) to confirm the segmented control's actual filtering
behavior still works under the new styling, not just its appearance.

## Verification this session

- `streamlit.testing.v1.AppTest` on all four pages + the dashboard entry
  point — zero exceptions, before and after the two bug fixes.
- Headless `streamlit run` + `curl` — HTTP 200, clean log.
- Playwright screenshots of all four pages in a real headless browser.
- Interactive check: toggled rating filter chips off/on and switched sort
  order on Issue Explorer, confirmed the review count and card order
  actually updated correctly, not just that the page didn't crash.

## What I did not touch

- No analytical logic changed — `src/*.py`, `data/`, and the notebooks are
  untouched this session.
- Did not fix `app_performance` / `unexplained_deduction` precision — still
  flagged `needs_regex_fix`, exactly as the previous session left them. The
  Methodology page's validation table still surfaces this correctly.
- Did not visually check the app below ~1100px viewport height or on a
  narrow/mobile width — only checked at 1440×1100. The brief asked for
  "reasonably usable, not broken" at smaller sizes; that's unverified.

## Next steps

1. Same open item as last session: fix the `app_performance` and
   `unexplained_deduction` regex, re-validate, re-run
   `validation_status_table()` immediately after to confirm the number
   that lands in the primary CSV matches what was just annotated.
2. Spot-check the app at a narrow/mobile viewport width — this session only
   verified desktop (1440px).
3. If Streamlit gets upgraded, re-inspect the DOM for `stButtonGroup` and
   `stMultiSelectTagsContainer` before assuming the CSS selectors in
   `theme.py` still match — see the bug writeup above.

---


## ⚠️ Read this first: precision numbers in the previous handoff were wrong

The previous handoff's "Final validated precision — all categories" table
does not match what's actually in `data/validation/*.csv` right now. I
re-ran `notebooks/05_prioritization.ipynb` fresh against the committed files
(not from memory, not from the old handoff) and got different numbers for
three categories:

| Category | Previous handoff claimed | Actually in the repo right now |
|---|---|---|
| app_performance | 0.900 (validated) | **0.600 — needs_regex_fix** |
| unexplained_deduction | 0.840 (validated, after Round 6) | **0.700 — needs_regex_fix** |
| device_compatibility | 1.000 (n=5) | 0.833 (n=30 — bigger sample, probably more trustworthy) |

Best guess at what happened: the previous handoff says the Round 6 fix for
`unexplained_deduction` was "verified against the *existing* Round 5
annotations," and also says the round3/round4/round5 files were "saved
back into the repo" — they weren't. `git show --stat` on the last commit
shows only the primary `precision_*.csv` files changed, no round-suffixed
files. Whatever got `unexplained_deduction` to 0.840 and `app_performance`
to 0.900 didn't make it into the file that `validation_status_table()`
actually reads. `app_performance` wasn't even supposed to be touched that
session (it wasn't one of the 3 stuck categories), so it regressing from
0.900 to 0.600 in the committed file is the stranger of the two — worth
checking whether the primary CSV got overwritten by a fresh unannotated
sample at some point without the old annotations carried over.

**I didn't try to fix the regex this session** — that's real classifier
work. The dashboard (below) surfaces this correctly on its own: the
Methodology page reads `validation_status_table()` live, so both categories
show up flagged red as `needs_regex_fix` with a warning banner, not
silently presented as fine.

## What happened this session

1. Reviewed `src/prioritization.py` and `src/analysis.py` — logic is sound,
   no changes needed. Deliberately not a single composite score; tier rules
   are plain if/else so they're auditable (see module docstrings).
2. Re-ran `notebooks/05_prioritization.ipynb` end-to-end against the current
   `bca_mobile_reviews_classified.csv` — ran clean, no errors. This is what
   surfaced the precision mismatch above.
3. Built `app/dashboard.py` from scratch (was 0 bytes). Four pages via
   `st.navigation`/`st.Page`, same pattern as the Retention/RFM dashboard:
   - **Overview & Priority** — KPIs + the live priority table + a
     share-of-negative-reviews bar chart, colored by tier
   - **Trends** — monthly share line chart per issue, trend direction table
   - **Issue Explorer** — pick a category, read the actual review text
     behind it, filter by star rating, sort by recency or helpfulness
   - **Methodology** — pipeline explanation + the live validation status
     table + an explicit warning banner listing any category currently
     below 0.80 precision
4. All four pages verified with `streamlit.testing.v1.AppTest` (no
   exceptions) plus a headless `streamlit run` smoke test (HTTP 200, clean
   log). `use_container_width` calls updated to `width=` (old API is
   deprecated, removal after 2025-12-31).

## Design

"Field report" direction — warm paper background (`#FAF8F4`), navy ink
text, Manrope for headings / IBM Plex Mono for data, restrained blue accent
(`#2453A6`). Signal colors (red/amber/green) reserved for priority tier and
validation status only, so they carry real meaning instead of decorating
everything. Theme lives in `app/utils/theme.py`.

## Architecture

- `app/utils/data_loader.py` (new) — `st.cache_data`-wrapped loaders.
  Computes frequency/trend/validation/priority tables live from the
  committed CSVs on every load — this is intentional, see its docstring.
  Nothing is hardcoded from a notebook run or a handoff doc.
- `app/utils/formatting.py` — label/color/number formatting, no pandas.
- `app/utils/theme.py` (new) — design tokens + one CSS injection.
- `app/components/*.py` — one `render(tables: dict)` function per page.
- `app/dashboard.py` — thin entry point, wires pages via `st.navigation`.

## Files changed this session

- `app/dashboard.py`, `app/components/*.py`, `app/utils/*.py` — dashboard
  built (see above)
- `notebooks/05_prioritization.ipynb` — re-executed in place, outputs now
  reflect current data (including the two `needs_regex_fix` flags)
- This file

**Committed to git this session** — check `git log` if picking this up
fresh; don't assume uncommitted like last time without checking.

## Next steps

1. **Fix `app_performance` and `unexplained_deduction` regex again.** Given
   the mismatch above, first re-confirm what's actually annotated in
   `data/validation/precision_app_performance.csv` and
   `precision_unexplained_deduction.csv` right now (`git show` won't help
   here — the file on disk is the source of truth) before starting a new
   validation round. Don't trust either this handoff or the previous one's
   precision claims over the actual CSV.
2. **Going forward: after any validation round, immediately re-run
   `validation_status_table()`** (or just reload the Methodology page in
   the dashboard) to confirm the number that lands in the primary
   `precision_*.csv` file matches what you think you just annotated, before
   writing it into a handoff as final. That would have caught this
   discrepancy same-session instead of a session later.
3. `ui_ux_regression` still only has 2 total matches in 5,000 reviews — same
   as before, not urgent, worth a regex sanity check eventually.
4. Run `streamlit run app/dashboard.py` locally to eyeball it for real
   (only AppTest + headless smoke-tested here, never visually inspected in
   a browser).
