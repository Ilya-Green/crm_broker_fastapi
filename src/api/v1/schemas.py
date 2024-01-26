import enum
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union

from babel import Locale
from pydantic import AnyHttpUrl, BaseModel, EmailStr, constr, validator, IPvAnyAddress, AnyUrl
from pydantic import Field as PydField
from pydantic.color import Color
from sqlalchemy import JSON, Column, DateTime, Enum, String, Text

from sqlmodel import Field, Relationship, SQLModel, MetaData
from starlette_admin.i18n import get_countries_list

from src.models import Client, Status


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"

# class ClientStatuses(SQLModel):


class ClientCreateIn(SQLModel):
    auth_key: str = Field()
    first_name: str = Field(min_length=3)
    second_name: Optional[str] = Field(min_length=3)
    email: EmailStr = Field()
    phone_number: str = Field(min_length=4, default="+1111111111")

    ip: Optional[IPvAnyAddress] = Field(default="1.1.1.1")
    country_code: Optional[str] = Field(default="ZA", min_length=2, max_length=2)
    funnel_name: Optional[str] = Field(max_length=30)
    funnel_link: Optional[AnyUrl] = Field()
    patronymic: Optional[str] = Field(min_length=3)
    city: Optional[str] = Field(min_length=3)
    address: Optional[str] = Field(min_length=3)
    description: Optional[str] = Field(min_length=3)
    additional_contact: Optional[str] = Field(min_length=3)
    title: Optional[str] = Field(min_length=3)

    @validator("country_code")
    def validate_country_code(cls, value):
        locale = Locale.parse("en")  # Используйте нужную вам локаль
        countries_list = [x for x, _ in get_countries_list()]
        if value not in countries_list:
            raise ValueError("Недопустимый код страны")
        return value


class ClientCreateOut(SQLModel):
    detail: str = Field(default="success")
    autologin: Optional[str] = Field()


class ClientListIn(SQLModel):
    auth_key: str = Field()
    offset: int = Field(default=0)
    limit: int = Field(default=0)
    sorting_field: str = Field(default="id")
    sorting_order: str = Field(default="desc", description="asc or desc. forward or reverse order")
    ignoreClientIds: List[int] = Field()
    return_count: bool = Field(default=0)


class ClientOut(SQLModel):
    id: Optional[int] = Field(primary_key=True)
    first_name: str = Field(min_length=3)
    email: EmailStr = Field()
    phone_number: str = Field(min_length=4)

    ip: Optional[str] = Field()
    funnel_name: Optional[str] = Field()
    funnel_link: Optional[str] = Field()
    title: Optional[str] = Field()
    second_name: Optional[str] = Field()
    patronymic: Optional[str] = Field()
    city: Optional[str] = Field()
    description: Optional[str] = Field()
    address: Optional[str] = Field()
    additional_contact: Optional[str] = Field()
    creation_date: Optional[datetime] = Field()
    country_code: Optional[str] = Field()

    type_id: Optional[int] = Field()

    status: Optional[str] = Field()
    type: Optional[str] = Field()


class ClientListOut(SQLModel):
    detail: str = Field(default='success')
    data: List[ClientOut] = Field()
