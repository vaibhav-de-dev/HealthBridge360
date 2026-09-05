import random
from datetime import timedelta

import pandas as pd

import config


REVENUE_TYPES = [
    "CLAIM_PAYMENT",
    "MEMBER_PAYMENT",
    "RECOVERY",
    "REFUND",
]

PAYMENT_STATUSES = [
    "PAID",
    "PENDING",
    "FAILED",
]

PAYMENT_METHODS = [
    "ACH",
    "CHECK",
    "CARD",
]


def generate_revenue_id(revenue_number):
    return f"REV{revenue_number:09d}"


def generate_sf_revenue():
    claims_path = (
        config.SNOWFLAKE_DATA_DIR
        / "sf_claims.csv"
    )

    output_path = (
        config.SNOWFLAKE_DATA_DIR
        / "sf_revenue.csv"
    )

    target_revenue = getattr(
        config,
        "TARGET_REVENUE",
        1_000_000,
    )

    random_seed = getattr(
        config,
        "SNOWFLAKE_REVENUE_SEED",
        config.RANDOM_SEED + 5,
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
        f"Reading claims: {claims_path}"
    )

    claims = pd.read_csv(
        claims_path,
        usecols=[
            "claim_id",
            "member_id",
            "service_date",
            "submission_date",
            "billed_amount",
            "allowed_amount",
            "member_responsibility",
        ],
        parse_dates=[
            "service_date",
            "submission_date",
        ],
    )

    print(
        f"Claims loaded: {len(claims):,}"
    )

    if claims["claim_id"].isna().any():
        raise ValueError(
            "NULL claim_id values found."
        )

    if claims["member_id"].isna().any():
        raise ValueError(
            "NULL member_id values found."
        )

    if claims["claim_id"].duplicated().any():
        raise ValueError(
            "Duplicate claim_id values found."
        )

    if claims["allowed_amount"].isna().any():
        raise ValueError(
            "NULL allowed_amount values found."
        )

    if target_revenue <= 0:
        raise ValueError(
            "TARGET_REVENUE must be greater than zero."
        )

    random_indexes = random_generator.choices(
        range(len(claims)),
        k=target_revenue,
    )

    print(
        f"Target revenue transactions: "
        f"{target_revenue:,}"
    )

    first_write = True
    revenue_written = 0
    revenue_number = 1

    while revenue_written < target_revenue:

        current_batch_size = min(
            batch_size,
            target_revenue - revenue_written,
        )

        batch_records = []

        batch_start = revenue_written
        batch_end = (
            revenue_written
            + current_batch_size
        )

        batch_indexes = random_indexes[
            batch_start:batch_end
        ]

        for claim_index in batch_indexes:

            claim = claims.iloc[
                claim_index
            ]

            revenue_type = random_generator.choices(
                REVENUE_TYPES,
                weights=[
                    70,
                    10,
                    12,
                    8,
                ],
                k=1,
            )[0]

            payment_status = random_generator.choices(
                PAYMENT_STATUSES,
                weights=[
                    75,
                    20,
                    5,
                ],
                k=1,
            )[0]

            payment_method = random_generator.choice(
                PAYMENT_METHODS
            )

            billed_amount = float(
                claim["billed_amount"]
            )

            allowed_amount = float(
                claim["allowed_amount"]
            )

            member_responsibility = float(
                claim["member_responsibility"]
            )

            if revenue_type == "REFUND":
                paid_amount = round(
                    allowed_amount
                    * random_generator.uniform(
                        0.05,
                        0.50,
                    ),
                    2,
                )

            elif revenue_type == "RECOVERY":
                paid_amount = round(
                    allowed_amount
                    * random_generator.uniform(
                        0.05,
                        0.40,
                    ),
                    2,
                )

            else:
                paid_amount = round(
                    max(
                        0,
                        allowed_amount
                        - member_responsibility,
                    )
                    * random_generator.uniform(
                        0.85,
                        1.05,
                    ),
                    2,
                )

            if paid_amount > billed_amount:
                paid_amount = round(
                    billed_amount,
                    2,
                )

            transaction_date = (
                claim["submission_date"]
                + timedelta(
                    days=random_generator.randint(
                        1,
                        60,
                    )
                )
            )

            batch_records.append(
                {
                    "revenue_id": generate_revenue_id(
                        revenue_number
                    ),
                    "claim_id": str(
                        claim["claim_id"]
                    ).strip(),
                    "member_id": str(
                        claim["member_id"]
                    ).strip(),
                    "revenue_type": revenue_type,
                    "transaction_date": (
                        transaction_date.strftime(
                            "%Y-%m-%d"
                        )
                    ),
                    "billed_amount": round(
                        billed_amount,
                        2,
                    ),
                    "paid_amount": paid_amount,
                    "member_responsibility": round(
                        member_responsibility,
                        2,
                    ),
                    "payment_status": payment_status,
                    "payment_method": payment_method,
                    "created_timestamp": (
                        transaction_date.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    ),
                }
            )

            revenue_number += 1

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

        revenue_written += current_batch_size

        print(
            f"Written revenue: "
            f"{revenue_written:,} / "
            f"{target_revenue:,}"
        )

    print(
        f"Generated: {output_path}"
    )

    print(
        f"Total revenue rows written: "
        f"{revenue_written:,}"
    )


if __name__ == "__main__":
    generate_sf_revenue()