from pathlib import Path

import pandas as pd

import config


def generate_claim_status_reference():
    statuses = [
        {
            "claim_status_code": "SUBMITTED",
            "claim_status_description": "Claim submitted for processing",
            "is_final_status": False,
            "status_category": "OPEN",
            "display_order": 1,
        },
        {
            "claim_status_code": "PENDING",
            "claim_status_description": "Claim is pending review",
            "is_final_status": False,
            "status_category": "OPEN",
            "display_order": 2,
        },
        {
            "claim_status_code": "APPROVED",
            "claim_status_description": "Claim approved for payment",
            "is_final_status": True,
            "status_category": "CLOSED",
            "display_order": 3,
        },
        {
            "claim_status_code": "DENIED",
            "claim_status_description": "Claim denied",
            "is_final_status": True,
            "status_category": "CLOSED",
            "display_order": 4,
        },
        {
            "claim_status_code": "PAID",
            "claim_status_description": "Claim payment completed",
            "is_final_status": True,
            "status_category": "FINANCIAL",
            "display_order": 5,
        },
        {
            "claim_status_code": "ADJUSTED",
            "claim_status_description": "Claim adjusted after processing",
            "is_final_status": True,
            "status_category": "FINANCIAL",
            "display_order": 6,
        },
        {
            "claim_status_code": "REVERSED",
            "claim_status_description": "Claim payment or processing reversed",
            "is_final_status": True,
            "status_category": "FINANCIAL",
            "display_order": 7,
        },
        {
            "claim_status_code": "IN_REVIEW",
            "claim_status_description": "Claim is under detailed review",
            "is_final_status": False,
            "status_category": "OPEN",
            "display_order": 8,
        },
    ]

    output_path = config.SNOWFLAKE_DATA_DIR / "sf_claim_status_ref.csv"

    dataframe = pd.DataFrame(statuses)

    dataframe.to_csv(output_path, index=False)

    print(f"Generated: {output_path}")
    print(f"Rows: {len(dataframe)}")


if __name__ == "__main__":
    generate_claim_status_reference()