import enum
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Set, Union, Sequence
import secrets

from babel import Locale
from jinja2 import Template
from pydantic import AnyHttpUrl, BaseModel, EmailStr, constr, validator
from pydantic import Field as PydField
from pydantic.color import Color
from sqlalchemy import JSON, Column, DateTime, Enum, String, Text

from sqlmodel import Field, Relationship, SQLModel, MetaData
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from starlette_admin.i18n import get_countries_list

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = SQLModel.metadata
metadata.naming_convention = NAMING_CONVENTION

templates_dir = "starlette_admin/templates"
templates = Jinja2Templates(templates_dir, extensions=["jinja2.ext.i18n"])


class Employee(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    login: str = Field(min_length=3, unique=True)
    password: str = Field(min_length=8)

    name: Optional[str] = Field()
    session: Optional[str] = Field()

    role_id: Optional[int] = Field(foreign_key="role.id")
    role: "Role" = Relationship(back_populates="user")

    notes: "Note" = Relationship(back_populates="employee")

    RetainNotes: "RetainNote" = Relationship(back_populates="employee")

    desk_id: Optional[int] = Field(foreign_key="desk.id")
    desk: "Desk" = Relationship(back_populates="employee")

    clients_responsible: "Client" = Relationship(back_populates="responsible")

    traders_responsible: "Trader" = Relationship(back_populates="responsible")

    actions: "Action" = Relationship(back_populates="employee")

    department_id: Optional[int] = Field(foreign_key="department.id")
    department: "Department" = Relationship(back_populates="employee")

    affiliate: "Affiliate" = Relationship(back_populates="employee")

    async def __admin_repr__(self, request: Request):
        return str(self.login)


class Role(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    sys_admin: bool = Field(default=0)
    name: str = Field(default=0)
    head: bool = Field(default=0)
    department_leader: bool = Field(default=0)
    desk_leader: bool = Field(default=0)
    accounts_can_access: bool = Field(default=0)
    roles_can_access: bool = Field(default=0)
    affiliates_can_access: bool = Field(default=0)
    affiliates_can_view_details: bool = Field(default=0)
    affiliates_can_create: bool = Field(default=0)
    affiliates_can_edit: bool = Field(default=0)
    clients_can_access: bool = Field(default=0)
    clients_can_edit: bool = Field(default=0)
    can_change_balance: bool = Field(default=0)
    can_create_deposit: bool = Field(default=0)
    can_change_password: bool = Field(default=0)
    retain: bool = Field(default=0)
    orders_can_access: bool = Field(default=0)
    transactions_can_access: bool = Field(default=0)

    user: "Employee" = Relationship(back_populates="role")

    def to_dict(self):
        excluded_fields = ['id', 'name']
        data_dict = {field_name: getattr(self, field_name) for field_name in self.__fields__.keys() if
                     field_name not in excluded_fields}
        data_dict.update({'role': self.name})
        return data_dict

    async def __admin_repr__(self, request: Request):
        return str(self.name)


class Affiliate(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    name: Optional[str] = Field()
    auth_key: Optional[str] = Field(default=secrets.token_hex(32), unique=True)
    email: Optional[EmailStr] = Field()

    desk_id: Optional[int] = Field(foreign_key="desk.id")
    desk: "Desk" = Relationship(back_populates="affiliate")

    department_id: Optional[int] = Field(foreign_key="department.id")
    department: "Department" = Relationship(back_populates="affiliate2")

    employee_id: Optional[int] = Field(foreign_key="employee.id")
    employee: "Employee" = Relationship(back_populates="affiliate")

    clients: "Client" = Relationship(back_populates="affiliate")

    async def __admin_repr__(self, request: Request):
        return str(self.name)


class Client(SQLModel, table=True):
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
    is_archived: Optional[bool] = Field(default=False)

    creation_date: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True), default=datetime.utcnow))

    country_code: Optional[str] = Field()
    # country: Optional[str] = Field()

    type_id: Optional[int] = Field(foreign_key="type.id")
    type: "Type" = Relationship(back_populates="client")

    status_id: Optional[int] = Field(foreign_key="status.id")
    status: "Status" = Relationship(back_populates="client")

    notes: "Note" = Relationship(back_populates="client")
    last_note: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True)))

    desk_id: Optional[int] = Field(foreign_key="desk.id")
    desk: "Desk" = Relationship(back_populates="client")

    department_id: Optional[int] = Field(foreign_key="department.id")
    department: "Department" = Relationship(back_populates="clients")

    responsible_id: Optional[int] = Field(foreign_key="employee.id")
    responsible: "Employee" = Relationship(back_populates="clients_responsible")

    actions: "Action" = Relationship(back_populates="client")

    affiliate_id: Optional[int] = Field(foreign_key="affiliate.id")
    affiliate: Affiliate = Relationship(back_populates="clients")

    trader_id: Optional[str] = Field(foreign_key="trader.id")
    trader: "Trader" = Relationship(back_populates="client")

    @validator("country_code")
    def validate_country_code(cls, value):
        locale = Locale.parse("en")  # Используйте нужную вам локаль
        countries_list = [x for x, _ in get_countries_list()]
        if value not in countries_list:
            raise ValueError("Недопустимый код страны")
        return value

    async def __admin_repr__(self, request: Request):
        return str(self.email) + ": " + str(self.first_name) + " " + str(self.second_name)


