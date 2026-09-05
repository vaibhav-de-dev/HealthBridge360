from collections import defaultdict

import pandas as pd


MEMBERS_PATH = "data/snowflake/sf_members_current.csv"
POLICIES_PATH = "data/snowflake/sf_policies.csv"
CLAIMS_PATH = "data/snowflake/sf_claims.csv"


def load_event_sources():
    members_df = pd.read_csv(
        MEMBERS_PATH,
        usecols=["member_id"]
    )

    policies_df = pd.read_csv(
        POLICIES_PATH,
        usecols=["policy_id", "member_id"]
    )

    claims_df = pd.read_csv(
        CLAIMS_PATH,
        usecols=["claim_id", "member_id", "policy_id"]
    )

    member_ids = members_df["member_id"].dropna().astype(str).tolist()

    member_to_policies = defaultdict(list)

    for row in policies_df.itertuples(index=False):
        if pd.notna(row.member_id) and pd.notna(row.policy_id):
            member_to_policies[str(row.member_id)].append(
                str(row.policy_id)
            )

    member_to_claims = defaultdict(list)

    for row in claims_df.itertuples(index=False):
        if pd.notna(row.member_id) and pd.notna(row.claim_id):
            member_to_claims[str(row.member_id)].append(
                {
                    "claim_id": str(row.claim_id),
                    "policy_id": (
                        str(row.policy_id)
                        if pd.notna(row.policy_id)
                        else None
                    )
                }
            )

    return {
        "member_ids": member_ids,
        "member_to_policies": dict(member_to_policies),
        "member_to_claims": dict(member_to_claims),
    }
