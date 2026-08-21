# BCA Mobile Customer Voice Analytics

An end-to-end **customer voice analytics and issue-prioritization system** built from Google Play reviews of BCA Mobile.

The project turns unstructured customer reviews into **auditable issue signals**, validates the classification rules against manually reviewed samples, tracks how issue prevalence changes over time, and surfaces which problems deserve attention first.

The analysis answers three practical questions:

1. **What problems are BCA Mobile customers actually reporting?**
2. **Which problems appear most often among negative reviews, and are they getting worse?**
3. **Which issues should be prioritized based on frequency, trend, financial impact, and classification confidence?**

The project deliberately avoids treating sentiment as the final answer. Instead, it focuses on **specific customer problems that can be inspected, validated, and acted on**.

**📊 [View the live interactive dashboard](YOUR_STREAMLIT_URL_HERE)**

Built with **Python, pandas, scikit-learn, Streamlit, Plotly, and rule-based text classification**.

---

## Business Problem

App-store ratings are useful as a high-level signal, but a rating alone does not tell a product team **what went wrong**.

A 1-star review might describe:

* a failed transaction where the balance was deducted,
* an app that crashes or cannot be opened,
* an OTP or login problem,
* a verification failure,
* a stuck BCA Mobile indicator,
* device compatibility problems,
* maintenance or downtime,
* customer-service friction,
* or a UI/UX problem.

The business question is therefore:

> **Which customer problems deserve attention first, and how confident should we be in the evidence behind each problem?**

Rather than producing a black-box sentiment score or a single opaque priority score, this project keeps the evidence visible:

**issue frequency → negative-review share → trend → validation confidence → priority tier**

That makes the resulting recommendations easier to inspect and challenge.

---

## Key Findings

### 1. The dataset contains 5,000 customer reviews covering May–August 2026

The committed classified dataset contains exactly **5,000 reviews**, with review dates spanning **May 1, 2026 to August 18, 2026**. Each record includes rating, review date, review text, helpfulness, rating group, detected issue labels, issue count, and whether at least one issue was detected.

The data is therefore structured not only for exploratory analysis, but also for tracing individual customer complaints back to the underlying review text.

**Business implication:** A review-level evidence trail makes the issue rankings more defensible than reporting aggregate counts without showing the underlying customer language.

---

### 2. Issue classification is intentionally transparent rather than black-box

The project uses **rule-based, multi-label issue classification** rather than an ML text classifier.

A single review can belong to multiple categories, because one complaint can describe more than one problem. The classifier contains explicit regex rules for categories such as:

* `transaction_failed_balance_deducted`
* `indicator_light_stuck`
* `unexplained_deduction`
* `face_verification_failure`
* `login_otp_access`
* `app_performance`
* `maintenance_downtime`
* `customer_service`
* `ui_ux_regression`
* `device_compatibility`

The reason for this choice is deliberate: a reviewer can read a rule and understand **why a review matched**, rather than having to trust an opaque model.

The approach does have an important trade-off: keyword-based rules can miss complaints that describe a problem without using the expected vocabulary. The project therefore treats recall gaps as a known limitation instead of claiming perfect coverage.

**Business implication:** The classification layer is explainable enough to support review, debugging, and stakeholder challenge.

---

### 3. The project prioritizes issues using explicit business rules rather than a black-box score

The prioritization layer combines:

* issue frequency,
* share of negative reviews,
* trend direction,
* validation status,
* and whether an issue has direct financial consequences.

Two categories receive explicit financial-priority treatment:

* **Transaction failed + balance deducted**
* **Unexplained deduction**

An issue becomes **High priority** when it is sufficiently prevalent and either has financial impact or is trending upward. Medium and Low tiers are assigned using the same readable rules.

The system intentionally avoids collapsing these dimensions into a single weighted score because that could hide the difference between:

> **frequent but unvalidated**

and

> **less frequent but strongly validated and financially consequential**

**Business implication:** The priority ledger is designed to answer *why* an issue is ranked highly, not just *what* its score happens to be.

---

### 4. Validation is treated as part of the analysis, not an afterthought

