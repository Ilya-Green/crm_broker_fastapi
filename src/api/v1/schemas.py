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
from pydantic import Field as PydanticField

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


class ClientData(SQLModel):
    id: Optional[int] = Field(primary_key=True)

    first_name: str = Field(min_length=3)
    email: EmailStr = Field()

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


class ClientCreateOut(SQLModel):
    detail: str = Field(default="success")
    autologin: Optional[str] = Field()
    data: Optional[ClientData] = Field()


class ClientListIn(SQLModel):
    auth_key: str = Field()
    date_from: Optional[datetime] = Field(default="2024-01-08T18:00:20.385616+03:00")
    date_to: Optional[datetime] = Field(default="2024-02-08T18:00:20.385616+03:00")
    during_last_minutes: Optional[int] = Field()
    offset: Optional[int] = Field(default=0)
    limit: Optional[int] = Field(default=0)
    sorting_field: Optional[str] = Field(default="id")
    sorting_order: Optional[str] = Field(default="desc", description="asc or desc. forward or reverse order")
    ignoreClientIds: Optional[List[int]] = Field(default=[0])
    return_count: Optional[bool] = Field(default=0)


class ClientListInPydantic(BaseModel):
    auth_key: str = Field()
    date_from: Optional[datetime] = PydanticField(default=None, example="2024-01-08T18:00:20.385616+03:00")
    date_to: Optional[datetime] = PydanticField(default=None, example="2024-02-08T18:00:20.385616+03:00")
    during_last_minutes: Optional[int] = PydanticField()
    offset: Optional[int] = PydanticField(default=0)
    limit: Optional[int] = PydanticField(default=0)
    sorting_field: Optional[str] = PydanticField(default="id")
    sorting_order: Optional[str] = PydanticField(default="desc", description="asc or desc. forward or reverse order")
    ignoreClientIds: Optional[List[int]] = PydanticField(default=[0])
    return_count: Optional[bool] = PydanticField(default=0)


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
    count: Optional[int] = Field()
    data: Optional[List[ClientOut]] = Field()
