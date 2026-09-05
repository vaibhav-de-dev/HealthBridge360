from datetime import datetime, timedelta
import random
import string


def generate_member_id(number: int) -> str:
    """Generate a consistent member ID."""
    return f"M{number:08d}"


def random_date(start_date: datetime, end_date: datetime) -> datetime:
    """Return a random date between two dates."""
    days_between = (end_date - start_date).days

    if days_between < 0:
        raise ValueError("start_date must be before end_date")

    random_days = random.randint(0, days_between)

    return start_date + timedelta(days=random_days)


def random_string(length: int = 10) -> str:
    """Generate a random uppercase alphanumeric string."""
    if length <= 0:
        raise ValueError("length must be greater than zero")

    characters = string.ascii_uppercase + string.digits

    return "".join(random.choices(characters, k=length))


def random_boolean(true_probability: float = 0.5) -> bool:
    """Return True based on the supplied probability."""
    if not 0 <= true_probability <= 1:
        raise ValueError("true_probability must be between 0 and 1")

    return random.random() < true_probability


def maybe_null(value, null_probability: float = 0.02):
    """Return None based on the supplied probability."""
    if not 0 <= null_probability <= 1:
        raise ValueError("null_probability must be between 0 and 1")

    if random.random() < null_probability:
        return None

    return value


def maybe_add_whitespace(value, whitespace_probability: float = 0.02):
    """Randomly introduce leading/trailing whitespace."""
    if value is None:
        return None

    if not 0 <= whitespace_probability <= 1:
        raise ValueError("whitespace_probability must be between 0 and 1")

    if random.random() >= whitespace_probability:
        return value

    whitespace_options = [
        f" {value}",
        f"{value} ",
        f" {value} ",
    ]

    return random.choice(whitespace_options)


def maybe_change_case(value, case_probability: float = 0.02):
    """Randomly change string case."""
    if value is None:
        return None

    if not 0 <= case_probability <= 1:
        raise ValueError("case_probability must be between 0 and 1")

    if random.random() >= case_probability:
        return value

    case_options = [
        str(value).upper(),
        str(value).lower(),
    ]

    return random.choice(case_options)