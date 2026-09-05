import random
from datetime import timedelta

import pandas as pd

import config


CLAIM_TYPES = [
    "MEDICAL",
    "PHARMACY",
    "DENTAL",
]

PLACE_OF_SERVICE = [
    "OFFICE",
    "INPATIENT_HOSPITAL",
    "OUTPATIENT_HOSPITAL",
    "EMERGENCY_ROOM",
    "URGENT_CARE",
    "LABORATORY",
    "PHARMACY",
]

DIAGNOSIS_CODES = [
    "E119",
    "I10",
    "J449",
    "M545",
    "E785",
    "K219",
    "N390",
    "F329",
    "G439",
    "Z0000",
    "Z1211",
    "R079",
]

PROCEDURE_CODES = [
    "99213",
    "99214",
    "99215",
    "80053",
    "85025",
    "93000",
    "81001",
    "36415",
    "71046",
    "70450",
    "20610",
    "43239",
    "45378",
    "47562",
    "29881",
]

CLAIM_STATUS_CODES = [
    "SUBMITTED",
    "PENDING",
    "APPROVED",
    "DENIED",
    "PAID",
    "ADJUSTED",
    "REVERSED",
    "IN_REVIEW",
]


def generate_claim_id(claim_number):
    return f"CLM{claim_number:09d}"


def generate_provider_id(random_generator):
    provider_number = random_generator.randint(1, 50_000)
    return f"PRV{provider_number:06d}"


def generate_amounts(random_generator):
    billed_amount = round(
        random_generator.uniform(50.00, 5000.00),
        2,
    )

    allowed_ratio = random_generator.uniform(
        0.55,
        0.95,
    )

    allowed_amount = round(
        billed_amount * allowed_ratio,
        2,
    )

    responsibility_ratio = random_generator.uniform(
        0.05,
        0.30,
    )

    member_responsibility = round(
        allowed_amount * responsibility_ratio,
        2,
    )

    if member_responsibility > allowed_amount:
        member_responsibility = allowed_amount

    return (
        billed_amount,
        allowed_amount,
        member_responsibility,
    )


def generate_service_date(
    policy_effective_date,
    policy_termination_date,
    random_generator,
):
    effective_date = pd.Timestamp(
        policy_effective_date
    )

    if pd.isna(policy_termination_date):
        end_date = pd.Timestamp(
            config.CURRENT_DATA_END_DATE
        )
    else:
        end_date = pd.Timestamp(
            policy_termination_date
        )

    if end_date < effective_date:
        end_date = effective_date

    day_range = (
        end_date - effective_date
    ).days

    if day_range <= 0:
        return effective_date

    random_days = random_generator.randint(
        0,
        day_range,
    )

    return effective_date + timedelta(
        days=random_days
    )


