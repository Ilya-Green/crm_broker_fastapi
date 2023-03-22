import enum
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Set, Union, Sequence
import secrets

from pydantic import AnyHttpUrl, BaseModel, EmailStr, constr
from pydantic import Field as PydField
from pydantic.color import Color
from sqlalchemy import JSON, Column, DateTime, Enum, String, Text

from sqlmodel import Field, Relationship, SQLModel, MetaData


class Employee(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    login: str = Field(min_length=3)
    password: str = Field(min_length=8)

    role_id: Optional[int] = Field(foreign_key="role.id")
    role: "Role" = Relationship(back_populates="user")

    notes: "Note" = Relationship(back_populates="employee")

    desk_id: Optional[int] = Field(foreign_key="desk.id")
    desk: "Desk" = Relationship(back_populates="responsible")

    clients_responsible: "Client" = Relationship(back_populates="responsible")

    actions: "Action" = Relationship(back_populates="employee")

    department_head: "Department" = Relationship(back_populates="head")


class Role(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    sys_admin: bool = Field(default=0)
    name: str = Field(default=0)
    head: bool = Field(default=0)
    desk_leader: bool = Field(default=0)
    accounts_can_access: bool = Field(default=0)
    roles_can_access: bool = Field(default=0)
    clients_can_access: bool = Field(default=0)

    user: "Employee" = Relationship(back_populates="role")

    def to_dict(self):
        excluded_fields = ['id', 'name']
        return {field_name: getattr(self, field_name) for field_name in self.__fields__.keys() if
                field_name not in excluded_fields} | {'role': self.name}


class Affiliate(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    name: Optional[str] = Field()
    auth_key: Optional[str] = Field(default=secrets.token_hex(32))


class Client(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    first_name: str = Field(min_length=3)
    email: EmailStr = Field()
    phone_number: str = Field(min_length=4)

    title: Optional[str] = Field()
    second_name: Optional[str] = Field()
    patronymic: Optional[str] = Field()
    country_id: Optional[int] = Field()
    city: Optional[str] = Field()
    status_name: Optional[str] = Field()
    description: Optional[str] = Field()
    address: Optional[str] = Field()
    region: Optional[str] = Field()
    postcode: Optional[int] = Field()
    additional_contact: Optional[str] = Field()

    creation_date: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True), default=datetime.utcnow))

    status_id: Optional[int] = Field(foreign_key="status.id")
    status: "Status" = Relationship(back_populates="client")

    notes: "Note" = Relationship(back_populates="client")

    desk_id: Optional[int] = Field(foreign_key="desk.id")
    desk: "Desk" = Relationship(back_populates="client")

    responsible_id: Optional[int] = Field(foreign_key="employee.id")
    responsible: "Employee" = Relationship(back_populates="clients_responsible")

    actions: "Action" = Relationship(back_populates="client")


class Status(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    name: str = Field()

    client: Client = Relationship(back_populates="status")


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
    content: str = Field(sa_column=Column(Text), min_length=5)
    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime(timezone=False), default=datetime.utcnow)
    )

    client_id: Optional[int] = Field(foreign_key="client.id")
    client: Client = Relationship(back_populates="notes")

    # employee_name: Optional[str] = Field()
    employee_id: Optional[int] = Field(foreign_key="employee.id")
    employee: Employee = Relationship(back_populates="notes")


class Desk(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    name: str = Field()
    description: Optional[str] = Field()
    creation_date: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=True), default=datetime.utcnow))
    language_id: Optional[int] = Field()

    client: Client = Relationship(back_populates="desk")

    department_id: Optional[int] = Field(foreign_key="department.id")
    department: "Department" = Relationship(back_populates="desk")

    # responsible_id: Optional[int] = Field(foreign_key="employee.id")
    responsible: Employee = Relationship(back_populates="desk")


class Department(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    name: str = Field()

    desk: Desk = Relationship(back_populates="department")

    head_id: Optional[int] = Field(foreign_key="employee.id")
    head: Employee = Relationship(back_populates="department_head")
