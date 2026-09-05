from datetime import datetime

import pandas as pd

import config


FIRST_NAMES = [
    "James", "Robert", "John", "Michael", "David",
    "William", "Richard", "Joseph", "Thomas", "Charles",
    "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth",
    "Barbara", "Susan", "Jessica", "Sarah", "Karen"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones",
    "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin"
]

STATE_ZIP_RANGES = {
    "AL": (35000, 36999),
    "AZ": (85000, 86999),
    "CA": (90000, 96199),
    "CO": (80000, 81699),
    "CT": (6000, 6999),
    "FL": (32000, 34999),
    "GA": (30000, 31999),
    "IL": (60000, 62999),
    "MA": (1000, 2799),
    "MD": (20600, 21999),
    "MI": (48000, 49999),
    "MN": (55000, 56999),
    "MO": (63000, 65999),
    "NC": (27000, 28999),
    "NJ": (7000, 8999),
    "NV": (88900, 89999),
    "NY": (10000, 14999),
    "OH": (43000, 45999),
    "OR": (97000, 97999),
    "PA": (15000, 19699),
    "SC": (29000, 29999),
    "TN": (37000, 38999),
    "TX": (75000, 79999),
    "UT": (84000, 84999),
    "VA": (22000, 24699),
    "WA": (98000, 99499),
    "WI": (53000, 54999),
}


def derive_date_of_birth(birth_year, member_number):
    year = int(birth_year)

    month = (member_number % 12) + 1
    day = (member_number % 28) + 1

    return f"{year:04d}-{month:02d}-{day:02d}"


def derive_zip_code(state, member_number):
    state = str(state).strip().upper()

    if state not in STATE_ZIP_RANGES:
        return None

    minimum, maximum = STATE_ZIP_RANGES[state]
    zip_range = maximum - minimum + 1

    zip_code = minimum + (member_number % zip_range)

    return f"{zip_code:05d}"


def derive_member_name(member_number):
    first_name = FIRST_NAMES[member_number % len(FIRST_NAMES)]
    last_name = LAST_NAMES[
        (member_number // len(FIRST_NAMES)) % len(LAST_NAMES)
    ]

    return first_name, last_name


def generate_sf_members():
    source_path = (
        config.S3_DATA_DIR / "members_history_2021.csv"
    )

    output_path = (
        config.SNOWFLAKE_DATA_DIR / "sf_members_current.csv"
    )

    print(f"Reading source: {source_path}")

    dataframe = pd.read_csv(source_path)

    print(f"Historical rows loaded: {len(dataframe):,}")

    dataframe["effective_date"] = pd.to_datetime(
        dataframe["effective_date"],
        errors="coerce"
    )

    dataframe["record_updated_ts"] = pd.to_datetime(
        dataframe["record_updated_ts"],
        errors="coerce"
    )

    dataframe = dataframe.sort_values(
        by=[
            "legacy_member_id",
            "effective_date",
            "record_updated_ts"
        ],
        ascending=[True, True, True]
    )

    current_members = (
        dataframe
        .drop_duplicates(
            subset=["legacy_member_id"],
            keep="last"
        )
        .copy()
    )

    print(
        f"Unique current members selected: "
        f"{len(current_members):,}"
    )

    current_members = current_members.reset_index(drop=True)

    current_members["member_number"] = (
        current_members.index + 1
    )

    first_names = []
    last_names = []
    date_of_births = []
    zip_codes = []

    for _, row in current_members.iterrows():
        member_number = int(row["member_number"])

        first_name, last_name = derive_member_name(
            member_number
        )

        date_of_birth = derive_date_of_birth(
            row["birth_year"],
            member_number
        )

        zip_code = derive_zip_code(
            row["state"],
            member_number
        )

        first_names.append(first_name)
        last_names.append(last_name)
        date_of_births.append(date_of_birth)
        zip_codes.append(zip_code)

    current_members["first_name"] = first_names
    current_members["last_name"] = last_names
    current_members["date_of_birth"] = date_of_births
    current_members["zip_code"] = zip_codes

    current_members["member_status"] = (
        current_members["coverage_end_date"]
        .isna()
        .map({
            True: "ACTIVE",
            False: "INACTIVE"
        })
    )

    output_dataframe = current_members[
        [
            "legacy_member_id",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "state",
            "zip_code",
            "policy_type",
            "member_status",
            "effective_date",
            "coverage_end_date",
            "record_updated_ts"
        ]
    ].copy()

    output_dataframe = output_dataframe.rename(
        columns={
            "legacy_member_id": "member_id",
            "effective_date": "effective_date",
            "coverage_end_date": "termination_date",
            "record_updated_ts": "last_updated_timestamp"
        }
    )

    output_dataframe.to_csv(
        output_path,
        index=False
    )

    print(
        f"Generated: {output_path}"
    )

    print(
        f"Rows written: {len(output_dataframe):,}"
    )

    print(
        f"Unique member IDs: "
        f"{output_dataframe['member_id'].nunique():,}"
    )


if __name__ == "__main__":
    generate_sf_members()