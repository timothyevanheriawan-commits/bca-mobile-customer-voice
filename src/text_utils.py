"""
Shared text-processing helpers for exploratory analysis and issue classification.

This module exists because tokenize()/top_ngrams()/plot_ngrams() were originally
defined inline in 02_exploratory_analysis.ipynb, then copy-pasted (not imported)
into 03_issue_classification.ipynb. Pulling them out here means 02, 03, and
04_validation.ipynb all use the exact same tokenization logic — no risk of the
notebooks silently drifting out of sync with each other.

rating_group() is included for the same reason: 02 defined it as a function,
03 redefined it as an inline lambda. One definition here, used everywhere.
"""

import re
from collections import Counter

import matplotlib.pyplot as plt


# Indonesian stopwords for informal app-review text. Intentionally kept as a
# plain, visible set (not hidden in an external library) so a reviewer of this
# repo can see exactly what's being filtered and why, and it's easy to amend
# if a real complaint term is accidentally being dropped.
ID_STOPWORDS = {
    # function words / pronouns
    "yang", "di", "ke", "dari", "untuk", "dengan", "ini", "itu", "dan", "atau", "tidak",
    "tapi", "tetapi", "karena", "saya", "aku", "gua", "gue", "kita", "kami", "sy",
    # particles / fillers common in Indonesian informal text
    "ya", "gak", "ga", "enggak", "nggak", "nya", "aja", "sih", "deh", "dong", "banget",
    "bgt", "kok", "kan", "lah", "kah", "pun", "nih", "tuh", "yg", "dg", "dgn", "utk",
    "krn", "dr", "pd", "spy", "biar", "bs", "udh", "sdh", "dpt",
    # auxiliary / generic verbs
    "kalau", "kalo", "jadi", "sudah", "udah", "belum", "blm", "lagi", "masih", "juga",
    "ada", "adalah", "akan", "bisa", "pada", "oleh", "sebagai", "dalam", "sangat",
    "sekali", "saja", "semua", "harus", "mau", "bukan", "apa", "gimana", "bagaimana",
    "dapat", "punya",
    # domain terms that will appear in nearly every review regardless of sentiment
    # (kept separate/visible so it's a deliberate choice, not silent)
    "hp", "app", "aplikasi", "apk", "bca", "mobile", "banking", "bank",
}


def rating_group(rating: int) -> str:
    """Bucket a 1-5 star rating into negative (1-2) / neutral (3) / positive (4-5).

    Product-issue signal lives almost entirely in the negative group; 3-star is
    kept separate because it often reflects "it works but X is annoying" rather
    than a hard complaint.
    """
    if rating <= 2:
        return "negative"
    elif rating == 3:
        return "neutral"
    else:
        return "positive"


def tokenize(text: str) -> list:
    """Lowercase, strip punctuation/numbers, drop stopwords and 1-2 letter tokens."""
    text = str(text).lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    tokens = text.split()
    return [t for t in tokens if t not in ID_STOPWORDS and len(t) > 2]


def top_ngrams(texts, n: int = 1, top_k: int = 25):
    """Count the top-k n-grams across a collection of texts."""
    counter = Counter()
    for text in texts:
        tokens = tokenize(text)
        if n == 1:
            grams = tokens
        else:
            grams = [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]
        counter.update(grams)
    return counter.most_common(top_k)


def plot_ngrams(ngram_counts, title: str):
    """Horizontal bar chart of (term, count) pairs, most frequent at the top."""
    labels, counts = zip(*ngram_counts) if ngram_counts else ([], [])
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.barh(labels[::-1], counts[::-1], color="steelblue")
    ax.set_title(title)
    ax.set_xlabel("Frequency")
    plt.tight_layout()
    plt.show()