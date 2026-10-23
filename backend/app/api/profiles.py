from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import CsrfProtected, CurrentAdmin
from app.db.session import get_db_session
from app.models import UserProfile
from app.schemas.profile import ProfileCreateRequest, ProfilePage, ProfileResponse
from app.services.audit import AuditEvent, record_audit
from app.services.profiles import (
    canonicalize_profile_email,
    validate_date_of_birth,
    validate_profile_location,
)

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def profile_response(profile: UserProfile) -> ProfileResponse:
    return ProfileResponse(
        id=profile.id,
        first_name=profile.first_name,
        last_name=profile.last_name,
        date_of_birth=profile.date_of_birth,
        email=profile.email,
        country=profile.country,
        city=profile.city,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def validate_profile_payload(payload: ProfileCreateRequest) -> None:
    try:
        validate_date_of_birth(payload.date_of_birth, date.today())
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[{
                "loc": ["body", "date_of_birth"],
                "msg": str(error),
                "type": "value_error",
            }],
        ) from error
    try:
        validate_profile_location(payload.country, payload.city)
    except ValueError as error:
        field = "country" if payload.country not in {"US", "IN"} else "city"
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[{"loc": ["body", field], "msg": str(error), "type": "value_error"}],
        ) from error


def save_profile(
    db: Session,
    payload: ProfileCreateRequest,
    admin_id: int,
) -> UserProfile:
    profile = UserProfile(
        first_name=payload.first_name,
        last_name=payload.last_name,
        date_of_birth=payload.date_of_birth,
        email=str(payload.email).strip(),
        canonical_email=canonicalize_profile_email(str(payload.email)),
        country=payload.country,
        city=payload.city,
        created_by=admin_id,
    )
    db.add(profile)
    try:
        db.flush()
        record_audit(
            db,
            AuditEvent(
                admin_id=admin_id,
                action="PROFILE_CREATE",
                entity_type="user_profile",
                entity_id=profile.id,
            ),
        )
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=[{
                "loc": ["body", "email"],
                "msg": "A profile with this email already exists",
                "type": "duplicate_email",
            }],
        ) from error
    db.refresh(profile)
    return profile


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: ProfileCreateRequest,
    current_admin: CurrentAdmin,
    _csrf: CsrfProtected,
    db: Annotated[Session, Depends(get_db_session)],
) -> ProfileResponse:
    admin, _session = current_admin
    validate_profile_payload(payload)
    return profile_response(save_profile(db, payload, admin.id))


@router.get("", response_model=ProfilePage)
def list_profiles(
    _current_admin: CurrentAdmin,
    db: Annotated[Session, Depends(get_db_session)],
    q: Annotated[str | None, Query(max_length=100)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> ProfilePage:
    query = select(UserProfile)
    count_query = select(func.count()).select_from(UserProfile)
    if q:
        search = f"%{q.strip()}%"
        condition = or_(
            UserProfile.first_name.like(search),
            UserProfile.last_name.like(search),
        )
        query = query.where(condition)
        count_query = count_query.where(condition)
    total = db.scalar(count_query) or 0
    profiles = db.scalars(
        query.order_by(UserProfile.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return ProfilePage.from_items(
        [profile_response(profile) for profile in profiles],
        page,
        page_size,
        total,
    )


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(
    profile_id: int,
    _current_admin: CurrentAdmin,
    db: Annotated[Session, Depends(get_db_session)],
) -> ProfileResponse:
    profile = db.get(UserProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile_response(profile)
