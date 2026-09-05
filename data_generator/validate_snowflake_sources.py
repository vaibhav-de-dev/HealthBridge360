import pandas as pd

import config


def load_ids(file_path, column_name):
    dataframe = pd.read_csv(
        file_path,
        usecols=[column_name],
    )

    return set(
        dataframe[column_name]
        .dropna()
        .astype(str)
        .str.strip()
    )


def validate_unique_key(
    file_path,
    key_column,
    expected_rows,
):
    dataframe = pd.read_csv(
        file_path,
        usecols=[key_column],
    )

    actual_rows = len(dataframe)
    unique_keys = dataframe[key_column].nunique()

    assert actual_rows == expected_rows, (
        f"{file_path.name}: expected "
        f"{expected_rows:,} rows, got "
        f"{actual_rows:,}"
    )

    assert unique_keys == actual_rows, (
        f"{file_path.name}: duplicate "
        f"{key_column} values found"
    )

    assert not dataframe[key_column].isna().any(), (
        f"{file_path.name}: NULL "
        f"{key_column} values found"
    )

    return actual_rows


def main():

    base_path = config.SNOWFLAKE_DATA_DIR

    files = {
        "members": base_path / "sf_members_current.csv",
        "policies": base_path / "sf_policies.csv",
        "claims": base_path / "sf_claims.csv",
        "adjustments": (
            base_path
            / "sf_claims_adjustments.csv"
        ),
        "revenue": base_path / "sf_revenue.csv",
        "violations": base_path / "sf_violations.csv",
        "status": (
            base_path
            / "sf_claim_status_ref.csv"
        ),
    }

    expected_rows = {
        "members": 100_000,
        "policies": 160_000,
        "claims": 1_200_000,
        "adjustments": 150_000,
        "revenue": 1_000_000,
        "violations": 35_000,
        "status": 8,
    }

    print("=" * 70)
    print("HealthBridge360 - Snowflake Source Audit")
    print("=" * 70)

    # --------------------------------------------------------
    # PRIMARY KEY VALIDATION
    # --------------------------------------------------------

    validate_unique_key(
        files["members"],
        "member_id",
        expected_rows["members"],
    )

    validate_unique_key(
        files["policies"],
        "policy_id",
        expected_rows["policies"],
    )

    validate_unique_key(
        files["claims"],
        "claim_id",
        expected_rows["claims"],
    )

    validate_unique_key(
        files["adjustments"],
        "adjustment_id",
        expected_rows["adjustments"],
    )

    validate_unique_key(
        files["revenue"],
        "revenue_id",
        expected_rows["revenue"],
    )

    validate_unique_key(
        files["violations"],
        "violation_id",
        expected_rows["violations"],
    )

    validate_unique_key(
        files["status"],
        "claim_status_code",
        expected_rows["status"],
    )

    print("PASS - Primary keys and row counts")

    # --------------------------------------------------------
    # LOAD REFERENCE ID SETS
    # --------------------------------------------------------

    member_ids = load_ids(
        files["members"],
        "member_id",
    )

    policy_ids = load_ids(
        files["policies"],
        "policy_id",
    )

    claim_ids = load_ids(
        files["claims"],
        "claim_id",
    )

    status_codes = load_ids(
        files["status"],
        "claim_status_code",
    )

    # --------------------------------------------------------
    # POLICY FK VALIDATION
    # --------------------------------------------------------

    policies = pd.read_csv(
        files["policies"],
        usecols=["policy_id", "member_id"],
    )

    invalid_policy_members = (
        set(
            policies["member_id"]
            .astype(str)
            .str.strip()
        )
        - member_ids
    )

    assert len(invalid_policy_members) == 0, (
        "Invalid member FKs found in policies"
    )

    print("PASS - policies.member_id ? members.member_id")

    # --------------------------------------------------------
    # CLAIM FK VALIDATION
    # --------------------------------------------------------

    claims = pd.read_csv(
        files["claims"],
        usecols=[
            "claim_id",
            "member_id",
            "policy_id",
            "claim_status_code",
        ],
    )

    invalid_claim_members = (
        set(
            claims["member_id"]
            .astype(str)
            .str.strip()
        )
        - member_ids
    )

    invalid_claim_policies = (
        set(
            claims["policy_id"]
            .astype(str)
            .str.strip()
        )
        - policy_ids
    )

    invalid_claim_statuses = (
        set(
            claims["claim_status_code"]
            .astype(str)
            .str.strip()
        )
        - status_codes
    )

    assert len(invalid_claim_members) == 0, (
        "Invalid member FKs found in claims"
    )

    assert len(invalid_claim_policies) == 0, (
        "Invalid policy FKs found in claims"
    )

    assert len(invalid_claim_statuses) == 0, (
        "Invalid claim status FKs found in claims"
    )

    # --------------------------------------------------------
    # CLAIM MEMBER/POLICY PAIR VALIDATION
    # --------------------------------------------------------

    policy_pairs = set(
        zip(
            policies["policy_id"]
            .astype(str)
            .str.strip(),
            policies["member_id"]
            .astype(str)
            .str.strip(),
        )
    )

    claim_pairs = set(
        zip(
            claims["policy_id"]
            .astype(str)
            .str.strip(),
            claims["member_id"]
            .astype(str)
            .str.strip(),
        )
    )

    invalid_claim_pairs = (
        claim_pairs - policy_pairs
    )

    assert len(invalid_claim_pairs) == 0, (
        "Claims contain invalid "
        "policy/member combinations"
    )

    print(
        "PASS - claims member/policy relationships"
    )

    # --------------------------------------------------------
    # ADJUSTMENT FK VALIDATION
    # --------------------------------------------------------

    adjustments = pd.read_csv(
        files["adjustments"],
        usecols=["adjustment_id", "claim_id"],
    )

    invalid_adjustment_claims = (
        set(
            adjustments["claim_id"]
            .astype(str)
            .str.strip()
        )
        - claim_ids
    )

    assert len(invalid_adjustment_claims) == 0, (
        "Invalid claim FKs found in adjustments"
    )

    print(
        "PASS - adjustments.claim_id ? claims.claim_id"
    )

    # --------------------------------------------------------
    # REVENUE FK + MEMBER/CLAIM PAIR VALIDATION
    # --------------------------------------------------------

    revenue = pd.read_csv(
        files["revenue"],
        usecols=[
            "revenue_id",
            "claim_id",
            "member_id",
        ],
    )

    invalid_revenue_claims = (
        set(
            revenue["claim_id"]
            .astype(str)
            .str.strip()
        )
        - claim_ids
    )

    invalid_revenue_members = (
        set(
            revenue["member_id"]
            .astype(str)
            .str.strip()
        )
        - member_ids
    )

    claim_member_pairs = set(
        zip(
            claims["claim_id"]
            .astype(str)
            .str.strip(),
            claims["member_id"]
            .astype(str)
            .str.strip(),
        )
    )

    revenue_claim_member_pairs = set(
        zip(
            revenue["claim_id"]
            .astype(str)
            .str.strip(),
            revenue["member_id"]
            .astype(str)
            .str.strip(),
        )
    )

    invalid_revenue_pairs = (
        revenue_claim_member_pairs
        - claim_member_pairs
    )

    assert len(invalid_revenue_claims) == 0, (
        "Invalid claim FKs found in revenue"
    )

    assert len(invalid_revenue_members) == 0, (
        "Invalid member FKs found in revenue"
    )

    assert len(invalid_revenue_pairs) == 0, (
        "Revenue contains invalid "
        "claim/member combinations"
    )

    print(
        "PASS - revenue claim/member relationships"
    )

    # --------------------------------------------------------
    # VIOLATION FK + CLAIM/MEMBER VALIDATION
    # --------------------------------------------------------

    violations = pd.read_csv(
        files["violations"],
        usecols=[
            "violation_id",
            "member_id",
            "claim_id",
        ],
    )

    invalid_violation_members = (
        set(
            violations["member_id"]
            .astype(str)
            .str.strip()
        )
        - member_ids
    )

    violation_claims = set(
        violations["claim_id"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    invalid_violation_claims = (
        violation_claims - claim_ids
    )

    assert len(invalid_violation_members) == 0, (
        "Invalid member FKs found in violations"
    )

    assert len(invalid_violation_claims) == 0, (
        "Invalid claim FKs found in violations"
    )

    violation_claim_member_pairs = set(
        zip(
            violations["claim_id"]
            .dropna()
            .astype(str)
            .str.strip(),
            violations.loc[
                violations["claim_id"].notna(),
                "member_id"
            ]
            .astype(str)
            .str.strip(),
        )
    )

    invalid_violation_pairs = (
        violation_claim_member_pairs
        - claim_member_pairs
    )

    assert len(invalid_violation_pairs) == 0, (
        "Violations contain invalid "
        "claim/member combinations"
    )

    print(
        "PASS - violation claim/member relationships"
    )

    # --------------------------------------------------------
    # NULL CLAIM VALIDATION
    # --------------------------------------------------------

    null_claim_count = (
        violations["claim_id"]
        .isna()
        .sum()
    )

    assert null_claim_count == 8_750, (
        f"Expected 8,750 member-level violations, "
        f"found {null_claim_count:,}"
    )

    print(
        "PASS - member-level violation NULL claim count"
    )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print("=" * 70)
    print("ALL SNOWFLAKE SOURCE VALIDATIONS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()