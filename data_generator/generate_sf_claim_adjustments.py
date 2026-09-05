import random
from datetime import timedelta

import pandas as pd

import config


ADJUSTMENT_TYPES = [
    "CORRECTION",
    "REVERSAL",
    "REPROCESS",
]

ADJUSTMENT_REASONS = [
    "CODING_CORRECTION",
    "DUPLICATE_CLAIM",
    "PRICING_CORRECTION",
    "MEMBER_ELIGIBILITY_UPDATE",
    "PROVIDER_CORRECTION",
    "PROCESSING_ERROR",
    "PAYMENT_REVERSAL",
]


def generate_adjustment_id(adjustment_number):
    return f"ADJ{adjustment_number:09d}"


def generate_sf_claim_adjustments():
    claims_path = (
        config.SNOWFLAKE_DATA_DIR
        / "sf_claims.csv"
    )

    output_path = (
        config.SNOWFLAKE_DATA_DIR
        / "sf_claims_adjustments.csv"
    )

    target_adjustments = getattr(
        config,
        "TARGET_ADJUSTMENTS",
        150_000,
    )

    random_seed = getattr(
        config,
        "SNOWFLAKE_ADJUSTMENTS_SEED",
        config.RANDOM_SEED + 4,
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
            "allowed_amount",
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

    if claims["claim_id"].duplicated().any():
        raise ValueError(
            "Duplicate claim_id values found."
        )

    if claims["allowed_amount"].isna().any():
        raise ValueError(
            "NULL allowed_amount values found."
        )

    if target_adjustments <= 0:
        raise ValueError(
            "TARGET_ADJUSTMENTS must be greater than zero."
        )

    if target_adjustments > len(claims):
        raise ValueError(
            "TARGET_ADJUSTMENTS cannot exceed "
            "the number of claims."
        )

    selected_claims = claims.sample(
        n=target_adjustments,
        random_state=random_seed,
    ).reset_index(drop=True)

    print(
        f"Target adjustments: "
        f"{target_adjustments:,}"
    )

    first_write = True
    adjustments_written = 0
    adjustment_number = 1

    while adjustments_written < target_adjustments:

        current_batch_size = min(
            batch_size,
            target_adjustments - adjustments_written,
        )

        batch_records = []

        batch_start = adjustments_written
        batch_end = (
            adjustments_written
            + current_batch_size
        )

        batch_claims = selected_claims.iloc[
            batch_start:batch_end
        ]

        for _, claim in batch_claims.iterrows():

            adjustment_type = random_generator.choice(
                ADJUSTMENT_TYPES
            )

            reason = random_generator.choice(
                ADJUSTMENT_REASONS
            )

            previous_amount = float(
                claim["allowed_amount"]
            )

            adjustment_factor = random_generator.uniform(
                0.05,
                0.35,
            )

            if adjustment_type == "REVERSAL":
                adjusted_amount = 0.00

            elif adjustment_type == "CORRECTION":
                adjusted_amount = round(
                    previous_amount
                    * random_generator.uniform(
                        0.65,
                        1.15,
                    ),
                    2,
                )

            else:
                adjusted_amount = round(
                    previous_amount
                    * (
                        1
                        + random_generator.uniform(
                            -adjustment_factor,
                            adjustment_factor,
                        )
                    ),
                    2,
                )

            claim_date = claim["submission_date"]

            adjustment_date = (
                claim_date
                + timedelta(
                    days=random_generator.randint(
                        1,
                        45,
                    )
                )
            )

            batch_records.append(
                {
                    "adjustment_id": generate_adjustment_id(
                        adjustment_number
                    ),
                    "claim_id": str(
                        claim["claim_id"]
                    ).strip(),
                    "adjustment_type": adjustment_type,
                    "previous_amount": round(
                        previous_amount,
                        2,
                    ),
                    "adjusted_amount": adjusted_amount,
                    "adjustment_reason": reason,
                    "adjustment_date": (
                        adjustment_date.strftime(
                            "%Y-%m-%d"
                        )
                    ),
                    "adjusted_by": (
                        f"SYSTEM_"
                        f"{random_generator.randint(100, 999)}"
                    ),
                    "created_timestamp": (
                        adjustment_date.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    ),
                }
            )

            adjustment_number += 1

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

        adjustments_written += current_batch_size

        print(
            f"Written adjustments: "
            f"{adjustments_written:,} / "
            f"{target_adjustments:,}"
        )

    print(
        f"Generated: {output_path}"
    )

    print(
        f"Total adjustments written: "
        f"{adjustments_written:,}"
    )


if __name__ == "__main__":
    generate_sf_claim_adjustments()