class Trader(SQLModel, table=True):
    # id: Optional[str] = Field(primary_key=True)
    # name: Optional[str] = Field()
    # email: EmailStr = Field()
    # phone_number: str = Field()
    # balance: int = Field(default=0)
    # created_at_tp: Optional[datetime] = Field()
    id: Optional[str] = Field(primary_key=True, index=True)
    name: Optional[str] = Field()
    surname: Optional[str] = Field()
    email: Optional[EmailStr] = Field()
    phone_number: Optional[str] = Field()
    date: Optional[datetime] = Field()
    password: Optional[str] = Field()
    country: Optional[str] = Field()
    accountNumber: Optional[str] = Field()
    created_at_tp: Optional[datetime] = Field()
    balance: Optional[float] = Field()
    mainBalance: Optional[float] = Field()
    bonuses: Optional[float] = Field()
    credFacilities: Optional[float] = Field()
    accountStatus: Optional[str] = Field()
    blocked: Optional[bool] = Field()
    isActive: Optional[bool] = Field()
    isVipStatus: Optional[bool] = Field()
    orderisBlocked: Optional[bool] = Field()
    autologin: Optional[str] = Field()
    autologin_link: Optional[AnyHttpUrl] = Field()
    last_note: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True)))

    status_id: Optional[int] = Field(foreign_key="retainstatus.id")
    status: "RetainStatus" = Relationship(back_populates="traders")

    responsible_id: Optional[int] = Field(foreign_key="employee.id")
    responsible: "Employee" = Relationship(back_populates="traders_responsible")

    client: "Client" = Relationship(back_populates="trader")

    orders: "Order" = Relationship(back_populates="trader")

    transactions: "Transaction" = Relationship(back_populates="trader")

    notes: "RetainNote" = Relationship(back_populates="trader")

    async def __admin_repr__(self, request: Request):
        return str(self.email) + ": " + str(self.name) + " " + str(self.surname)

    async def __detail_repr__(self, obj: Any) -> str:
        template = templates.get_template("displays/trader.html")
        rendered_template = template.render(obj=self)
        return rendered_template


class Transaction(SQLModel, table=True):
    id: Optional[str] = Field(primary_key=True)
    content: Optional[str] = Field()
    createdAt: datetime = Field()
    dirName: Optional[str] = Field()
    type: str = Field()
    value: float = Field()
    v: Optional[int] = Field()

    trader_id: str = Field(foreign_key="trader.id")
    trader: "Trader" = Relationship(back_populates="transactions")

    async def __admin_repr__(self, request: Request):
        return str(self.value) + "$: " + str(self.type) + ": " + self.createdAt.strftime("%Y-%m-%d")


class Order(SQLModel, table=True):
    wid: Optional[str] = Field()
    id: Optional[str] = Field(primary_key=True)
    asset_name: str = Field()
    amount: float = Field()
    opening_price: float = Field()
    pledge: float = Field()
    type: str = Field()
    is_closed: bool = Field()
    created_at: Optional[datetime] = Field()
    take_profit: Optional[float] = Field()
    stop_loss: Optional[float] = Field()
    auto_close: bool = Field()
    v: Optional[int] = Field()
    closed_at: Optional[datetime] = Field()
    closed_price: Optional[float] = Field()
    profit: Optional[float] = Field()
    spread: Optional[float] = Field()

    user_id: Optional[str] = Field(foreign_key="trader.id")
    trader: "Trader" = Relationship(back_populates="orders")

    async def __admin_repr__(self, request: Request):
        return str(self.asset_name) + ": " + str(self.amount) + ": " + self.created_at.strftime("%m-%d %H:%M")


