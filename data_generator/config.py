from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"

S3_DATA_DIR = DATA_DIR / "s3"
SNOWFLAKE_DATA_DIR = DATA_DIR / "snowflake"
WEB_API_DATA_DIR = DATA_DIR / "web_api"


# ============================================================
# DATA GENERATION CONTROL
# ============================================================

RANDOM_SEED = 42

TOTAL_MEMBERS = 100_000

# Deterministic seeds for each Snowflake dataset.
# Keep the historical-member seed/settings unchanged above.
SNOWFLAKE_SEEDS = {
    "status_ref": 1007,
    "members": 1001,
    "policies": 1002,
    "claims": 1003,
    "adjustments": 1004,
    "revenue": 1005,
    "violations": 1006,
}

# Target row volumes for the Snowflake source model.
TARGET_POLICY_COUNT = 160_000
TARGET_CLAIM_COUNT = 1_200_000
TARGET_ADJUSTMENT_COUNT = 150_000
TARGET_REVENUE_COUNT = 1_000_000
TARGET_VIOLATION_COUNT = 35_000


# ============================================================
# HISTORICAL MEMBER GENERATION
# ============================================================

TEST_MEMBER_COUNT = 100_000

MIN_HISTORICAL_VERSIONS = 1
MAX_HISTORICAL_VERSIONS = 3

HISTORICAL_YEARS = [2019, 2020, 2021]


# ============================================================
# JOB 1 TEST DATASET
# ============================================================

JOB1_TEST_RECORD_COUNT = 500
JOB1_TEST_SEED = 42

JOB1_TEST_YEARS = [2023, 2024, 2025]


# ============================================================
# DATE CONFIGURATION
# ============================================================

HISTORICAL_START_YEAR = 2019
HISTORICAL_END_YEAR = 2021

CURRENT_DATA_START_DATE = "2026-01-01"
CURRENT_DATA_END_DATE = "2026-01-31"

INGESTION_DATE = "2026-01-09"


# ============================================================
# SOURCE 1 - HISTORICAL MEMBER DATA
# ============================================================

HISTORICAL_MEMBER_FILES = [
    "members_history_2019.csv",
    "members_history_2020.csv",
    "members_history_2021.csv",
]


# ============================================================
# SOURCE 2 - SNOWFLAKE SOURCE DATA
# ============================================================

SNOWFLAKE_FILES = [
    "sf_members_current.csv",
    "sf_claims.csv",
    "sf_claims_adjustments.csv",
    "sf_policies.csv",
    "sf_revenue.csv",
    "sf_violations.csv",
    "sf_claim_status_ref.csv",
]

# Dedicated output paths for each Snowflake dataset.
SNOWFLAKE_MEMBERS_FILE = SNOWFLAKE_DATA_DIR / "sf_members_current.csv"
SNOWFLAKE_POLICIES_FILE = SNOWFLAKE_DATA_DIR / "sf_policies.csv"
SNOWFLAKE_CLAIMS_FILE = SNOWFLAKE_DATA_DIR / "sf_claims.csv"
SNOWFLAKE_ADJUSTMENTS_FILE = (
    SNOWFLAKE_DATA_DIR / "sf_claims_adjustments.csv"
)
SNOWFLAKE_REVENUE_FILE = SNOWFLAKE_DATA_DIR / "sf_revenue.csv"
SNOWFLAKE_VIOLATIONS_FILE = SNOWFLAKE_DATA_DIR / "sf_violations.csv"
SNOWFLAKE_STATUS_REF_FILE = (
    SNOWFLAKE_DATA_DIR / "sf_claim_status_ref.csv"
)

# Batch size used by large-volume generators to control memory usage.
SNOWFLAKE_BATCH_SIZE = 100_000


# ============================================================
# SOURCE 3 - HEALTHCARE EVENTS API
# ============================================================

EVENT_FILE_PREFIX = "healthcare_events"

EVENT_BATCH_SIZE = 10_000


# ============================================================
# DATA QUALITY CONFIGURATION
# ============================================================

NULL_PERCENTAGE = 0.02
DUPLICATE_PERCENTAGE = 0.01
INVALID_VALUE_PERCENTAGE = 0.01
WHITESPACE_PERCENTAGE = 0.02
CASE_VARIATION_PERCENTAGE = 0.02
ZERO_VALUE_PERCENTAGE = 0.01


# ============================================================
# OUTPUT FORMATS
# ============================================================

HISTORICAL_OUTPUT_FORMAT = "csv"
SNOWFLAKE_OUTPUT_FORMAT = "csv"
EVENT_OUTPUT_FORMAT = "json"


# ============================================================
# CREATE REQUIRED DIRECTORIES
# ============================================================

for directory in [
    DATA_DIR,
    LOG_DIR,
    S3_DATA_DIR,
    SNOWFLAKE_DATA_DIR,
    WEB_API_DATA_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)
