import config
import utils


def main():
    print("=" * 60)
    print("HealthBridge360 Data Generator")
    print("=" * 60)

    print(f"Project root   : {config.PROJECT_ROOT}")
    print(f"Total members  : {config.TOTAL_MEMBERS}")
    print(f"Random seed    : {config.RANDOM_SEED}")

    print("\nUtility test")
    print("-" * 60)

    print(f"Sample member ID : {utils.generate_member_id(1)}")
    print(f"Sample string    : {utils.random_string(8)}")
    print(f"Sample boolean   : {utils.random_boolean()}")

    print("\nGenerator framework initialized successfully.")


if __name__ == "__main__":
    main()