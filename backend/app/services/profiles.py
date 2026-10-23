from datetime import date

from app.locations import is_valid_location

MIN_DATE_OF_BIRTH = date(1900, 1, 1)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def canonicalize_profile_email(email: str) -> str:
    normalized = normalize_email(email)
    local_part, separator, domain = normalized.partition("@")
    if not separator or domain not in {"gmail.com", "googlemail.com"}:
        return normalized
    local_part = local_part.split("+", 1)[0].replace(".", "")
    return f"{local_part}@gmail.com"


def validate_profile_location(country: str, city: str) -> None:
    if country not in {"US", "IN"}:
        raise ValueError("country must be US or IN")
    if not is_valid_location(country, city):
        raise ValueError("city is not approved for the selected country")


def validate_date_of_birth(date_of_birth: date, today: date) -> None:
    if date_of_birth < MIN_DATE_OF_BIRTH:
        raise ValueError(
            f"date_of_birth cannot be earlier than {MIN_DATE_OF_BIRTH.isoformat()}"
        )
    if date_of_birth > today:
        raise ValueError("date_of_birth cannot be in the future")
