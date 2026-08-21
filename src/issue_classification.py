"""
Rule-based, multi-label issue classification for BCA Mobile customer reviews.

Chosen over an ML classifier for the same reason word-frequency counting was
chosen over a topic model in 02_exploratory_analysis.ipynb: at this stage the
goal is a transparent, auditable mapping from "this review matched because of
these exact words" rather than a black box. A reviewer of this repo should be
able to read a rule and predict what it will and won't catch.

This is deliberately not perfect recall. Keyword rules will always miss
reviews that describe a problem without using any of the expected words.
That gap is measured and reported honestly in the notebooks, not hidden.

CHANGE LOG (decisions made after reviewing 03's unclassified-negative n-grams
against the full classified dataset — see chat history / notebook 03 findings
for the evidence each change is based on):

- indicator_light_stuck: added "sinyal" as a synonym for lampu/indikator. Many
  customers describe the stuck indicator light as "sinyal" (e.g. "sinyal bagus
  tapi indikator merah terus"), not "lampu"/"indikator". Also added "biru"
  (blue) as a third observed indicator state, previously undocumented.
- app_performance: added patterns for "app won't open/can't be accessed"
  (distinct concept from "lemot"=slow), plus "trouble" and "gangguan" as
  generic failure terms.
- customer_service: added "susah dihubungi/direspon" (CS unreachable).

Net effect measured against the full 5,000-row dataset: unclassified negative
reviews dropped from 48.6% to 41.8% (157 reviews recovered). Positive-group
match rate rose from 7.7% to 9.7%, but every newly-matched positive review was
manually checked and genuinely describes the problem — this reflects real
rating-text mismatch in the source data (customers who rate the overall
experience/brand highly while still describing an incident), not the rule
firing on unrelated context. See notebook 03 for the manual check.

ROUND 2 (based on 04_validation.ipynb precision/recall results on the fully
annotated samples):

- unexplained_deduction (precision 0.433 -> targeted fix): 13 of 17 false
  positives were reviews describing a SPECIFIC failed QRIS/transfer where
  balance was deducted — i.e. they match transaction_failed_balance_deducted's
  definition, not this one ("not tied to a specific attempted transaction").
  Added ISSUE_EXCLUDES entries so the generic "kepotong/terpotong/potongan"
  match is suppressed whenever "gagal" or a transaction-context word
  (qris/transfer/top up/pembayaran) appears nearby. Reviewed the correct=1
  rows separately to confirm they consistently do NOT mention those words —
  they instead describe admin-fee timing issues, "tiba-tiba"/self-triggered
  loss, or a missing mutasi entry, which the remaining positive rules still
  catch.
- login_otp_access (precision 0.600 -> targeted fix): 3 of 12 false positives
  were actually face_verification_failure (login blocked specifically by face
  verification, already its own category) — added an exclude for
  "verifikasi wajah/muka" nearby. 1 was actually device_compatibility
  ("gak bisa diakses ... hp versi lama") — added an exclude for
  device-compatibility language. 2 were bare "registrasi" mentions with no
  actual OTP/access failure described — narrowed that rule to require
  co-occurrence with otp/kode akses/pulsa rather than firing on any mention
  of "registrasi". The remaining ~5 false positives (a feature suggestion, a
  sarcastic rhetorical question, ambiguous new-phone complaints) didn't share
  a generalizable pattern distinct enough to fix without risking new false
  positives elsewhere — left as known residual noise, worth a second
  annotation pass after this change lands.
- maintenance_downtime (precision 0.767 -> targeted fix): 1 false positive
  was a negated mention ("tidak ada pemeliharaan..." = NO maintenance) that
  the bare keyword match couldn't distinguish — added a negation exclude.
  2 more were QRIS-failure narratives where "maintenance" was only cited as
  BCA's excuse, with the review's actual subject being the failed
  transaction — added the same transaction-context exclude used for
  unexplained_deduction. The remaining 4 (an inconsistent-looking maintenance
  timing complaint, a rhetorical jab, a mostly-positive review with a minor
  critique, a vague guidance complaint) were left alone rather than force-fit
  a rule to flip a single annotator judgment call.
- device_compatibility (recall gap 20% in the blind sample, i.e. 10/50
  unclassified-negative reviews were actually this category): the existing
  rules required the literal word "kompatibel" (or close misspellings) or the
  phrase "versi hp/aplikasi". Most misses instead said "gak bisa update /
  download", named a specific misspelling ("kompetible", "downlod"), or said
  "hp jadul" (old phone) without ever using "kompatibel". Added patterns for
  all three. NOTE: broadening was not re-validated with a fresh precision
  sample — recommend pulling a new precision_device_compatibility.csv sample
  and re-running 04's scoring cells before fully trusting this category's
  updated count.
- app_performance (recall gap 30%, largest of any category): two silent
  misses were typo/suffix gaps in the EXISTING rules rather than missing
  concepts — "ganguan" (missing one "g", vs. the rule's "gangguan") and
  "errornya" (the old \\berror\\b required a boundary right after the word,
  which Indonesian suffixes like "-nya" break). Fixed both without changing
  what the rules are trying to catch. Also added a pattern for "keluar
  sendiri/terus" and "force close" (app self-closing/crashing), a distinct
  failure mode not covered by "lemot" (slow) or the existing "can't open"
  patterns. Same caveat as device_compatibility: not yet re-validated with a
  fresh precision sample.

Net effect of Round 2 on the classified dataset (n=5,000): see
04_validation.ipynb re-run and 03's summary table for before/after counts.

ROUND 3 (fresh precision sample for unexplained_deduction still scored ~0.27,
i.e. Round 2's fix was incomplete — hand-checked against the actual 30-row
sample in data/validation/precision_unexplained_deduction.csv before writing
any new pattern, same as Round 1/2):
- unexplained_deduction: the Round 2 exclude only covered the
  "kepotong/terpotong/potongan" trigger word. The category's OTHER positive
  trigger ("saldo hilang/berkurang") was never added to the exclude, so any
  review phrased "qris gagal ... saldo berkurang" (instead of "...kepotong")
  still slipped through — roughly 8 of the 22 fresh false positives were
  exactly this. Widened every exclude to cover both trigger families.
- Found two more false-positive patterns the Round 2 fix didn't anticipate:
  (1) a top-up/purchase that never arrived but still got charged
  ("belum/gak masuk/kirim") — same "specific failed transaction" story as the
  gagal-family, just phrased without the literal word "gagal"; (2) a named,
  understood fee complaint ("biaya admin bulanan 2x", "biaya cetak fisik") —
  the reviewer knows exactly why the money left, they're complaining about
  the amount/frequency, which isn't "unexplained" by this category's own
  definition. Added excludes for both.
- Two single-row edge cases handled narrowly rather than with a broad rule:
  a fraud/scam report ("kena kasus penipuan, saldo kekuras") is a security
  problem, not a technical glitch — different root cause, doesn't belong in
  either category as currently scoped; a review primarily complaining about
  unhelpful customer service, where the deduction was just background
  context, belongs under customer_service.
- Left the `mengendap` positive-trigger word itself alone but excluded
  "biaya mengendap" specifically — in the sample it only ever appeared as
  BCA's named dormant-account fee, i.e. the opposite of "unexplained."

Checked the new exclude logic against all 30 rows of the actual Round-2
sample by hand before applying it (18/30 -> 30/30 agreement with a manual
read) but this is still Claude's read, not Timothy's — the regenerated
precision_unexplained_deduction.csv below still needs a real independent
annotation pass before this category's numbers go in front of anyone.

VALIDATION HISTORY — unexplained_deduction precision, all numbers from
Timothy's own annotations in data/validation/ (Round 3 onward; Rounds 1-2
above predate that discipline and should be read as directional only):
  Round 3: 0.433 -> 0.633  (fixed literal "gagal"-only detection; missed
           synonyms eror/batal/gabisa and negation abbreviations tdk/g)
  Round 4: 0.633 -> 0.567  (fixed those synonyms, but a fresh sample showed
           MORE synonyms — pending/belum berhasil/tidak diproses/typos.
           Precision regressed: synonym-chasing was not converging.)
  Round 5: 0.567 -> 0.700  (abandoned synonym-chasing entirely. Rewrote the
           exclude to detect WHETHER A TRANSACTION TYPE IS NAMED — qris,
           transfer, top-up, purchase, etc. — near the deduction word,
           regardless of how the failure itself is phrased. This is the
           actual distinguishing signal between this category and
           transaction_failed_balance_deducted.)
  Round 6: 0.700 -> 0.840  (same rework, closed two remaining gaps found in
           the Round 5 sample: generic "transaksi gagal" wording with no
           named type, and "qris" typos/spacing. Scored against the
           existing Round 5 annotations, not a fresh sample — re-ran the
           updated classifier over those same 30 already-labeled reviews
           and confirmed every row it dropped had a human-given correct=0.)
  FINAL (all three previously-failing categories, Timothy-annotated):
    unexplained_deduction: 0.840 | login_otp_access: 0.967 |
    maintenance_downtime: 0.833
  Classification is considered closed as of Round 6. Any future precision
  drift should be caught by re-running notebook 04 against a fresh sample,
  not assumed from this history.
"""

