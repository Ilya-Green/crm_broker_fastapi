import enum
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from babel import Locale
from pydantic import AnyHttpUrl, BaseModel, EmailStr, constr, validator
from pydantic import Field as PydField
from pydantic.color import Color
from sqlalchemy import JSON, Column, DateTime, Enum, String, Text

from sqlmodel import Field, Relationship, SQLModel, MetaData
from starlette_admin.i18n import get_countries_list


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"

# class ClientStatuses(SQLModel):


class ClientCreate(SQLModel):
    auth_key: str = Field()
    first_name: str = Field(min_length=3)
    email: EmailStr = Field()
    phone_number: str = Field(min_length=4, default="+1111111111")
    status_id: int = Field(default=1, description='1-lead,2-live,3-demo')

    title: Optional[str] = Field(min_length=3)
    # # login: Optional[str] = Field(min_length=3)
    second_name: Optional[str] = Field(min_length=3)
    patronymic: Optional[str] = Field(min_length=3)
    country_code: Optional[str] = Field(default="US", min_length=2, max_length=2)
    city: Optional[str] = Field(min_length=3)
    # # status_name: Optional[str] = Field(sa_column=Column(Enum(Gender)), default="hot")
    description: Optional[str] = Field(min_length=3)
    address: Optional[str] = Field(min_length=3)
    region: Optional[str] = Field(min_length=3)
    postcode: Optional[int] = Field()
    additional_contact: Optional[str] = Field(min_length=3)

    @validator("country_code")
    def validate_country_code(cls, value):
        locale = Locale.parse("en")  # Используйте нужную вам локаль
        countries_list = [x for x, _ in get_countries_list()]
        if value not in countries_list:
            raise ValueError("Недопустимый код страны")
        return value



class ClientList(SQLModel):
    auth_key: str = Field()
    use_pattern: bool = Field(default=0)
    admin_pattern_id: int = Field()
    user_pattern_id: int = Field()
    keyword: str = Field()
    offset: int = Field(default=-1)
    limit: int = Field(default=-1)
    pattern_check: str = Field()
    sorting_field: str = Field(default="id")
    sorting_order: str = Field(default="asc", description="asc or desc. forward or reverse order")
    ignoreClientIds: List[int] = Field()
    count: bool = Field(default=0)
