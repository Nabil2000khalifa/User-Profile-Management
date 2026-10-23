from typing import Annotated

from fastapi import APIRouter, Query

from app.core.auth import CurrentAdmin
from app.locations import LOCATIONS, cities_for_country

router = APIRouter(prefix="/api/v1/locations", tags=["locations"])


@router.get("/countries")
def countries(_current_admin: CurrentAdmin) -> dict[str, list[str]]:
    return {"items": list(LOCATIONS)}


@router.get("/cities")
def cities(
    _current_admin: CurrentAdmin,
    country: Annotated[str, Query(min_length=2, max_length=2)],
) -> dict[str, list[str]]:
    return {"items": list(cities_for_country(country) or ())}
