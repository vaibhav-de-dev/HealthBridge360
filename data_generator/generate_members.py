import csv
import random
from datetime import datetime, timedelta

import config
import utils


# ============================================================
# REFERENCE DATA
# ============================================================

US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
]

GENDERS = ["M", "F"]

POLICY_TYPES = [
    "HMO",
    "PPO",
    "EPO"
]

MEMBER_SEGMENTS = [
    "INDIVIDUAL",
    "FAMILY",
    "CORPORATE"
]

MEMBER_TIERS = [
    "SILVER",
    "GOLD",
    "PLATINUM"
]

SOURCE_SYSTEMS = [
    "LEGACY_A",
    "LEGACY_B"
]


# ============================================================
# MEMBER MASTER DATA
# ============================================================

def generate_master_members(member_count):
    """
    Generate the master member population.

    The same member population is reused across all historical
    yearly files so that cross-year relationships remain valid.
    """

    members = []

    for number in range(1, member_count + 1):
        birth_year = random.randint(1960, 2005)

        enrollment_start = datetime(2015, 1, 1)
        enrollment_end = datetime(2019, 12, 31)

        enrollment_date = utils.random_date(
            enrollment_start,
            enrollment_end
        ).date()

        members.append({
            "legacy_member_id": f"LEG_{number:08d}",
            "birth_year": birth_year,
            "gender": random.choice(GENDERS),
            "state": random.choice(US_STATES),
            "enrollment_date": enrollment_date
        })

    return members


# ============================================================
# HISTORICAL RECORD GENERATION
# ============================================================

def generate_historical_record(member, year, version):
    """Generate one historical member-policy record."""

    effective_date = datetime(
        year,
        random.randint(1, 12),
        random.randint(1, 28)
    )

    coverage_start_date = effective_date.date()

    # The latest historical year intentionally has open-ended
    # coverage, so coverage_end_date is legitimately NULL.
    if year == config.HISTORICAL_YEARS[-1]:
        coverage_end_date = None
    else:
        coverage_end_date = (
            effective_date + timedelta(days=364)
        ).date()

    record_updated_ts = effective_date + timedelta(
        days=random.randint(1, 30),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )

    policy_id = (
        f"POL_{year}_{version}_{random.randint(100000, 999999)}"
    )

    return {
        "legacy_member_id": member["legacy_member_id"],
        "birth_year": member["birth_year"],
        "gender": member["gender"],
        "state": member["state"],
        "enrollment_date": member["enrollment_date"],
        "policy_id": policy_id,
        "policy_type": random.choice(POLICY_TYPES),
        "coverage_start_date": coverage_start_date,
        "coverage_end_date": coverage_end_date,
        "member_segment": random.choice(MEMBER_SEGMENTS),
        "member_tier": random.choice(MEMBER_TIERS),
        "effective_date": effective_date.date(),
        "record_updated_ts": record_updated_ts,
        "source_system": random.choice(SOURCE_SYSTEMS)
    }


# ============================================================
# DATA QUALITY INJECTION
# ============================================================

def apply_data_quality_issues(record, quality_stats):
    """
    Inject controlled data-quality issues and track exactly
    what was injected.
    """

    # --------------------------------------------------------
    # NULL injection
    # --------------------------------------------------------

    original_state = record["state"]

    record["state"] = utils.maybe_null(
        record["state"],
        config.NULL_PERCENTAGE
    )

    if original_state is not None and record["state"] is None:
        quality_stats["null_injections"] += 1

    original_segment = record["member_segment"]

    record["member_segment"] = utils.maybe_null(
        record["member_segment"],
        config.NULL_PERCENTAGE
    )

    if original_segment is not None and record["member_segment"] is None:
        quality_stats["null_injections"] += 1

    original_tier = record["member_tier"]

    record["member_tier"] = utils.maybe_null(
        record["member_tier"],
        config.NULL_PERCENTAGE
    )

    if original_tier is not None and record["member_tier"] is None:
        quality_stats["null_injections"] += 1

    # --------------------------------------------------------
    # Whitespace injection
    # --------------------------------------------------------

    if record["state"] is not None:
        original_state = record["state"]

        record["state"] = utils.maybe_add_whitespace(
            record["state"],
            config.WHITESPACE_PERCENTAGE
        )

        if record["state"] != original_state:
            quality_stats["whitespace_injections"] += 1

    # --------------------------------------------------------
    # Case variation injection
    # --------------------------------------------------------

    if record["state"] is not None:
        original_state = record["state"]

        record["state"] = utils.maybe_change_case(
            record["state"],
            config.CASE_VARIATION_PERCENTAGE
        )

        if record["state"] != original_state:
            quality_stats["case_variations"] += 1

    return record


# ============================================================
# YEARLY FILE GENERATION
# ============================================================

def write_year_file(year, members, quality_stats):
    """Generate and write one historical yearly CSV file."""

    output_path = (
        config.S3_DATA_DIR /
        f"members_history_{year}.csv"
    )

    fieldnames = [
        "legacy_member_id",
        "birth_year",
        "gender",
        "state",
        "enrollment_date",
        "policy_id",
        "policy_type",
        "coverage_start_date",
        "coverage_end_date",
        "member_segment",
        "member_tier",
        "effective_date",
        "record_updated_ts",
        "source_system"
    ]

    row_count = 0

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for member in members:
            versions = random.randint(
                config.MIN_HISTORICAL_VERSIONS,
                config.MAX_HISTORICAL_VERSIONS
            )

            for version in range(1, versions + 1):
                record = generate_historical_record(
                    member,
                    year,
                    version
                )

                record = apply_data_quality_issues(
                    record,
                    quality_stats
                )

                writer.writerow(record)
                row_count += 1

    print(
        f"Generated {row_count:,} rows -> {output_path}"
    )


# ============================================================
# MAIN
# ============================================================

def generate_historical_members(member_count=None):
    """Generate all configured historical member files."""

    if member_count is None:
        member_count = config.TEST_MEMBER_COUNT

    random.seed(config.RANDOM_SEED)

    print("=" * 60)
    print("HealthBridge360 - Historical Member Generator")
    print("=" * 60)

    print(f"Members               : {member_count:,}")
    print(
        f"Historical years      : "
        f"{config.HISTORICAL_YEARS}"
    )

    quality_stats = {
        "null_injections": 0,
        "whitespace_injections": 0,
        "case_variations": 0
    }

    members = generate_master_members(member_count)

    for year in config.HISTORICAL_YEARS:
        write_year_file(
            year,
            members,
            quality_stats
        )

    print("\nData Quality Injection Summary")
    print("-" * 60)
    print(
        f"NULL injections       : "
        f"{quality_stats['null_injections']:,}"
    )
    print(
        f"Whitespace injections : "
        f"{quality_stats['whitespace_injections']:,}"
    )
    print(
        f"Case variations       : "
        f"{quality_stats['case_variations']:,}"
    )

    print("\nHistorical member generation completed.")


if __name__ == "__main__":
    generate_historical_members()