def generate_sf_claims():
    policies_path = (
        config.SNOWFLAKE_DATA_DIR
        / "sf_policies.csv"
    )

    status_path = (
        config.SNOWFLAKE_DATA_DIR
        / "sf_claim_status_ref.csv"
    )

    output_path = (
        config.SNOWFLAKE_DATA_DIR
        / "sf_claims.csv"
    )

    target_claims = getattr(
        config,
        "TARGET_CLAIMS",
        1_200_000,
    )

    random_seed = getattr(
        config,
        "SNOWFLAKE_CLAIMS_SEED",
        config.RANDOM_SEED + 3,
    )

    batch_size = getattr(
        config,
        "SNOWFLAKE_BATCH_SIZE",
        100_000,
    )

    random_generator = random.Random(
        random_seed
    )

    print(
        f"Reading policies: {policies_path}"
    )

    policies = pd.read_csv(
        policies_path,
        parse_dates=[
            "effective_date",
            "termination_date",
        ],
    )

    print(
        f"Policies loaded: {len(policies):,}"
    )

    statuses = pd.read_csv(
        status_path,
        usecols=["claim_status_code"],
    )

    valid_statuses = [
        status
        for status in statuses[
            "claim_status_code"
        ].astype(str)
        if status in CLAIM_STATUS_CODES
    ]

    if not valid_statuses:
        raise ValueError(
            "No valid claim status codes found."
        )

    if policies["policy_id"].duplicated().any():
        raise ValueError(
            "Duplicate policy_id values found."
        )

    if policies["member_id"].isna().any():
        raise ValueError(
            "NULL member_id found in policies."
        )

    if policies["policy_id"].isna().any():
        raise ValueError(
            "NULL policy_id found in policies."
        )

    if target_claims <= 0:
        raise ValueError(
            "TARGET_CLAIMS must be greater than zero."
        )

    print(
        f"Target claims: {target_claims:,}"
    )

    # Sample actual policy rows with replacement.
    selected_policy_indexes = random_generator.choices(
        range(len(policies)),
        k=target_claims,
    )

    first_write = True
    claims_written = 0
    claim_number = 1

    while claims_written < target_claims:

        current_batch_size = min(
            batch_size,
            target_claims - claims_written,
        )

        batch_records = []

        for _ in range(current_batch_size):

            policy_index = selected_policy_indexes[
                claims_written
            ]

            policy = policies.iloc[
                policy_index
            ]

            service_date = generate_service_date(
                policy["effective_date"],
                policy["termination_date"],
                random_generator,
            )

            claim_type = random_generator.choice(
                CLAIM_TYPES
            )

            claim_status = random_generator.choices(
                valid_statuses,
                weights=[
                    10,  # SUBMITTED
                    10,  # PENDING
                    15,  # APPROVED
                    8,   # DENIED
                    30,  # PAID
                    8,   # ADJUSTED
                    4,   # REVERSED
                    15,  # IN_REVIEW
                ],
                k=1,
            )[0]

            submission_date = (
                service_date
                + timedelta(
                    days=random_generator.randint(
                        1,
                        30,
                    )
                )
            )

            billed_amount, allowed_amount, member_responsibility = (
                generate_amounts(
                    random_generator
                )
            )

            claim_version = random_generator.choices(
                [1, 2, 3],
                weights=[94, 5, 1],
                k=1,
            )[0]

            diagnosis_code = random_generator.choice(
                DIAGNOSIS_CODES
            )

            procedure_code = random_generator.choice(
                PROCEDURE_CODES
            )

            batch_records.append(
                {
                    "claim_id": generate_claim_id(
                        claim_number
                    ),
                    "member_id": str(
                        policy["member_id"]
                    ).strip(),
                    "policy_id": str(
                        policy["policy_id"]
                    ).strip(),
                    "claim_status_code": claim_status,
                    "claim_type": claim_type,
                    "provider_id": generate_provider_id(
                        random_generator
                    ),
                    "service_date": service_date.strftime(
                        "%Y-%m-%d"
                    ),
                    "submission_date": submission_date.strftime(
                        "%Y-%m-%d"
                    ),
                    "diagnosis_code": diagnosis_code,
                    "procedure_code": procedure_code,
                    "place_of_service": random_generator.choice(
                        PLACE_OF_SERVICE
                    ),
                    "billed_amount": billed_amount,
                    "allowed_amount": allowed_amount,
                    "member_responsibility": member_responsibility,
                    "claim_version": claim_version,
                    "created_timestamp": submission_date.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "updated_timestamp": (
                        submission_date
                        + timedelta(
                            days=random_generator.randint(
                                0,
                                15,
                            )
                        )
                    ).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                }
            )

            claim_number += 1
            claims_written += 1

        batch_dataframe = pd.DataFrame(
            batch_records
        )

        batch_dataframe.to_csv(
            output_path,
            mode="w" if first_write else "a",
            header=first_write,
            index=False,
        )

        first_write = False

        print(
            f"Written claims: "
            f"{claims_written:,} / "
            f"{target_claims:,}"
        )

    print(
        f"Generated: {output_path}"
    )

    print(
        f"Total claims written: "
        f"{claims_written:,}"
    )


if __name__ == "__main__":
    generate_sf_claims()