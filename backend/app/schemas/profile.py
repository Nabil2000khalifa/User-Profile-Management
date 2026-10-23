from datetime import date, datetime
from math import ceil

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ProfileCreateRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    email: EmailStr
    country: str = Field(min_length=2, max_length=2)
    city: str = Field(min_length=1, max_length=100)

    @field_validator("first_name", "last_name", "country", "city")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("This field is required")
        return trimmed


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    date_of_birth: date
    email: EmailStr
    country: str
    city: str
    created_at: datetime
    updated_at: datetime


class ProfilePage(BaseModel):
    items: list[ProfileResponse]
    page: int
    page_size: int
    total: int
    total_pages: int

    @classmethod
    def from_items(
        cls,
        items: list[ProfileResponse],
        page: int,
        page_size: int,
        total: int,
    ) -> "ProfilePage":
        return cls(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size) if total else 0,
        )
