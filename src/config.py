from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
VALIDATION_DATA_DIR = DATA_DIR / "validation"


# ============================================================
# DATA COLLECTION
# ============================================================

APP_ID = "com.bca"

LANGUAGE = "id"
COUNTRY = "id"

# Maximum number of reviews to collect.
# Set to None to collect until Google Play stops returning reviews.
MAX_REVIEWS = 5000

BATCH_SIZE = 100

# Pause between requests to reduce request frequency.
REQUEST_DELAY = 1


# ============================================================
# FILE NAMES
# ============================================================

RAW_REVIEWS_FILE = (
    RAW_DATA_DIR / "bca_mobile_reviews_raw.csv"
)