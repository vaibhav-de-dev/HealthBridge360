import random
from datetime import timedelta

import pandas as pd

import config


POLICY_TYPES = [
    "PPO",
    "HMO",
    "EPO",
    "HDHP",
]

PLAN_NAMES = {
    "PPO": [
        "Choice PPO",
        "Preferred PPO",
        "National PPO",
    ],
    "HMO": [
        "Standard HMO",
        "Preferred HMO",
        "Value HMO",
    ],
    "EPO": [
        "Select EPO",
        "Network EPO",
        "Advantage EPO",
    ],
    "HDHP": [
        "HSA HDHP",
        "Value HDHP",
        "Premium HDHP",
    ],
}

COVERAGE_LEVELS = [
    "INDIVIDUAL",
    "FAMILY",
]


def generate_policy_id(policy_number):
    return f"POL{policy_number:08d}"


def calculate_financials(policy_type, random_generator):
    if policy_type == "HDHP":
        deductible = random_generator.choice(
            [1500.00, 2000.00, 2500.00, 3000.00]
        )
    else:
        deductible = random_generator.choice(
            [500.00, 750.00, 1000.00, 1500.00]
        )

    out_of_pocket_max = deductible * random_generator.choice(
        [2, 3, 4]
    )

    premium = random_generator.uniform(
        250.00,
        1200.00
    )

    return (
        round(premium, 2),
        round(deductible, 2),
        round(out_of_pocket_max, 2),
    )


def generate_sf_policies():
    source_path = (
        config.SNOWFLAKE_DATA_DIR
        / "sf_members_current.csv"
    )

    output_path = (
        config.SNOWFLAKE_DATA_DIR
        / "sf_policies.csv"
    )

    target_policies = getattr(
        config,
        "TARGET_POLICIES",
        160_000
    )

    random_seed = getattr(
        config,
        "SNOWFLAKE_POLICIES_SEED",
        config.RANDOM_SEED + 2
    )

    random_generator = random.Random(random_seed)

    print(f"Reading source: {source_path}")

    members = pd.read_csv(source_path)

    print(
        f"Members loaded: {len(members):,}"
    )

    members["effective_date"] = pd.to_datetime(
        members["effective_date"],
        errors="coerce"
    )

    members["termination_date"] = pd.to_datetime(
        members["termination_date"],
        errors="coerce"
    )

    if members["member_id"].isna().any():
        raise ValueError(
            "sf_members_current contains NULL member_id values."
        )

    if members["member_id"].duplicated().any():
        raise ValueError(
            "sf_members_current contains duplicate member_id values."
        )

    if target_policies < len(members):
        raise ValueError(
            "TARGET_POLICIES cannot be smaller than "
            "the number of members."
        )

    extra_policy_count = target_policies - len(members)

    selected_extra_members = members.sample(
        n=extra_policy_count,
        random_state=random_seed
    )

    records = []
    policy_number = 1

    # --------------------------------------------------------
    # Current policy: exactly one policy for every member
    # --------------------------------------------------------

    for _, member in members.iterrows():

        policy_type = str(
            member["policy_type"]
        ).strip().upper()

        if policy_type not in POLICY_TYPES:
            policy_type = random_generator.choice(
                POLICY_TYPES
            )

        coverage_level = random_generator.choice(
            COVERAGE_LEVELS
        )

        plan_name = random_generator.choice(
            PLAN_NAMES[policy_type]
        )

        premium, deductible, oop_max = (
            calculate_financials(
                policy_type,
                random_generator
            )
        )

        effective_date = (
            member["effective_date"]
        )

        if pd.isna(effective_date):
            effective_date = pd.Timestamp(
                "2021-01-01"
            )

        termination_date = (
            member["termination_date"]
        )

        if pd.isna(termination_date):
            policy_status = "ACTIVE"
            termination_value = None
        else:
            policy_status = "TERMINATED"
            termination_value = (
                termination_date.strftime("%Y-%m-%d")
            )

        records.append(
            {
                "policy_id": generate_policy_id(
                    policy_number
                ),
                "member_id": str(
                    member["member_id"]
                ).strip(),
                "policy_type": policy_type,
                "plan_name": plan_name,
                "coverage_level": coverage_level,
                "effective_date": (
                    effective_date.strftime("%Y-%m-%d")
                ),
                "termination_date": termination_value,
                "premium_amount": premium,
                "deductible_amount": deductible,
                "out_of_pocket_max": oop_max,
                "policy_status": policy_status,
                "last_updated_timestamp": (
                    member["last_updated_timestamp"]
                ),
            }
        )

        policy_number += 1

    # --------------------------------------------------------
    # Historical policy: one additional policy for selected
    # members, ending before their current policy begins
    # --------------------------------------------------------

    for _, member in selected_extra_members.iterrows():

        policy_type = random_generator.choice(
            POLICY_TYPES
        )

        coverage_level = random_generator.choice(
            COVERAGE_LEVELS
        )

        plan_name = random_generator.choice(
            PLAN_NAMES[policy_type]
        )

        premium, deductible, oop_max = (
            calculate_financials(
                policy_type,
                random_generator
            )
        )

        current_effective_date = (
            member["effective_date"]
        )

        if pd.isna(current_effective_date):
            current_effective_date = pd.Timestamp(
                "2021-01-01"
            )

        historical_end_date = (
            current_effective_date
            - timedelta(days=random_generator.randint(30, 180))
        )

        historical_start_date = (
            historical_end_date
            - timedelta(days=random_generator.randint(180, 730))
        )

        records.append(
            {
                "policy_id": generate_policy_id(
                    policy_number
                ),
                "member_id": str(
                    member["member_id"]
                ).strip(),
                "policy_type": policy_type,
                "plan_name": plan_name,
                "coverage_level": coverage_level,
                "effective_date": (
                    historical_start_date.strftime("%Y-%m-%d")
                ),
                "termination_date": (
                    historical_end_date.strftime("%Y-%m-%d")
                ),
                "premium_amount": premium,
                "deductible_amount": deductible,
                "out_of_pocket_max": oop_max,
                "policy_status": "TERMINATED",
                "last_updated_timestamp": (
                    member["last_updated_timestamp"]
                ),
            }
        )

        policy_number += 1

    policies = pd.DataFrame(records)

    policies.to_csv(
        output_path,
        index=False
    )

    print(
        f"Generated: {output_path}"
    )

    print(
        f"Rows written: {len(policies):,}"
    )

    print(
        f"Unique policy IDs: "
        f"{policies['policy_id'].nunique():,}"
    )

    print(
        f"Unique members represented: "
        f"{policies['member_id'].nunique():,}"
    )


if __name__ == "__main__":
    generate_sf_policies()