import re

import pandas as pd


ISSUE_RULES = {
    "transaction_failed_balance_deducted": [
        r"\b(qris|top\s?up|transfer|isi\s+pulsa|pembayaran)\b.{0,50}\b(gagal|kepotong|ke\s?potong|terpotong|potong)",
        r"\b(gagal|kepotong|ke\s?potong|terpotong|potong)\b.{0,50}\b(qris|top\s?up|transfer|pulsa|pembayaran)\b",
        r"transaksi\s+(qris\s+)?gagal.{0,40}saldo",
        r"saldo.{0,20}(ke\s?potong|terpotong).{0,40}(gagal|tidak\s+(terkirim|berhasil|masuk))",
        r"(gagal|tidak\s+(terkirim|berhasil)).{0,40}saldo.{0,20}(ke\s?potong|terpotong)",
    ],
    "indicator_light_stuck": [
        r"\bindikator\b",
        r"\blampu\b.{0,20}(merah|hijau|ijo|biru)",
        r"(merah|hijau|ijo|biru).{0,20}\blampu\b",
        # "sinyal" used as a synonym for the indicator light — contrast pattern
        # "sinyal bagus/kuat tapi [merah/hijau/biru] terus"
        r"\bsinyal\b.{0,30}(merah|hijau|ijo|biru)",
        r"(merah|hijau|ijo|biru).{0,30}\bsinyal\b",
        r"warna\s+sinyal",
    ],
    "unexplained_deduction": [
        r"\bsaldo\b.{0,25}(hilang|ilang|berkurang)",
        r"\b(potongan|kepotong|ke\s?potong|terpotong)\b",
        r"uang.{0,25}(hilang|ilang|kemana)",
        r"\bmutasi\b.{0,25}(gak\s+ada|tidak\s+ada|nggak\s+ada)",
        r"mengendap",
    ],
    "face_verification_failure": [
        r"ver[ei][fv]ikasi.{0,20}(wajah|muka|diri)",
        r"\bkamera\b.{0,20}verifikasi",
    ],
    "login_otp_access": [
        r"\b(gak|ga|gk|nggak|tidak)\s+bisa\s+(login|masuk|di\s?akses)\b",
        r"\botp\b",
        r"\bganti\s+(nomor\s+)?sim\b",
        r"kode\s+akses",
        r"\blogin(nya)?\b.{0,25}(ribet|susah|sulit|dipersulit|peribet)",
        # narrowed from a bare \bregistrasi\b (fired on any re-registration
        # mention, including ones with no actual OTP/access failure — see
        # ROUND 2 change log) to require it co-occur with the OTP/access
        # mechanism specifically
        r"registrasi.{0,30}\b(otp|kode\s+akses|pulsa)\b",
        r"\b(otp|kode\s+akses|pulsa)\b.{0,30}registrasi",
    ],
    "app_performance": [
        r"\blemot\b",
        r"\b(error|eror)",  # no trailing \b: catches suffixed forms like "errornya"
        r"\brestart\b",
        r"uninstall|instal\s+ulang|hapus\s+download",
        # app won't open / can't be accessed at all (distinct from "lemot"=slow)
        r"(gak|ga|gk|nggak|tidak)\s+bisa\s+(di\s?)?buka",
        r"susah\s+(di\s?)?buka",
        r"susah\s+diakses",
        r"\btrouble\b",
        r"\b(gangguan|ganguan)\b",  # "ganguan" is a common one-g typo
        # app self-closing / crashing — distinct failure mode from "lemot"
        # or "can't open at all"
        r"\bkeluar\s+(sendiri|terus)\b",
        r"\bkembali\s+sendiri\b",
        r"force\s*close",
    ],
    "maintenance_downtime": [
        r"pemeliharaan",
        r"\bmaintenance\b",
        r"perbaikan\s+sistem",
    ],
    "customer_service": [
        r"\bcs\b",
        r"halo\s+bca",
        r"\bkomplain\b",
        r"\blapor(an)?\b",
        r"call\s*center",
        r"\bcabang\b",
        # CS unreachable / unresponsive
        r"susah\s+(di\s?)?hubungi",
        r"susah\s+direspon",
    ],
    "ui_ux_regression": [
        r"tampilan.{0,40}(jelek|bingung|ribet)",
        r"\bikon\b",
        r"setelah\s+update.{0,30}(jelek|ribet|bingung|susah)",
    ],
    "device_compatibility": [
        # ROUND 3 fix: the previous version of this pattern ("kompa?te?bel")
        # had a typo and never actually matched the standard spelling
        # "kompatibel" — only obscure misspellings. Confirmed by testing the
        # literal word "kompatibel" against both lines below before the fix:
        # neither matched. This was likely undercounting the category since
        # before Round 2 even started.
        r"(tidak|ga|gak|nggak)\s+komp?[ae]t[ei]b(el|le)",
        r"komp?[ae]t[ei]b(el|le)|kopatibel",
        r"versi\s+(hp|aplikasi)",
        # "can't update/download the app" — in this dataset almost always
        # means the OS/device is too old to install the new version, which
        # is the actual device_compatibility story even when the review
        # never says the word "kompatibel" (see ROUND 2 change log)
        r"(tidak|ga|gak|nggak)\s+bisa\s+(di\s?)?(update|download|downlod)\b",
        r"\b(update|download|downlod)\b.{0,20}(tidak|ga|gak|nggak)\s+bisa",
        r"\bhp\b.{0,15}\bjadul\b|\bjadul\b.{0,15}\bhp\b",
    ],
}

