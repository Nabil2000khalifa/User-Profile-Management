LOCATIONS: dict[str, tuple[str, ...]] = {
    "US": ("New York", "Los Angeles", "Chicago"),
    "IN": ("Mumbai", "Delhi", "Ahmedabad"),
}


def cities_for_country(country: str) -> tuple[str, ...] | None:
    return LOCATIONS.get(country)


def is_valid_location(country: str, city: str) -> bool:
    return city in LOCATIONS.get(country, ())