The repository contains dedicated validation samples for the issue categories, including precision samples and recall-gap samples. The prioritization pipeline reads these validation files and labels categories as:

* `validated`
* `partially_validated`
* `needs_regex_fix`
* `unvalidated`

A category below the project's **0.80 precision threshold** is explicitly flagged rather than being presented as trustworthy.

The current repository state also documents an important example of this discipline: after the latest classifier changes, fresh 30-row samples for `app_performance` and `unexplained_deduction` were created but intentionally left unannotated. Until those reviews receive fresh human labels, the dashboard treats them as **unvalidated** rather than inventing a precision number.

**Business implication:** An issue count with uncertain classification quality is surfaced as uncertain instead of being presented as established fact.

---

### 5. The latest classification work materially reduced two sources of false positives

The latest classifier revision regenerated the 5,000-row dataset and reduced the number of reviews tagged with:

| Issue                     | Earlier Count | Current Count |
| ------------------------- | ------------: | ------------: |
| **App Performance**       |           688 |       **641** |
| **Unexplained Deduction** |           174 |        **95** |

The change was targeted at false-positive patterns rather than indiscriminately broadening the rules. The repository documents examples including failed transactions being confused with unexplained deductions, unsupported devices being confused with app-performance complaints, and negated phrases such as “ga pake lemot” being incorrectly treated as active performance problems.

**Business implication:** The classification pipeline is being improved through evidence-driven rule refinement rather than simply maximizing the number of tagged reviews.

---

### 6. The analysis treats trend as a change in issue share, not raw mention count

Monthly issue trends are calculated using the **share of that month's reviews** mentioning each issue rather than simply comparing raw counts.

This matters because review volume itself can vary over time, especially in app-store data where newer reviews may be overrepresented. The trend logic therefore compares the average issue share in the first half of the observation window with the second half.

An issue is classified as:

* **Increasing** when relative change is above 20%
* **Decreasing** when relative change is below -20%
* **Stable** otherwise
* **Insufficient data** when fewer than four months are available

The project intentionally uses this simple comparison rather than fitting a regression model because the dataset covers only a short time window and some issue categories contain relatively few observations.

**Business implication:** The trend signal is simple enough for a stakeholder to inspect and reproduce directly from the monthly table.

---

## Business Recommendations

Recommendations should be driven by the evidence ledger rather than by raw issue volume alone.

| Signal                              | Situation                                                                     | Priority            | Recommended Action                                                    | Objective                                          |
| ----------------------------------- | ----------------------------------------------------------------------------- | ------------------- | --------------------------------------------------------------------- | -------------------------------------------------- |
| **Financial-impact issues**         | Failed transactions or deductions directly affect customer money              | **Critical / High** | Investigate root causes and prioritize engineering fixes              | Reduce high-severity financial incidents           |
| **Increasing issues**               | Issue share is materially higher in the later half of the observation window  | **High**            | Investigate recent releases, infrastructure, or process changes       | Prevent emerging problems from becoming persistent |
| **High-frequency validated issues** | Problem appears repeatedly and classification confidence is established       | **High**            | Prioritize product/process remediation                                | Improve the largest recurring customer pain points |
| **Medium recurring issues**         | Issue is frequent enough to matter but not increasing or financially critical | **Medium**          | Monitor, investigate root cause, and evaluate UX/process improvements | Prevent gradual accumulation of customer friction  |
| **Unvalidated / low-volume issues** | Evidence exists but classification confidence or sample size is insufficient  | **Low / Monitor**   | Collect more annotations before making strong claims                  | Avoid investing based on noisy issue counts        |

The most important operational principle is:

> **Do not prioritize solely because an issue is common. Prioritize based on frequency, direction, business consequence, and confidence in the classification.**

---

## Methodology

The project follows a reproducible pipeline:

```text
Google Play Reviews
        ↓
Data Cleaning & Audit
        ↓
Rating / Review Structuring
        ↓
Rule-Based Multi-Label Classification
        ↓
Issue Frequency Analysis
        ↓
Monthly Issue Trend Analysis
        ↓
Manual Validation
        ↓
Priority Tiering
        ↓
Interactive Streamlit Dashboard
```