# Patterns that, if found, SUPPRESS a category match even though one of its
# ISSUE_RULES patterns fired. Used for cases where two categories' keyword
# rules legitimately overlap in vocabulary but the review is clearly about
# only one of them once you read the surrounding context — see the ROUND 2
# entries in the module docstring for the specific evidence behind each one.
# This is still meant to be readable top-to-bottom like ISSUE_RULES: each
# exclude pattern says exactly what context suppresses the match, no hidden
# scoring or weighting.
ISSUE_EXCLUDES = {
    "unexplained_deduction": [
        # ROUND 5 — full rework, not another synonym patch.
        #
        # Rounds 1-4 tried to detect every way a review can say "I attempted
        # a transaction and it failed/errored/got cancelled/is pending" —
        # gagal, eror, batal, ga bisa, tidak berhasil, belum berhasil, tidak
        # diproses, pending, plus typos and abbreviations of all of those.
        # Precision oscillated (0.433 -> 0.633 -> 0.567) instead of
        # converging: closing one synonym gap kept revealing another,
        # because the review text can describe "failed" in effectively
        # unlimited colloquial ways.
        #
        # New approach: stop trying to detect the failure wording at all.
        # Instead, detect whether the review names a SPECIFIC transaction
        # TYPE (QRIS, transfer, top-up, a purchase, a bill payment...).
        # Almost every false positive in every round mentioned one of these
        # regardless of how the failure itself was phrased — that's the
        # actual signal, not the failure verb. If a transaction type is
        # named near the deduction word, it's a specific-attempt story ->
        # transaction_failed_balance_deducted's territory, not this
        # category's ("balance moved with no stated transaction at all").
        # Window set to 500 (dataset's max review length) rather than a
        # tighter number — in a long rambling review the transaction keyword
        # and the deduction word can be far apart, and these keywords are
        # specific enough (qris/qr/va/transfer/beli/bayar/pulsa/token) that
        # requiring proximity added a failure mode without adding precision.
        # "qr" added alongside "qris" — several reviews shorten it.
        # ROUND 6: after the ROUND 5 rework, the last false positives all
        # named the transaction generically ("transaksi gagal") instead of
        # a specific type (qris/transfer/beli/...), or misspelled "qris" as
        # "qiris"/"q ris" — neither was in the keyword list.
        #
        # NOTE: excluding on bare "transaksi" (without requiring "gagal")
        # was tried first and rejected — it wrongly excluded genuine
        # unexplained_deduction cases like "ada transaksi yang tidak saya
        # lakukan, saldo berkurang" (an unauthorized-transaction complaint,
        # which IS this category's story). Requiring "gagal" specifically
        # keeps that case tagged while still catching the actual FPs, all of
        # which used "transaksi gagal" verbatim — checked against the
        # ROUND 5 annotated sample (not a fresh one) before adding.
        # ROUND 7 — the ROUND 6 version of this exclude required the literal
        # word "transaksi" (correctly spelled) plus "gagal" specifically.
        # A fresh precision sample (data/validation/precision_unexplained_deduction.csv,
        # scored 0.700) showed two gaps: (1) "transaksi" typo'd/transposed
        # ("tramsaksi", "tarnsaksi") never matched the literal pattern, and
        # (2) reviews describing the same "attempted transaction, no named
        # type, generic failure" story with "gangguan" or "pending" instead
        # of "gagal" ("transaksi sedang gangguan tp saldo kepotong", "pending
        # mulu... saldo udah kepotong") weren't covered at all since "gagal"
        # was the only failure word recognized. Dropping the "transaksi"
        # requirement and widening the failure-word set to gagal/gangguan/
        # pending fixes both without re-introducing the synonym-chasing loop
        # from Rounds 3-4: checked against every correct=1 row in the current
        # sample first, and none of them use gagal/gangguan/pending near a
        # deduction word, so this doesn't touch any confirmed true positive.
        r"\b(gagal|gangguan|pending)\b.{0,120}\b(kepotong|ke\s?potong|terpotong|potongan|potong|hilang|ilang|berkurang)\b",
        r"\b(kepotong|ke\s?potong|terpotong|potongan|potong|hilang|ilang|berkurang)\b.{0,120}\b(gagal|gangguan|pending)\b",
        r"\b(qris|qr|q\s*ris|qiris|va|virtual\s*account|transfer|\btf\b|top\s*up|topup|beli|pembelian|bayar|pembayaran|pulsa|token|tarik\s*tunai)\b.{0,500}\b(kepotong|ke\s?potong|terpotong|potongan|potong|hilang|ilang|berkurang)\b",
        r"\b(kepotong|ke\s?potong|terpotong|potongan|potong|hilang|ilang|berkurang)\b.{0,500}\b(qris|qr|q\s*ris|qiris|va|virtual\s*account|transfer|\btf\b|top\s*up|topup|beli|pembelian|bayar|pembayaran|pulsa|token|tarik\s*tunai)\b",
        # a named, understood fee ("biaya admin", "potongan bulanan") is an
        # explained deduction — the complaint is the amount/frequency, not
        # "where did my money go"
        r"(biaya|potongan)\s*.{0,10}(admin|bulanan|tahunan|cetak|penutupan|kartu)",
        r"biaya.{0,20}mengendap",
        # fraud/scam is a different root cause (security), not a technical
        # "unexplained" glitch — shouldn't be folded into this category
        r"(penipuan|kena\s+tipu|di\s?tipu|scam)",
        # reviews primarily complaining about unhelpful customer service,
        # where the deduction is just background context, belong under
        # customer_service instead
        r"\bcs\b.{0,60}(berbelit|solusi|respon)",
    ],
    "login_otp_access": [
        # login blocked specifically by face verification is
        # face_verification_failure's story
        r"ver[ei][fv]ikasi.{0,20}(wajah|muka)",
        # "can't get in" caused by device/version incompatibility is
        # device_compatibility's story (same ROUND 3 typo fix as the
        # positive rule — "kompa?te?bel" never matched "kompatibel" itself)
        r"(tidak|ga|gak|nggak)\s+komp?[ae]t[ei]b(el|le)",
        r"versi\s+(hp|aplikasi).{0,20}(lama|jadul|tidak\s+mendukung)",
        # "can't get in" caused by the app being slow/crashing is
        # app_performance's story, not a credential/access problem
        r"(lemot|force\s*close).{0,40}(gak|ga|gk|tidak|nggak)\s+bisa\s+masuk",
        r"(gak|ga|gk|tidak|nggak)\s+bisa\s+masuk.{0,40}(lemot|force\s*close)",
    ],
    "maintenance_downtime": [
        # negation: "tidak ada pemeliharaan" means there is NO maintenance —
        # the bare keyword match can't tell affirmation from negation on
        # its own
        r"(tidak|gak|ga|nggak)\s+ada\b.{0,15}\b(pemeliharaan|maintenance)\b",
        # "maintenance" cited only as BCA's excuse inside a QRIS-failure
        # narrative — the review's actual subject is the failed transaction
        r"transaksi\s+(qris\s+)?gagal.{0,40}saldo",
    ],
    # ROUND 7 — app_performance precision sample (n=30) scored 0.600, the
    # worst of any category. Read all 12 false positives by hand
    # (data/validation/precision_app_performance.csv) before writing
    # anything below. One pattern deliberately NOT here: several false
    # positives mention the indicator light (lampu/indikator/sinyal + a
    # color) alongside a generic trigger word like "lemot" or "gangguan" —
    # but so do several CONFIRMED TRUE POSITIVES in the same sample (e.g.
    # "Sekarang BCA mobile sering eror, indikator merah terus...",
    # correct=1). There's no regex-visible difference between those two
    # cases; an exclude broad enough to catch the false positives would
    # also silently flip real true positives to false negatives. Per this
    # module's own precedent (see the single-row edge cases left alone in
    # the unexplained_deduction history above), that's left as genuine
    # ambiguity rather than force-fit a rule.
    "app_performance": [
        # "gak bisa dibuka" caused by an old/unsupported device is
        # device_compatibility's story, not a generic performance one —
        # same distinction already drawn for login_otp_access above.
        r"(tidak|ga|gak|nggak)\s+bisa\s+(di\s?)?buka.{0,200}(versi\s+lama|hp.{0,15}(lama|jadul)|(ga|gak|tidak|nggak)\s+support)",
        r"(versi\s+lama|hp.{0,15}(lama|jadul)|(ga|gak|tidak|nggak)\s+support).{0,200}(tidak|ga|gak|nggak)\s+bisa\s+(di\s?)?buka",
        # a named transaction type failing with the balance deducted is
        # transaction_failed_balance_deducted's / unexplained_deduction's
        # story — "gangguan"/"error" here is describing that failure, not a
        # standalone performance complaint.
        r"\b(qris|qr|transfer|top\s*up|topup|beli|pembelian|bayar|pembayaran|pulsa|token)\b.{0,300}\b(kepotong|ke\s?potong|terpotong|potongan|potong)\b",
        r"\b(kepotong|ke\s?potong|terpotong|potongan|potong)\b.{0,300}\b(qris|qr|transfer|top\s*up|topup|beli|pembelian|bayar|pembayaran|pulsa|token)\b",
        # negation: "ga pake lemot (lagi)" means NO LONGER laggy — a
        # positive review, not a complaint. Bare \blemot\b can't tell
        # affirmation from negation on its own (same class of bug as the
        # maintenance_downtime negation exclude above).
        r"\b(ga|gak|tidak|nggak)\s+(pake|pakai)\s+lemot\b",
        # "jangan lemot ya" is a closing wish/hope, not a description of an
        # actual performance problem occurring right now.
        r"\bjangan\s+lemot\b",
    ],
}

