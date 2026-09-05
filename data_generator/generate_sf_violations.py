import random
from datetime import timedelta

import pandas as pd

import config


VIOLATION_TYPES = [
    "DUPLICATE_CLAIM",
    "INVALID_PROCEDURE",
    "INVALID_DIAGNOSIS",
    "ELIGIBILITY_MISMATCH",
    "MEMBER_DATA_QUALITY",
    "PAYMENT_ANOMALY",
    "PROVIDER_DATA_QUALITY",
]

SEVERITIES = [
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
]

VIOLATION_STATUSES = [
    "OPEN",
    "RESOLVED",
    "UNDER_REVIEW",
]

VIOLATION_DESCRIPTIONS = {
    "DUPLICATE_CLAIM": (
        "Potential duplicate claim detected"
    ),
    "INVALID_PROCEDURE": (
        "Procedure code failed validation"
    ),
    "INVALID_DIAGNOSIS": (
        "Diagnosis code failed validation"
    ),
    "ELIGIBILITY_MISMATCH": (
        "Claim activity does not match eligibility"
    ),
    "MEMBER_DATA_QUALITY": (
        "Member record contains a data quality issue"
    ),
    "PAYMENT_ANOMALY": (
        "Potential payment anomaly detected"
    ),
    "PROVIDER_DATA_QUALITY": (
        "Provider information failed validation"
    ),
}


def generate_violation_id(violation_number):
    return f"VIO{violation_number:08d}"


def generate_sf_violations():
    members_path = (
        config.SNOWFLAKE_DATA_DIR
        / "sf_members_current.csv"
    )

    claims_path = (
        config.SNOWFLAKE_DATA_DIR
        / "sf_claims.csv"
    )

    output_path = (
        config.SNOWFLAKE_DATA_DIR
        / "sf_violations.csv"
    )

    target_violations = getattr(
        config,
        "TARGET_VIOLATIONS",
        35_000,
    )

    random_seed = getattr(
        config,
        "SNOWFLAKE_VIOLATIONS_SEED",
        config.RANDOM_SEED + 6,
    )

    random_generator = random.Random(
        random_seed
    )

    print(
        f"Reading members: {members_path}"
    )

    members = pd.read_csv(
        members_path,
        usecols=["member_id"],
    )

    print(
        f"Members loaded: {len(members):,}"
    )

    print(
        f"Reading claims: {claims_path}"
    )

    claims = pd.read_csv(
        claims_path,
        usecols=[
            "claim_id",
            "member_id",
            "service_date",
        ],
        parse_dates=["service_date"],
    )

    print(
        f"Claims loaded: {len(claims):,}"
    )

    if members["member_id"].isna().any():
        raise ValueError(
            "NULL member_id values found."
        )

    if claims["claim_id"].isna().any():
        raise ValueError(
            "NULL claim_id values found."
        )

    if target_violations <= 0:
        raise ValueError(
            "TARGET_VIOLATIONS must be greater than zero."
        )

    if target_violations > len(members):
        raise ValueError(
            "TARGET_VIOLATIONS is larger than the "
            "available member population."
        )

    # --------------------------------------------------------
    # Select members that will receive violations.
    # --------------------------------------------------------

    selected_members = members.sample(
        n=target_violations,
        random_state=random_seed,
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # Select claim rows independently.
    # A portion of violations will be claim-level.
    # --------------------------------------------------------

    claim_count = int(
        target_violations * 0.75
    )

    selected_claims = claims.sample(
        n=claim_count,
        random_state=random_seed + 1,
    ).reset_index(drop=True)

    claim_lookup = (
        selected_claims
        .set_index("claim_id")
        ["member_id"]
        .astype(str)
        .str.strip()
        .to_dict()
    )

    records = []

    for violation_number in range(
        1,
        target_violations + 1,
    ):

        member_id = str(
            selected_members.iloc[
                violation_number - 1
            ]["member_id"]
        ).strip()

        violation_type = random_generator.choice(
            VIOLATION_TYPES
        )

        severity = random_generator.choices(
            SEVERITIES,
            weights=[
                45,
                35,
                17,
                3,
            ],
            k=1,
        )[0]

        violation_status = random_generator.choices(
            VIOLATION_STATUSES,
            weights=[
                35,
                45,
                20,
            ],
            k=1,
        )[0]

        # 75% claim-level, 25% member-level.
        if violation_number <= claim_count:
            claim = selected_claims.iloc[
                violation_number - 1
            ]

            claim_id = str(
                claim["claim_id"]
            ).strip()

            detected_date = (
                claim["service_date"]
                + timedelta(
                    days=random_generator.randint(
                        1,
                        90,
                    )
                )
            )

            # Keep the claim/member relationship correct.
            member_id = str(
                claim["member_id"]
            ).strip()

        else:
            claim_id = None

            detected_date = pd.Timestamp(
                "2026-01-01"
            ) + timedelta(
                days=random_generator.randint(
                    0,
                    30,
                )
            )

        if violation_status == "RESOLVED":

            resolved_date = (
                detected_date
                + timedelta(
                    days=random_generator.randint(
                        1,
                        30,
                    )
                )
            )

            resolved_date_value = (
                resolved_date.strftime(
                    "%Y-%m-%d"
                )
            )

        else:
            resolved_date_value = None

        records.append(
            {
                "violation_id": generate_violation_id(
                    violation_number
                ),
                "member_id": member_id,
                "claim_id": claim_id,
                "violation_type": violation_type,
                "severity": severity,
                "violation_status": violation_status,
                "violation_description": (
                    VIOLATION_DESCRIPTIONS[
                        violation_type
                    ]
                ),
                "detected_date": (
                    detected_date.strftime(
                        "%Y-%m-%d"
                    )
                ),
                "resolved_date": resolved_date_value,
                "created_timestamp": (
                    detected_date.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                ),
            }
        )

    violations = pd.DataFrame(records)

    violations.to_csv(
        output_path,
        index=False,
    )

    claim_level_count = (
        violations["claim_id"]
        .notna()
        .sum()
    )

    member_level_count = (
        violations["claim_id"]
        .isna()
        .sum()
    )

    print(
        f"Generated: {output_path}"
    )

    print(
        f"Rows written: "
        f"{len(violations):,}"
    )

    print(
        f"Unique violation IDs: "
        f"{violations['violation_id'].nunique():,}"
    )

    print(
        f"Claim-level violations: "
        f"{claim_level_count:,}"
    )

    print(
        f"Member-level violations: "
        f"{member_level_count:,}"
    )


if __name__ == "__main__":
    generate_sf_violations()