### Data Cleaning

The repository includes dedicated cleaning and audit modules before issue analysis.

The goal is to preserve the original review evidence while standardizing the fields needed for downstream analysis.

The processed dataset contains:

```text
review_id
rating
review_date
review_text
thumbs_up
review_length
rating_group
issues
issue_count
has_issue
```

The final processed dataset contains **5,000 review records**.

---

### Rating Grouping

Reviews are grouped into positive, neutral, and negative categories based on their star rating.

The dashboard then uses the **negative-review population as a key denominator** for issue prioritization.

This answers a more actionable question than simply asking how common an issue is overall:

> **Among customers who are already unhappy, how often does this issue appear?**

The issue-frequency function explicitly reports both:

* share of all reviews
* share of negative reviews

and also tracks the proportion of issue-tagged reviews coming from 1–2 star reviews as a sanity check.

---

### Issue Classification

Classification is multi-label.

A review may be tagged with more than one issue when multiple problems are present.

For example, a review can simultaneously describe:

```text
indicator_light_stuck
+
app_performance
```

rather than being forced into a single category.

This is important because customer complaints frequently contain several related problems.

---

### Validation

Validation uses manually annotated samples stored in:

```text
data/validation/
```

The repository contains precision samples for multiple categories and recall-gap samples for identifying cases where the classifier failed to assign an issue.

Precision is calculated from the manually reviewed sample and compared against the project's **0.80 threshold**.

Categories below that threshold are explicitly marked `needs_regex_fix` rather than silently treated as reliable.

---

### Issue Frequency

For every issue category, the project calculates:

* number of mentions
* share of all reviews
* share of negative reviews
* percentage originating from 1–2 star reviews

Because a review can contain multiple issue tags, issue counts **do not necessarily sum to the total number of reviews**.

---

### Trend Analysis

Issue trends are calculated from monthly issue share.

The analysis compares:

```text
First half of observation window
vs.
Second half of observation window
```

and classifies the resulting direction using a ±20% relative-change threshold.

The project deliberately avoids regression-based trend modeling because the observation window is short and some issue categories have small sample sizes.

---

### Priority Logic

Priority tiers are generated from readable rules rather than an opaque composite score.

The core logic is:

```text
High
= sufficiently frequent AND
  (financially consequential OR increasing)

Medium
= sufficiently frequent but not High

Low
= below the frequency threshold
```

The current minimum negative-review-share threshold is **3%**.

Validation status is displayed separately so that a high-priority category can still be visibly marked as provisional when its classification has not yet been adequately confirmed.

---

## Dataset

**Source:** Google Play reviews for the BCA Mobile application.

### Scope Used

* **5,000 reviews**
* **May 1, 2026 – August 18, 2026**
* Review text and star rating
* Review date
* Thumbs-up / helpfulness count
* Review length
* Rule-based issue labels
* Issue count
* Rating group

The processed dataset is committed at:

```text
data/processed/bca_mobile_reviews_classified.csv
```

### Important Dataset Note

This project is based on **user-generated Google Play reviews**, not internal BCA operational, transaction, or customer-service data.

The findings therefore describe what customers choose to report publicly in app-store reviews. They should not be interpreted as a complete representation of all BCA Mobile incidents or the entire customer base.

---

## Dashboard

The project includes a four-page Streamlit dashboard designed around a **Customer Intelligence / Voice of Customer** workflow.

### Overview & Priority

The landing page answers:

> **What should be looked at first?**

It provides:

* total review volume
* negative-review volume
* high-priority issue count
* validation warnings
* rating distribution
* priority ledger
* share of negative reviews by issue

The top-priority callout is generated directly from the live priority table so that the headline and the detailed ledger cannot drift apart.

---

### Trends

The Trends page shows:

* monthly issue share
* issue direction
* increasing / decreasing / stable classification
* comparisons across the observation window

The trend calculations are generated from the current review dataset rather than copied from a manually maintained summary.

---

### Issue Explorer

The Issue Explorer is the **customer evidence layer**.

For a selected issue, users can inspect:

* total mentions
* share of negative reviews
* share originating from 1–2 star reviews
* issue definition
* actual review text
* rating
* date
* helpfulness
* filtering and sorting controls

The purpose is deliberate:

> **Do not trust the aggregate number without being able to read the reviews behind it.**

---

### Methodology

The Methodology page documents:

* the analytical pipeline
* issue definitions
* classification logic
* validation status
* precision caveats
* prioritization rules

This makes the dashboard usable not only as a presentation layer, but also as an audit surface for the analysis itself.

---

## Tech Stack

* **Python**
* **Pandas** for data preparation and analytical transformations
* **NumPy** for numerical operations
* **Scikit-learn** for supporting analytical workflows
* **Streamlit** for the interactive application
* **Plotly** for visualization
* **Matplotlib / Seaborn** for exploratory analysis
* **Google Play Scraper** for review collection
* **Jupyter** for notebook-based analysis
* **Git / GitHub** for version control

---

## How to Reproduce

### 1. Clone the repository

```bash
git clone https://github.com/timothyevanheriawan-commits/bca-mobile-customer-voice.git
cd bca-mobile-customer-voice
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate on Windows:

```powershell
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the dashboard

```bash
streamlit run app/dashboard.py
```

The dashboard will then be available at:

```text
http://localhost:8501
```

---

## Repository Structure

```text
.
├── .streamlit/
│   └── config.toml
│
├── app/
│   ├── components/
│   │   ├── issue_explorer.py
│   │   ├── methodology.py
│   │   ├── overview.py
│   │   └── trends.py
│   │
│   ├── utils/
│   │   ├── data_loader.py
│   │   ├── definitions.py
│   │   ├── formatting.py
│   │   └── theme.py
│   │
│   └── dashboard.py
│
├── data/
│   ├── interim/
│   ├── processed/
│   │   └── bca_mobile_reviews_classified.csv
│   ├── raw/
│   └── validation/
│
├── notebooks/
│   ├── 01_data_audit.ipynb
│   ├── 02_exploratory_analysis.ipynb
│   ├── 03_issue_classification.ipynb
│   ├── 04_validation.ipynb
│   └── 05_prioritization.ipynb
│
├── outputs/
│
├── src/
│   ├── analysis.py
│   ├── cleaning.py
│   ├── config.py
│   ├── data_audit.py
│   ├── data_collection.py
│   ├── issue_classification.py
│   ├── prioritization.py
│   ├── sentiment.py
│   ├── validation.py
│   └── ...
│
├── tests/
│
├── requirements.txt
├── LICENSE
├── README.md
└── sessionHANDOFF.md
```

The repository separates the dashboard application from reusable analytical modules, while keeping the processed dataset and validation artifacts under `data/`.

---

## Limitations

* The analysis is based on **public Google Play reviews**, so it represents reported customer voice rather than the complete population of BCA Mobile users.
* The dataset covers only **May–August 2026**, giving the trend analysis a relatively short observation window.
* Rule-based classification is transparent but cannot achieve perfect recall because customers may describe the same problem using vocabulary that is not captured by the rules.
* Some issue categories have small numbers of observations, making broad generalizations risky.
* Validation quality varies by issue category. Some categories currently have fresh unannotated samples and therefore cannot honestly be presented as fully validated.
* Trend direction is intentionally based on first-half versus second-half monthly issue share rather than a fitted statistical trend model. This improves interpretability but sacrifices some statistical sophistication.
* A review may contain multiple issue labels, so issue counts are not additive.
* App-store ratings and text can disagree; a review may receive a high rating while still describing a concrete complaint. The classifier therefore does not assume that positive ratings imply absence of problems.

---

## Project Goal

This project demonstrates an end-to-end approach to **Customer Voice Analytics**, combining data preparation, transparent text classification, manual validation, issue-level analysis, trend analysis, prioritization, and interactive visualization.

The objective is not simply to count complaints.

It is to answer:

> **What are customers struggling with, how strong is the evidence, and which problems should the business investigate first?**

That distinction is what turns a review dataset into a **decision-support system** rather than just another sentiment dashboard.
