from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import Engine

from app.db.session import check_database_connection, get_configured_engine

router = APIRouter(prefix="/api/v1/health", tags=["health"])


def get_database_engine() -> Engine:
    return get_configured_engine()


@router.get("/database")
def database_health(
    response: Response,
    engine: Annotated[Engine, Depends(get_database_engine)],
) -> dict[str, str]:
    if not check_database_connection(engine):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable"}
    return {"status": "ok"}