class Type(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    name: str = Field()

    client: Client = Relationship(back_populates="type")

    async def __admin_repr__(self, request: Request):
        return "id " + str(self.id) + ": " + str(self.name)


class Status(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    name: str = Field()
    hide: Optional[bool] = Field()

    client: Client = Relationship(back_populates="status")

    async def __admin_repr__(self, request: Request):
        return "id " + str(self.id) + ": " + str(self.name)


class RetainStatus(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    name: str = Field()
    hide: bool = Field(default=False)

    traders: Trader = Relationship(back_populates="status")

    async def __admin_repr__(self, request: Request):
        return "id " + str(self.id) + ": " + str(self.name)


class Action(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    starting_date: Optional[datetime] = Field()
    closing_date: Optional[datetime] = Field()
    type: Optional[str] = Field()
    description: Optional[str] = Field()
    status: Optional[str] = Field()

    # creator_id: Optional[int] = Field(foreign_key="employee.id")
    responsible_id: Optional[int] = Field(foreign_key="employee.id")

    employee: "Employee" = Relationship(back_populates="actions")

    client_id: Optional[int] = Field(foreign_key="client.id")
    client: Client = Relationship(back_populates="actions")


class Note(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    content: str = Field(sa_column=Column(Text))
    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=False), default=datetime.utcnow)
    )

    client_id: Optional[int] = Field(foreign_key="client.id")
    client: Client = Relationship(back_populates="notes")

    employee_name: Optional[str] = Field()
    employee_id: Optional[int] = Field(foreign_key="employee.id")
    employee: Employee = Relationship(back_populates="notes")

    async def __admin_repr__(self, request: Request):
        return self.created_at.strftime("%m-%d %H:%M") + ": " + str(self.employee_name) + ": " + str(self.content)

    async def __detail_repr__(self, obj: Any) -> str:
        template = templates.get_template("displays/notes.html")
        rendered_template = template.render(obj=self)
        outer_template = templates.get_template("displays/notes_wrapper.html")
        wrapped_template = outer_template.render(content=rendered_template)
        return wrapped_template


class RetainNote(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    content: str = Field(sa_column=Column(Text))
    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=False), default=datetime.utcnow)
    )

    trader_id: Optional[str] = Field(foreign_key="trader.id")
    trader: Trader = Relationship(back_populates="notes")

    employee_name: Optional[str] = Field()
    employee_id: Optional[int] = Field(foreign_key="employee.id")
    employee: Employee = Relationship(back_populates="RetainNotes")

    async def __admin_repr__(self, request: Request):
        return self.created_at.strftime("%m-%d %H:%M") + ": " + str(self.content)

    async def __detail_repr__(self, obj: Any) -> str:
        template = templates.get_template("displays/notes.html")
        rendered_template = template.render(obj=self)
        outer_template = templates.get_template("displays/notes_wrapper.html")
        wrapped_template = outer_template.render(content=rendered_template)
        return wrapped_template


class Desk(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    name: str = Field()
    description: Optional[str] = Field()
    creation_date: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True), default=datetime.utcnow))
    language_id: Optional[str] = Field()

    client: Client = Relationship(back_populates="desk")

    department_id: Optional[int] = Field(foreign_key="department.id", default=None)
    department: "Department" = Relationship(back_populates="desk")

    # responsible_id: Optional[int] = Field(foreign_key="employee.id")
    employee: Employee = Relationship(back_populates="desk")

    affiliate: "Affiliate" = Relationship(back_populates="desk")

    async def __admin_repr__(self, request: Request):
        return str(self.name)


class Department(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    name: str = Field()

    desk: Desk = Relationship(back_populates="department")

    employee: Employee = Relationship(back_populates="department")

    clients: Client = Relationship(back_populates="department")

    affiliate2: "Affiliate" = Relationship(back_populates="department")

    async def __admin_repr__(self, request: Request):
        return str(self.name)