_COMPILED_RULES = {
    issue: [re.compile(p, re.IGNORECASE) for p in patterns]
    for issue, patterns in ISSUE_RULES.items()
}

_COMPILED_EXCLUDES = {
    issue: [re.compile(p, re.IGNORECASE) for p in patterns]
    for issue, patterns in ISSUE_EXCLUDES.items()
}


def classify_issues(text: str) -> list:
    """Return every issue category whose pattern matches this review text.

    A category is skipped if any of its ISSUE_EXCLUDES patterns also match —
    see the module docstring's ROUND 2 notes for why each exclude exists.
    """
    text = str(text)
    matched = []
    for issue, patterns in _COMPILED_RULES.items():
        if not any(p.search(text) for p in patterns):
            continue
        excludes = _COMPILED_EXCLUDES.get(issue, [])
        if any(p.search(text) for p in excludes):
            continue
        matched.append(issue)
    return matched


def classify_dataframe(df: pd.DataFrame, text_col: str = "review_text") -> pd.DataFrame:
    """Add issues / issue_count / has_issue columns to a copy of df.

    Centralizes the pattern used in 03_issue_classification.ipynb so notebooks
    don't each re-derive these three columns by hand.
    """
    out = df.copy()
    out["issues"] = out[text_col].apply(classify_issues)
    out["issue_count"] = out["issues"].apply(len)
    out["has_issue"] = out["issue_count"] > 0
    return out


def build_issue_summary(df: pd.DataFrame, rating_col: str = "rating",
                         rating_group_col: str = "rating_group") -> pd.DataFrame:
    """Per-category count, share of all reviews, negative-rate, and avg rating.

    Expects df already has an "issues" column (list of category strings per
    row) — e.g. from classify_dataframe(). Mirrors the summary table built in
    03_issue_classification.ipynb so it isn't hand-rebuilt in every notebook
    that needs it (03, 04, and later the dashboard).
    """
    rows = []
    for issue in ISSUE_RULES:
        matched = df[df["issues"].apply(lambda tags: issue in tags)]
        rows.append({
            "issue": issue,
            "total_mentions": len(matched),
            "pct_of_all_reviews": len(matched) / len(df) if len(df) else float("nan"),
            "pct_negative": (matched[rating_group_col] == "negative").mean() if len(matched) else float("nan"),
            "avg_rating": matched[rating_col].mean() if len(matched) else float("nan"),
        })

    return (
        pd.DataFrame(rows)
        .sort_values("total_mentions", ascending=False)
        .reset_index(drop=True)
    )