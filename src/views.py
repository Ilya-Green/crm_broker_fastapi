import json
from datetime import datetime
import time

import anyio
import requests
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette_admin import (
    CollectionField,
    ColorField,
    EmailField,
    ExportType,
    IntegerField,
    JSONField,
    ListField,
    StringField,
    URLField,
    TextAreaField,
    HasMany,
    HasOne,
    CollectionField,
    DateTimeField, RequestAction,
    # PasswordField,
    CountryField,
    PhoneField,
    TimeField,
    TimeZoneField,
)
from starlette_admin.contrib.sqla.helpers import build_query, build_order_clauses
from starlette_admin.fields import FileField, RelationField, BooleanField
from .fields import PasswordField, CopyField, NotesField, EmailCopyField, StatusField, TraderField, ResponsibleField, \
    CustomPhoneField
from starlette_admin.contrib.sqlmodel import ModelView
from starlette.requests import Request
from sqlalchemy.orm import Session, joinedload, sessionmaker
from sqlmodel import Session, select
from starlette.requests import Request
from sqlalchemy import or_, and_
from typing import Optional, Dict, Union, Sequence
from starlette_admin import action
from typing import Any, List
from urllib.parse import urlparse, parse_qs
from starlette_admin import BaseField, RelationField
from dataclasses import dataclass
from starlette.datastructures import FormData
from starlette_admin.i18n import ngettext
from starlette_admin.i18n import lazy_gettext as _
from starlette.datastructures import FormData
from sqlalchemy.sql import Select
from sqlalchemy import func
from jinja2 import Template
from starlette_admin.exceptions import ActionFailed, FormValidationError
import aiohttp
import asyncio
import logging
from sqlalchemy import select as sqlalchemy_select

from starlette_admin.helpers import html_params
from .models import Employee, Role, Client, Desk, Affiliate, Department, Note, Trader, Order, Transaction, Status
from . import engine
from .platfrom_integration import update_platform_data, edit_account_platform, change_account_password_platform, \
    update_order, edit_order_platform, update_orders, update_platform_data_by_id

logger = logging.getLogger("api")


class MyModelView(ModelView):
    include_relationships: bool = True
    page_size = 20
    page_size_options = [5, 10, 25, 50, 100, 500, 1000]
    export_types = []


class EmployeeView(MyModelView):
    async def select2_result(self, obj: Any, request: Request) -> str:
        """
        Override this function to customize the way that search results are rendered.
        !!! note
            The returned value should be html. You can use `<span>mytext</span>`
            when you want to return string value
        !!! danger
            Escape your database value to avoid Cross-Site Scripting (XSS) attack.
            You can use Jinja2 Template render with `autoescape=True`.
            For more information [click here](https://owasp.org/www-community/attacks/xss/)

        Parameters:
            obj: item returned by `find_all` or `find_by_pk`
            request: Starlette Request

        """
        template_str = (
            "<span>{%for col in fields %}{%if obj[col]%}<strong>{{col}}:"
            " </strong>{{obj[col]}} {%endif%}{%endfor%}</span>"
        )
        fields = [
            field.name
            for field in self.fields
            if not isinstance(field, (RelationField, FileField, PasswordField))
        ]
        return Template(template_str, autoescape=True).render(obj=obj, fields=fields)

    list_template = "employee_list_template.html"

    responsive_table = True
    column_visibility = True
    search_builder = True

    def is_accessible(self, request: Request) -> bool:
        self.id = request.state.user["id"]
        self.desk_id = request.state.user["desk_id"]
        self.department_id = request.state.user["department_id"]
        self.desk_leader = request.state.user["desk_leader"]
        self.department_leader = request.state.user["department_leader"]
        self.head = request.state.user["head"]
        self.sys_admin = request.state.user["sys_admin"]
        self.retain = request.state.user["retain"]

        if "accounts_can_access" in request.state.user:
            if request.state.user["sys_admin"] is True:
                return True
        if "accounts_can_access" in request.state.user:
            if request.state.user["head"] is True:
                return True
        if "accounts_can_access" in request.state.user:
            if request.state.user["department_leader"] is True:
                return True
        if "accounts_can_access" in request.state.user:
            if request.state.user["desk_leader"] is True:
                return True
        return False

    def get_list_query(self):
        if self.sys_admin:
            return super().get_list_query()
        if self.head:
            if self.retain:
                return super().get_list_query().where(Employee.role_id != 1)
        if self.head:
            return super().get_list_query().where(Employee.role_id != 1).where(Employee.role_id != 7)
        if self.department_leader:
            return super().get_list_query().where(Employee.role_id != 1).where(Employee.department_id != 0).where(Employee.department_id == self.department_id).where(Employee.role_id != 7)
        if self.desk_leader:
            return super().get_list_query().where(Employee.role_id != 1).where(Employee.desk_id != 0).where(Employee.department_id == self.department_id).where(Employee.desk_id == self.desk_id).where(Employee.role_id != 7)

    def get_count_query(self) -> Select:
        if self.sys_admin:
            return super().get_count_query()
        if self.head:
            if self.retain:
                return super().get_count_query().where(Employee.role_id != 1)
        if self.head:
            return super().get_count_query().where(Employee.role_id != 1).where(Employee.role_id != 7)
        if self.department_leader:
            return super().get_count_query().where(Employee.role_id != 1).where(Employee.department_id != 0).where(Employee.department_id == self.department_id)
        if self.desk_leader:
            return super().get_count_query().where(Employee.role_id != 1).where(Employee.desk_id != 0).where(Employee.department_id == self.department_id).where(Employee.desk_id == self.desk_id)

    def can_edit(self, request: Request) -> bool:
        if "accounts_can_access" in request.state.user:
            if request.state.user["sys_admin"] is True:
                return True

    def can_create(self, request: Request) -> bool:
        if "accounts_can_access" in request.state.user:
            if request.state.user["sys_admin"] is True:
                return True
        if "accounts_can_access" in request.state.user:
            if request.state.user["head"] is True:
                return True

    def can_delete(self, request: Request) -> bool:
        if "accounts_can_access" in request.state.user:
            if request.state.user["sys_admin"] is True:
                return True

    # def can_view_details(self, request: Request) -> bool:
    #     if "accounts_can_access" in request.state.user:
    #         if request.state.user["sys_admin"] is True:
    #             return True

    @action(
        name="set_role",
        text="Set Role",
        confirmation="Enter the role id",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        #         <input name="id" class="form-control" id="floating-input" value="">
        form="""<div class="input-group input-group-sm mb-3">,
                <div class="input-group-prepend">
                <span class="input-group-text" id="inputGroup-sizing-sm">id:</span>
                </div>
                <input  name="id" type="text" class="form-control" aria-label="Small" aria-describedby="inputGroup-sizing-sm">
                </div>""",
    )
    async def set_role(self, request: Request, pks: List[Any]) -> str:
        session: Session = request.state.session
        for Employee in await self.find_by_pks(request, pks):
            Employee.role_id = request.query_params["id"]
            session.add(Employee)
        session.commit()
        return "{} employee were successfully changed to role with id: {}".format(
            len(pks), request.query_params["id"]
        )

    @action(
        name="set_department",
        text="Set department",
        confirmation="Enter the department id",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        #         <input name="id" class="form-control" id="floating-input" value="">
        form="""<div class="input-group input-group-sm mb-3">,
            <div class="input-group-prepend">
            <span class="input-group-text" id="inputGroup-sizing-sm">id:</span>
            </div>
            <input  name="id" type="text" class="form-control" aria-label="Small" aria-describedby="inputGroup-sizing-sm">
            </div>""",
    )
    async def set_department(self, request: Request, pks: List[Any]) -> str:
        session: Session = request.state.session
        for Employee in await self.find_by_pks(request, pks):
            Employee.department_id = request.query_params["id"]
            session.add(Employee)
        session.commit()
        return "{} clients were successfully changed to department with id: {}".format(
            len(pks), request.query_params["id"]
        )

    @action(
        name="set_desk",
        text="Set desk",
        confirmation="Enter the desk id",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        #         <input name="id" class="form-control" id="floating-input" value="">
        form="""<div class="input-group input-group-sm mb-3">,
               <div class="input-group-prepend">
               <span class="input-group-text" id="inputGroup-sizing-sm">id:</span>
               </div>
               <input  name="id" type="text" class="form-control" aria-label="Small" aria-describedby="inputGroup-sizing-sm">
               </div>""",
    )
    async def set_desk(self, request: Request, pks: List[Any]) -> str:
        if self.department_leader:
            with Session(engine) as session:
                statement = select(Desk).where(Desk.id == request.query_params["id"])
                desk_result = session.exec(statement).first()
                if desk_result.department_id != request.state.user["department_id"]:
                    raise ActionFailed("ID not from your department")
        session: Session = request.state.session

        for Employee in await self.find_by_pks(request, pks):
            Employee.desk_id = request.query_params["id"]
            session.add(Employee)
        session.commit()
        return "{} clients were successfully changed to desk with id: {}".format(
            len(pks), request.query_params["id"]
        )

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        if name == "set_role":
            if request.state.user["sys_admin"]:
                return True
            return False
        if name == "set_department":
            if request.state.user["sys_admin"]:
                return True
            if request.state.user["head"]:
                return True
            return False
        if name == "set_desk":
            if request.state.user["sys_admin"]:
                return True
            if request.state.user["head"]:
                return True
            if request.state.user["department_leader"]:
                return True
            return False
        if name == "delete":
            return self.can_delete(request)
        return True


    fields = [
        Employee.id,
        Employee.login,
        PasswordField("password"),
        Employee.role,
        Employee.desk,
        # Employee.clients_responsible,
        Employee.department,
        # Employee.notes,
        Employee.actions,
    ]

    exclude_fields_from_create = [Employee.actions, Employee.notes]
    # exclude_fields_from_list = [Employee.password]
    # exclude_fields_from_detail = [Employee.password]
    # exc

    # def get_list_query(self):
    #     if self.sys_admin:
    #         return super().get_list_query()
        # if self.head:
        #     # test = super().get_list_query().where(Desk.department_id == self.department_id)
        #     return super().get_list_query()
        # if self.department_leader:
        #     return super().get_list_query().where(Client.desk_id.in_(self.department_desks))
        # if self.desk_leader:
        #     return super().get_list_query().where((Client.desk_id == self.desk_id))
        # return super().get_list_query().where(Client.responsible_id == self.id).where(Client.desk_id == self.desk_id)


class RolesView(MyModelView):
    responsive_table = True
    column_visibility = True
    search_builder = True

    def is_accessible(self, request: Request) -> bool:
        if "roles_can_access" in request.state.user:
            if request.state.user["sys_admin"] is True:
                return True
        return False


class DepartmentsView(MyModelView):
    responsive_table = True
    column_visibility = True
    search_builder = True

    def is_accessible(self, request: Request) -> bool:
        self.id = request.state.user["id"]
        self.desk_id = request.state.user["desk_id"]
        self.department_id = request.state.user["department_id"]
        self.desk_leader = request.state.user["desk_leader"]
        self.department_leader = request.state.user["department_leader"]
        self.head = request.state.user["head"]
        self.sys_admin = request.state.user["sys_admin"]

        if request.state.user["sys_admin"] is True:
            return True
        if request.state.user["head"] is True:
            return True
        if request.state.user["department_leader"] is True:
            return True
        return False

    def can_edit(self, request: Request) -> bool:
        if "accounts_can_access" in request.state.user:
            if request.state.user["sys_admin"] is True:
                return True
        if "accounts_can_access" in request.state.user:
            if request.state.user["head"] is True:
                return True

    def can_create(self, request: Request) -> bool:
        if "accounts_can_access" in request.state.user:
            if request.state.user["sys_admin"] is True:
                return True
        if "accounts_can_access" in request.state.user:
            if request.state.user["head"] is True:
                return True

    def can_delete(self, request: Request) -> bool:
        if "accounts_can_access" in request.state.user:
            if request.state.user["sys_admin"] is True:
                return True
        if "accounts_can_access" in request.state.user:
            if request.state.user["head"] is True:
                return True

    def get_list_query(self):
        if self.sys_admin:
            return super().get_list_query()
        if self.head:
            return super().get_list_query()
        if self.department_leader:
            return super().get_list_query().where(Department.id == self.department_id)

    # fields = [
    #     Department.name,
    #     Department.desk,
    #     Department.employee,
    #     Department.clients,
    # ]


class DesksView(MyModelView):
    responsive_table = True
    column_visibility = True
    search_builder = True

    def is_accessible(self, request: Request) -> bool:
        self.id = request.state.user["id"]
        self.desk_id = request.state.user["desk_id"]
        self.department_id = request.state.user["department_id"]
        self.desk_leader = request.state.user["desk_leader"]
        self.department_leader = request.state.user["department_leader"]
        self.head = request.state.user["head"]
        self.sys_admin = request.state.user["sys_admin"]
        # self.department_head = request.state.user["department_head"]

        if request.state.user["sys_admin"] is True:
            return True
        if request.state.user["head"] is True:
            return True
        if request.state.user["department_leader"] is True:
            return True
        if request.state.user["desk_leader"] is True:
            return True
        return False

    def can_edit(self, request: Request) -> bool:
        if request.state.user["sys_admin"] is True:
            return True
        if request.state.user["head"] is True:
            return True
        if request.state.user["department_leader"] is True:
            return True

    def can_create(self, request: Request) -> bool:
        if request.state.user["sys_admin"] is True:
            return True
        if request.state.user["head"] is True:
            return True
        if request.state.user["department_leader"] is True:
            return True

    def can_delete(self, request: Request) -> bool:
        if request.state.user["sys_admin"] is True:
            return True
        if request.state.user["head"] is True:
            return True
        if request.state.user["department_leader"] is True:
            return True

    def get_list_query(self):
        if self.sys_admin:
            return super().get_list_query()
        if self.head:
            return super().get_list_query()
        if self.department_leader:
            return super().get_list_query().where(Desk.department_id == self.department_id)
        if self.desk_leader:
            return super().get_list_query().where(Desk.department_id == self.department_id).where(Desk.id == self.desk_id)


    def get_count_query(self):
        if self.sys_admin:
            return super().get_count_query()
        if self.head:
            return super().get_count_query()
        if self.department_leader:
            return super().get_count_query().where(Desk.department_id == self.department_id)
        if self.desk_leader:
            return super().get_count_query().where(Desk.id == self.desk_id)

    exclude_fields_from_create = [Desk.creation_date]
    exclude_fields_from_edit = [Desk.creation_date]


class AffiliatesView(MyModelView):
    exclude_fields_from_create = [Affiliate.auth_key]

    fields = [
        Affiliate.id,
        Affiliate.name,
        CopyField("auth_key"),
        Affiliate.clients,
    ]

    def is_accessible(self, request: Request) -> bool:
        if request.state.user["sys_admin"] is True:
            return True
        return False


class TradersView(MyModelView):
    detail_template: str = "trader_detail.html"

    # responsive_table = True
    column_visibility = True
    search_builder = True

    def is_accessible(self, request: Request) -> bool:
        referer_url = urlparse(request.headers.get("referer"))
        query_dict = parse_qs(referer_url.query)
        self.query = query_dict
        self.id = request.state.user["id"]
        self.desk_id = request.state.user["desk_id"]
        self.department_id = request.state.user["department_id"]
        self.desk_leader = request.state.user["desk_leader"]
        self.department_leader = request.state.user["department_leader"]
        self.head = request.state.user["head"]
        self.sys_admin = request.state.user["sys_admin"]
        self.retain = request.state.user["retain"]

        with Session(engine) as session:
            statement = select(Desk).where(Desk.department_id == request.state.user["department_id"])
            desks = session.exec(statement).all()
            # self.department_desks = desks
            self.department_desks = [desk.id for desk in desks]
        # self.role_name = request.state.user["id"]

        if request.state.user["sys_admin"] is True:
            return True
        if request.state.user["retain"] is True:
            return True
        return False

    def can_create(self, request: Request) -> bool:
        if request.state.user["sys_admin"] is True:
            return True

    def can_edit(self, request: Request) -> bool:
        ids = [request.path_params.get("pk")]
        update_platform_data_by_id(ids)
        if request.state.user["sys_admin"] is True:
            return True
        if request.state.user["head"] is True:
            return True
        if request.state.user["retain"] is True:
            return True

    def can_delete(self, request: Request) -> bool:
        if request.state.user["sys_admin"] is True:
            return True

    def can_view_details(self, request: Request) -> bool:
        return True

    def get_list_query(self):
        update_platform_data()
        if self.sys_admin:
            return super().get_list_query()
        if self.head:
            return super().get_list_query()
        if self.retain:
            return super().get_list_query().where(Trader.responsible_id == self.id)

    def get_count_query(self):
        # update_platform_data()
        if self.sys_admin:
            return super().get_count_query()
        if self.head:
            return super().get_count_query()
        if self.retain:
            return super().get_count_query().where(Trader.responsible_id == self.id)

    # fields = [
    #     Trader.
    # ]

    fields = [
        Trader.name,
        Trader.surname,
        Trader.email,
        Trader.phone_number,
        Trader.date,
        Trader.country,
        Trader.created_at_tp,
        Trader.balance,
        Trader.status,
        Trader.responsible,
        Trader.client,
        Trader.orders,
        Trader.bonuses,
        Trader.credFacilities,
        Trader.mainBalance,
        Trader.accountStatus,
        Trader.blocked,
        Trader.isActive,
        Trader.isVipStatus,
        URLField("autologin_link"),
        # Trader.autologin_link,
        Trader.autologin,
        Trader.transactions,
    ]

    exclude_fields_from_list = [
        Trader.password,
        Trader.accountNumber,
    ]
    exclude_fields_from_edit = [
        # Trader.email,
        # Trader.phone_number,
        Trader.created_at_tp,
        Trader.orders,
        Trader.password,
        Trader.bonuses,
        Trader.credFacilities,
        Trader.autologin,
        Trader.autologin_link,
        Trader.date,
        Trader.mainBalance,
        Trader.balance,
        Trader.transactions,
    ]
    # exclude_fields_from_create = [
    #     Client.notes,
    #     Client.creation_date,
    #     Client.actions,
    # ]

    # async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
    #     try:
    #         data = await self._arrange_data(request, data, True)
    #         await self.validate(request, data)
    #         session: Union[Session, AsyncSession] = request.state.session
    #         obj = await self.find_by_pk(request, pk)
    #         session.add(await self._populate_obj(request, obj, data, True))
    #         if isinstance(session, AsyncSession):
    #             await session.commit()
    #             await session.refresh(obj)
    #         else:
    #             await anyio.to_thread.run_sync(session.commit)
    #             await anyio.to_thread.run_sync(session.refresh, obj)
    #         return obj
    #     except Exception as e:
    #         self.handle_exception(e)

    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
    ) -> Sequence[Any]:
        session: Union[Session, AsyncSession] = request.state.session
        stmt = self.get_list_query().offset(skip)
        if limit > 0:
            stmt = stmt.limit(limit)
        if where is not None:
            if isinstance(where, dict):
                where = build_query(where, self.model)
            else:
                where = await self.build_full_text_search_query(
                    request, where, self.model
                )
            stmt = stmt.where(where)  # type: ignore
        stmt = stmt.order_by(*build_order_clauses(order_by or [], self.model))
        # for field in self.fields:
        #     if isinstance(field, RelationField) and not field.exclude_from_edit:
        #         stmt = stmt.options(joinedload(getattr(self.model, field.name)))

        if isinstance(session, AsyncSession):
            item = (await session.execute(stmt)).scalars().unique().all()
        items = (
            (await anyio.to_thread.run_sync(session.execute, stmt))
            .scalars()
            .unique()
            .all()
        )
        # ids = []
        # for trader in items:
        #     ids.append(trader.id)
        # update_platform_data_by_id(ids)
        return items

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        try:
            data = await self._arrange_data(request, data, True)
            await self.validate(request, data)
            session: Union[Session, AsyncSession] = request.state.session
            obj = await self.find_by_pk(request, pk)

            session.add(await self._populate_obj(request, obj, data, True))
            obj = await self._populate_obj(request, obj, data, True)
            edit_account_platform(await self._populate_obj(request, obj, data, True))
            if isinstance(session, AsyncSession):
                await session.commit()
                await session.refresh(obj)
            else:
                await anyio.to_thread.run_sync(session.commit)
                await anyio.to_thread.run_sync(session.refresh, obj)
            return obj
        except Exception as e:
            self.handle_exception(e)

    @action(
        name="change_responsible",
        text="Change responsible",
        confirmation="Enter the user id you want to assign as responsible",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        #         <input name="id" class="form-control" id="floating-input" value="">
        form="""<div class="input-group input-group-sm mb-3">,
        <div class="input-group-prepend">
        <span class="input-group-text" id="inputGroup-sizing-sm">id:</span>
        </div>
        <input  name="id" type="text" class="form-control" aria-label="Small" aria-describedby="inputGroup-sizing-sm">
        </div>""",
    )
    async def change_responsible(self, request: Request, pks: List[Any]) -> str:
        # with Session(engine) as session:
        #     statement = select(Employee).where(Employee.id == request.query_params["id"])
        #     desk_result = session.exec(statement).first()
        #     if self.desk_leader:
        #         if desk_result.desk_id != request.state.user["desk_id"] or desk_result.department_id != request.state.user["department_id"]:
        #             raise ActionFailed("ID not from your desk or department")
        #     if self.department_leader:
        #         if desk_result.department_id != request.state.user["department_id"]:
        #             raise ActionFailed("ID not from your department")
        session: Session = request.state.session
        for trader in await self.find_by_pks(request, pks):
            responsible_id = request.query_params["id"]
            trader.responsible_id = responsible_id
            session.commit()
            with Session(engine) as sqltable_session:
                statement = select(Client).where(Client.trader_id == trader.id)
                resp_client = sqltable_session.exec(statement).first()
            if resp_client:
                resp_client.responsible_id = responsible_id
                session.add(trader)
                print('test')
                with Session(engine) as sqltable_session:
                    sqltable_session.add(resp_client)
                    sqltable_session.commit()
        return "{} clients were successfully changed to responsible with id: {}".format(
            len(pks), request.query_params["id"]
        )

    @action(
        name="change_password",
        text="Change password",
        confirmation="Enter the password you want to set",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        #         <input name="id" class="form-control" id="floating-input" value="">
        form="""<div class="input-group input-group-sm mb-3">,
            <div class="input-group-prepend">
            <span class="input-group-text" id="inputGroup-sizing-sm">password:</span>
            </div>
            <input  name="password" type="text" class="form-control" aria-label="Small" aria-describedby="inputGroup-sizing-sm">
            </div>""",
    )
    async def change_password(self, request: Request, pks: List[Any]) -> str:
        # with Session(engine) as session:
        #     statement = select(Employee).where(Employee.id == request.query_params["id"])
        #     desk_result = session.exec(statement).first()
        #     if self.desk_leader:
        #         if desk_result.desk_id != request.state.user["desk_id"] or desk_result.department_id != request.state.user["department_id"]:
        #             raise ActionFailed("ID not from your desk or department")
        #     if self.department_leader:
        #         if desk_result.department_id != request.state.user["department_id"]:
        #             raise ActionFailed("ID not from your department")
        session: Session = request.state.session
        for Trader in await self.find_by_pks(request, pks):
            change_account_password_platform(Trader, request.query_params["password"])
        return "{} passwords were successfully set".format(
            len(pks)
        )

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        if name == "change_responsible":
            if request.state.user["sys_admin"]:
                return True
            if request.state.user["head"]:
                return True
            return False
        if name == "delete":
            return self.can_delete(request)
        return True


class TransactionsView(MyModelView):
    # responsive_table = True
    column_visibility = True
    search_builder = True

    def is_accessible(self, request: Request) -> bool:
        referer_url = urlparse(request.headers.get("referer"))
        query_dict = parse_qs(referer_url.query)
        self.query = query_dict
        self.id = request.state.user["id"]
        self.desk_id = request.state.user["desk_id"]
        self.department_id = request.state.user["department_id"]
        self.desk_leader = request.state.user["desk_leader"]
        self.department_leader = request.state.user["department_leader"]
        self.head = request.state.user["head"]
        self.sys_admin = request.state.user["sys_admin"]
        self.retain = request.state.user["retain"]

        with Session(engine) as session:
            statement = select(Desk).where(Desk.department_id == request.state.user["department_id"])
            desks = session.exec(statement).all()
            # self.department_desks = desks
            self.department_desks = [desk.id for desk in desks]
        # self.role_name = request.state.user["id"]

        if request.state.user["sys_admin"] is True:
            return True
        if request.state.user["retain"] is True:
            return True
        return False

    def can_create(self, request: Request) -> bool:
        if request.state.user["sys_admin"] is True:
            return True

    def can_edit(self, request: Request) -> bool:
        update_platform_data()
        if request.state.user["sys_admin"] is True:
            return True
        if request.state.user["head"] is True:
            return True
        if request.state.user["retain"] is True:
            return True

    def can_delete(self, request: Request) -> bool:
        if request.state.user["sys_admin"] is True:
            return True

    def can_view_details(self, request: Request) -> bool:
        return True

    def get_list_query(self):
        update_platform_data()
        return super().get_list_query()
    #     if self.sys_admin:
    #         return super().get_list_query()
    #     if self.head:
    #         return super().get_list_query()
    #     if self.retain:
    #         return super().get_list_query().where(Trader.responsible_id == self.id)
    #
    # def get_count_query(self):
    #     # update_platform_data()
    #     return super().get_list_query()
    #     if self.sys_admin:
    #         return super().get_count_query()
    #     if self.head:
    #         return super().get_count_query()
    #     if self.retain:
    #         return super().get_count_query().where(Trader.responsible_id == self.id)

    fields = [
        TraderField("trader"),
        Transaction.createdAt,
        Transaction.type,
        Transaction.value,
        Transaction.id,
        Transaction.trader,
    ]

    async def create(self, request: Request, data: Dict[str, Any]) -> Any:
        try:
            data = await self._arrange_data(request, data)
            await self.validate(request, data)
            session: Union[Session, AsyncSession] = request.state.session
            obj = await self._populate_obj(request, self.model(), data)
            session.add(obj)
            if isinstance(session, AsyncSession):
                await session.commit()
                await session.refresh(obj)
            else:
                await anyio.to_thread.run_sync(session.commit)
                await anyio.to_thread.run_sync(session.refresh, obj)
            return obj
        except Exception as e:
            return self.handle_exception(e)


class OrdersView(MyModelView):
    # responsive_table = True
    column_visibility = True
    search_builder = True

    def is_accessible(self, request: Request) -> bool:
        referer_url = urlparse(request.headers.get("referer"))
        query_dict = parse_qs(referer_url.query)
        self.query = query_dict
        self.id = request.state.user["id"]
        self.desk_id = request.state.user["desk_id"]
        self.department_id = request.state.user["department_id"]
        self.desk_leader = request.state.user["desk_leader"]
        self.department_leader = request.state.user["department_leader"]
        self.head = request.state.user["head"]
        self.sys_admin = request.state.user["sys_admin"]
        self.retain = request.state.user["retain"]

        with Session(engine) as session:
            statement = select(Desk).where(Desk.department_id == request.state.user["department_id"])
            desks = session.exec(statement).all()
            # self.department_desks = desks
            self.department_desks = [desk.id for desk in desks]
        # self.role_name = request.state.user["id"]

        with Session(engine) as session:
            statement = select(Trader).where(Trader.responsible_id == request.state.user["id"])
            traders = session.exec(statement).all()
            self.responsible_user_ids = [trader.id for trader in traders]

        if request.state.user["sys_admin"] is True:
            return True
        if request.state.user["retain"] is True:
            return True
        return False

    def can_create(self, request: Request) -> bool:
        if request.state.user["sys_admin"] is True:
            return True

    def can_edit(self, request: Request) -> bool:
        url = str(request.url)
        parsed_url = urlparse(url)
        path_segments = parsed_url.path.split("/")
        id_value = path_segments[-1]
        update_order(id_value)
        if request.state.user["sys_admin"] is True:
            return True
        if request.state.user["retain"] is True:
            return True

    def can_delete(self, request: Request) -> bool:
        if request.state.user["sys_admin"] is True:
            return True

    def can_view_details(self, request: Request) -> bool:
        return True

    fields = [
        TraderField("trader"),

        Order.asset_name,
        Order.amount,
        Order.opening_price,
        Order.closed_price,
        Order.type,
        Order.pledge,
        Order.is_closed,
        Order.created_at,
        Order.closed_at,
        Order.auto_close,
        Order.take_profit,
        Order.stop_loss,
        Order.trader,
    ]

    exclude_fields_from_list = [
        Order.id,
        Order.wid,
        Order.v,
    ]
    # exclude_fields_from_edit = [
    #     Trader.email,
    #     Trader.phone_number,
    #     Trader.created_at_tp,
    #     Trader.orders,
    # ]

    def get_list_query(self):
        update_orders()
        if self.sys_admin:
            return super().get_list_query()
        if self.head:
            return super().get_list_query()
        if self.retain:
            return super().get_list_query().where(Order.user_id.in_(self.responsible_user_ids))

    def get_count_query(self):
        # update_platform_data()
        if self.sys_admin:
            return super().get_count_query()
        if self.head:
            return super().get_count_query()
        if self.retain:
            return super().get_count_query().where(Order.user_id.in_(self.responsible_user_ids))

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        try:
            data = await self._arrange_data(request, data, True)
            await self.validate(request, data)
            session: Union[Session, AsyncSession] = request.state.session
            obj = await self.find_by_pk(request, pk)

            session.add(await self._populate_obj(request, obj, data, True))
            obj = await self._populate_obj(request, obj, data, True)
            edit_order_platform(await self._populate_obj(request, obj, data, True))
            if isinstance(session, AsyncSession):
                await session.commit()
                await session.refresh(obj)
            else:
                await anyio.to_thread.run_sync(session.commit)
                await anyio.to_thread.run_sync(session.refresh, obj)
            return obj
        except Exception as e:
            self.handle_exception(e)



class ClientsView(MyModelView):
    page_size_options = [5, 10, 25, 50, 100, 500, 1000]

    list_template = "client_list_template.html"
    detail_template: str = "clients_detail.html"

    fields_default_sort = ["id", ("id", True)]

    def custom_render_js(self, request: Request) -> Optional[str]:
        return request.url_for("statics", path="js/custom_render.js")

    # responsive_table = True
    column_visibility = True
    search_builder = True

    def is_accessible(self, request: Request) -> bool:
        referer_url = urlparse(request.headers.get("referer"))
        query_dict = parse_qs(referer_url.query)
        self.query = query_dict
        self.id = request.state.user["id"]
        self.desk_id = request.state.user["desk_id"]
        self.department_id = request.state.user["department_id"]
        self.desk_leader = request.state.user["desk_leader"]
        self.department_leader = request.state.user["department_leader"]
        self.head = request.state.user["head"]
        self.sys_admin = request.state.user["sys_admin"]
        self.retain = request.state.user["retain"]
        self.query_test = request.query_params

        with Session(engine) as session:
            statement = select(Desk).where(Desk.department_id == request.state.user["department_id"])
            desks = session.exec(statement).all()
            # self.department_desks = desks
            self.department_desks = [desk.id for desk in desks]
        # self.role_name = request.state.user["id"]

        if "clients_can_access" in request.state.user:
            if request.state.user["clients_can_access"] is True:
                return True
        if "retain" in request.state.user:
            if request.state.user["retain"] is True:
                return True
        return False

    def can_edit(self, request: Request) -> bool:
        if request.state.user["sys_admin"] is True:
            return True
        if request.state.user["head"] is True:
            return True

    def can_delete(self, request: Request) -> bool:
        if request.state.user["sys_admin"] is True:
            return True
        if request.state.user["head"] is True:
            return True

    # def can_change_responsible(self, request: Request) -> bool:
    #     if request.state.user["sys_admin"] is True:
    #         return True
    #     if request.state.user["head"] is True:
    #         return True
    #     if request.state.user["desk_leader"] is True:
    #         return True
    #     if request.state.user["head"] is True:
    #         return True
    #     return False

    def get_list_query(self):

        if "hide" not in self.query:
            with Session(engine) as session:
                statement = select(Status).where(Status.hide == False)
                statuses = session.exec(statement).all()
                exc_statuses = [status.id for status in statuses]
            query = super().get_list_query().where(or_(Client.status_id.in_(exc_statuses), Client.status_id.is_(None)))
        else:
            query = super().get_list_query()

        if "responsible_id" in self.query:
            query = query.where(Client.responsible_id == self.query["responsible_id"][0])
        if "status_id" in self.query:
            query = query.where(Client.status_id == self.query["status_id"][0])
        if self.sys_admin:
            return query
        if self.head:
            # test = super().get_list_query().where(Desk.department_id == self.department_id)
            return query
        if self.department_leader:
            query = query.where(Client.department_id != 0).where(Client.department_id == self.department_id)
            return query
        if self.desk_leader:
            query = query.where(Client.desk_id != 0).where(Client.department_id == self.department_id).where(Client.desk_id == self.desk_id)
            return query
        query = query.where(Client.department_id != 0).where(Client.desk_id != 0).where(Client.department_id == self.department_id).where(Client.desk_id == self.desk_id).where(Client.responsible_id == self.id)
        return query

    def get_count_query(self) -> Select:
        if "hide" not in self.query:
            with Session(engine) as session:
                statement = select(Status).where(Status.hide == False)
                statuses = session.exec(statement).all()
                exc_statuses = [status.id for status in statuses]
            query = super().get_count_query().where(or_(Client.status_id.in_(exc_statuses), Client.status_id.is_(None)))
        else:
            query = super().get_count_query()
        if "responsible_id" in self.query:
            query = query.where(Client.responsible_id == self.query["responsible_id"][0])
        if "status_id" in self.query:
            query = query.where(Client.status_id == self.query["status_id"][0])
        if self.sys_admin:
        #     if self.query:
        #         query = super().get_list_query()
        #         for key, value in self.query.items():
        #             # query = query.where(Client.key == 'HOT')
        #             query = query.where(getattr(Client, key).in_(value))
        #         return query
        #     else:
        #         return super().get_list_query()
            return query
        # if self.head:
        #     with Session(engine) as session:
        #         statement = select(Desk).where(Desk.department_id == self.department_id)
        #         desks = session.exec(statement).all()
        #         desk_ids = [desk.id for desk in desks]
        #         clients = super().get_list_query().where(Client.desk_id.in_(desk_ids))
        #         return clients
        if self.head:
            # test = super().get_list_query().where(Desk.department_id == self.department_id)
            return query
        if self.department_leader:
            query = query.where(Client.department_id != 0).where(Client.department_id == self.department_id)
            return query
        if self.desk_leader:
            query = query.where(Client.desk_id != 0).where(Client.department_id == self.department_id).where(Client.desk_id == self.desk_id)
            return query
        query = query.where(Client.department_id != 0).where(Client.desk_id != 0).where(Client.department_id == self.department_id).where(Client.desk_id == self.desk_id).where(Client.responsible_id == self.id)
        return query

    fields = [

        Client.status_id,
        Client.id,
        Client.first_name,
        Client.second_name,
        EmailCopyField("email"),
        CustomPhoneField("phone_number"),
        NotesField("notes"),
        StatusField("status"),
        ResponsibleField("responsible"),
        CountryField("country_code"),
        Client.creation_date,

        Client.description,
        Client.status,
        Client.type,
        Client.title,
        Client.patronymic,
        Client.city,
        Client.region,
        Client.address,
        Client.postcode,
        Client.additional_contact,
        Client.status_id,
        Client.desk,
        Client.department,
        Client.responsible,
        Client.actions,
        Client.affiliate,
        Client.trader,
        Client.notes,
        Client.responsible_id,
        Client.last_note,
    ]

    exclude_fields_from_list = [
        # Client.first_name,
    ]
    exclude_fields_from_edit = [
        Client.notes,
        Client.creation_date,
    ]
    exclude_fields_from_create = [
        Client.notes,
        Client.creation_date,
        Client.actions,
        Client.status,
        Client.responsible,
        Client.trader,
    ]

    @action(
        name="set_admin",
        text="Set",
        confirmation="Enter the department id",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        #         <input name="id" class="form-control" id="floating-input" value="">
        form=""" """,
        data_bs_target="#modal-admin",
    )
    async def set_admin(self, request: Request, pks: List[Any]) -> str:
        session: Session = request.state.session
        Clients = await self.find_by_pks(request, pks)

        updates = []
        for client in Clients:
            update_data = {'id': client.id}
            if request.query_params["department"] != "none":
                update_data['department_id'] = request.query_params["department"]
            if request.query_params["desk"] != "none":
                update_data['desk_id'] = request.query_params["desk"]
            if request.query_params["responsible"] != "none":
                update_data['responsible_id'] = request.query_params["responsible"]
            if request.query_params["status"] != "none":
                update_data['status_id'] = request.query_params["status"]
            updates.append(update_data)

        if updates:
            session.bulk_update_mappings(Client, updates)
            session.commit()

        return "{} clients were successfully changed".format(
            len(pks)
        )

    @action(
        name="set_department_leader",
        text="Set",
        confirmation="Enter the department id",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        #         <input name="id" class="form-control" id="floating-input" value="">
        form=""" """,
        data_bs_target="#modal-department",
    )
    async def set_department_leader(self, request: Request, pks: List[Any]) -> str:
        session: Session = request.state.session
        if request.query_params["desk"] != "none":
            for Client in await self.find_by_pks(request, pks):
                Client.desk_id = request.query_params["desk"]
                session.add(Client)
        if request.query_params["responsible"] != "none":
            for Client in await self.find_by_pks(request, pks):
                Client.responsible_id = request.query_params["responsible"]
                session.add(Client)
        if request.query_params["status"] != "none":
            for Client in await self.find_by_pks(request, pks):
                Client.status_id = request.query_params["status"]
                session.add(Client)
        session.commit()
        return "{} clients were successfully changed".format(
            len(pks)
        )

    @action(
        name="set_desk_leader",
        text="Set",
        confirmation="Enter the department id",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        #         <input name="id" class="form-control" id="floating-input" value="">
        form=""" """,
        data_bs_target="#modal-desk",
    )
    async def set_desk_leader(self, request: Request, pks: List[Any]) -> str:
        session: Session = request.state.session
        if request.query_params["responsible"] != "none":
            for Client in await self.find_by_pks(request, pks):
                Client.responsible_id = request.query_params["responsible"]
                session.add(Client)
        if request.query_params["status"] != "none":
            for Client in await self.find_by_pks(request, pks):
                Client.status_id = request.query_params["status"]
                session.add(Client)
        session.commit()
        return "{} clients were successfully changed".format(
            len(pks)
        )


    @action(
        name="set_department",
        text="Set department",
        confirmation="Enter the department id",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        #         <input name="id" class="form-control" id="floating-input" value="">
        form="""<div class="input-group input-group-sm mb-3">,
        <div class="input-group-prepend">
        <span class="input-group-text" id="inputGroup-sizing-sm">id:</span>
        </div>
        <input  name="id" type="text" class="form-control" aria-label="Small" aria-describedby="inputGroup-sizing-sm">
        </div>""",
    )
    async def set_department(self, request: Request, pks: List[Any]) -> str:
        session: Session = request.state.session
        for Client in await self.find_by_pks(request, pks):
            Client.department_id = request.query_params["id"]
            session.add(Client)
        session.commit()
        return "{} clients were successfully changed to department with id: {}".format(
            len(pks), request.query_params["id"]
        )

    @action(
        name="set_desk",
        text="Set desk",
        confirmation="Enter the desk id",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        #         <input name="id" class="form-control" id="floating-input" value="">
        form="""<div class="input-group input-group-sm mb-3">,
           <div class="input-group-prepend">
           <span class="input-group-text" id="inputGroup-sizing-sm">id:</span>
           </div>
           <input  name="id" type="text" class="form-control" aria-label="Small" aria-describedby="inputGroup-sizing-sm">
           </div>""",
    )
    async def set_desk(self, request: Request, pks: List[Any]) -> str:
        if self.department_leader:
            with Session(engine) as session:
                statement = select(Desk).where(Desk.id == request.query_params["id"])
                desk_result = session.exec(statement).first()
                if desk_result.department_id != request.state.user["department_id"]:
                    raise ActionFailed("ID not from your department")
        session: Session = request.state.session

        for Client in await self.find_by_pks(request, pks):
            Client.desk_id = request.query_params["id"]
            session.add(Client)
        session.commit()
        return "{} clients were successfully changed to desk with id: {}".format(
            len(pks), request.query_params["id"]
        )

    @action(
        name="change_responsible",
        text="Change responsible",
        confirmation="Enter the user id you want to assign as responsible",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        #         <input name="id" class="form-control" id="floating-input" value="">
        form="""<div class="input-group input-group-sm mb-3">,
        <div class="input-group-prepend">
        <span class="input-group-text" id="inputGroup-sizing-sm">id:</span>
        </div>
        <input  name="id" type="text" class="form-control" aria-label="Small" aria-describedby="inputGroup-sizing-sm">
        </div>""",
    )
    async def change_responsible(self, request: Request, pks: List[Any]) -> str:
        with Session(engine) as session:
            statement = select(Employee).where(Employee.id == request.query_params["id"])
            desk_result = session.exec(statement).first()
            if self.desk_leader:
                if desk_result.desk_id != request.state.user["desk_id"] or desk_result.department_id != request.state.user["department_id"]:
                    raise ActionFailed("ID not from your desk or department")
            if self.department_leader:
                if desk_result.department_id != request.state.user["department_id"]:
                    raise ActionFailed("ID not from your department")
        session: Session = request.state.session
        for Client in await self.find_by_pks(request, pks):
            Client.responsible_id = request.query_params["id"]
            session.add(Client)
        session.commit()
        return "{} clients were successfully changed to responsible with id: {}".format(
            len(pks), request.query_params["id"]
        )

    @action(
        name="clear_responsible",
        text="Clear responsible",
        # confirmation="Enter the user id you want to assign as responsible",
        # submit_btn_text="Yes, proceed",
        # submit_btn_class="btn-success",
        #         <input name="id" class="form-control" id="floating-input" value="">
        # form="""<div class="input-group input-group-sm mb-3">,
        # <div class="input-group-prepend">
        # <span class="input-group-text" id="inputGroup-sizing-sm">id:</span>
        # </div>
        # <input  name="id" type="text" class="form-control" aria-label="Small" aria-describedby="inputGroup-sizing-sm">
        # </div>""",
    )
    async def clear_responsible(self, request: Request, pks: List[Any]) -> str:
        with Session(engine) as session:
            statement = select(Employee).where(Employee.id == request.query_params["id"])
            desk_result = session.exec(statement).first()
            if self.desk_leader:
                if desk_result.desk_id != request.state.user["desk_id"] or desk_result.department_id != request.state.user["department_id"]:
                    raise ActionFailed("ID not from your desk or department")
            if self.department_leader:
                if desk_result.department_id != request.state.user["department_id"]:
                    raise ActionFailed("ID not from your department")
        session: Session = request.state.session
        for Client in await self.find_by_pks(request, pks):
            Client.responsible_id = None
            session.add(Client)
        session.commit()
        return "Responsible was successfully cleared to {} clients".format(
            len(pks)
        )

    @action(
        name="add_note",
        text="Add note",
        confirmation="Enter note",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        #         <input name="id" class="form-control" id="floating-input" value="">
        form="""<div class="input-group input-group-sm mb-3">,
        <div class="input-group-prepend">
            <span class="input-group-text">Note:</span>
        </div>
        <textarea name="note" class="form-control" aria-label="With textarea"></textarea>
        </div>""",
    )
    async def add_note(self, request: Request, pks: List[Any]) -> str:
        session: Session = request.state.session
        if request.query_params["note"] == "":
            return "Note is too short"
        for Client in await self.find_by_pks(request, pks):
            new_note = Note(content=request.query_params["note"], client_id=Client.id,
                            employee_id=request.state.user["id"], employee_name=request.state.user["name"])
            session.add(new_note)
            Client.last_note = datetime.utcnow()
            session.add(Client)
        session.commit()
        return "{} Note was successfully added".format(
            len(pks)
        )

    @action(
        name="change_status",
        id="changestatus",
        text="Change status",
        confirmation="Enter status id",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        #         <input name="id" class="form-control" id="floating-input" value="">
        form="""<div class="input-group input-group-sm mb-3">,
        <div class="input-group-prepend">
        <span class="input-group-text" id="inputGroup-sizing-sm">id:</span>
        </div>
        <input  name="id" type="text" class="form-control" aria-label="Small" aria-describedby="inputGroup-sizing-sm">
        </div>""",
        data_bs_target="#modal-action-status"
    )
    async def change_status(self, request: Request, pks: List[Any]) -> str:
        session: Session = request.state.session
        for Client in await self.find_by_pks(request, pks):
            Client.status_id = request.query_params["id"]
            session.add(Client)
        session.commit()
        return "{} clients were successfully changed status to id: {}".format(
            len(pks), request.query_params["id"]
        )


    async def is_action_allowed(self, request: Request, name: str) -> bool:
        if name == "set_admin":
            if request.state.user["sys_admin"]:
                return True
            if request.state.user["head"]:
                return True
            return False
        if name == "set_department_leader":
            if request.state.user["department_leader"]:
                return True
            return False
        if name == "set_desk_leader":
            if request.state.user["desk_leader"]:
                return True
            return False
        if name == "set_department":
            if request.state.user["sys_admin"]:
                return True
            if request.state.user["head"]:
                return True
            return False
        if name == "set_desk":
            if request.state.user["sys_admin"]:
                return True
            if request.state.user["head"]:
                return True
            if request.state.user["department_leader"]:
                return True
            return False
        if name == "change_responsible":
            if request.state.user["sys_admin"]:
                return True
            if request.state.user["head"]:
                return True
            if request.state.user["department_leader"]:
                return True
            if request.state.user["desk_leader"]:
                return True
            return False
        if name == "clear_responsible":
            if request.state.user["sys_admin"]:
                return True
            if request.state.user["head"]:
                return True
            if request.state.user["department_leader"]:
                return True
            if request.state.user["desk_leader"]:
                return True
            return False
        if name == "delete":
            return self.can_delete(request)
        return True

    # @action(
    #     name="add_note",
    #     text="Add note",
    #     confirmation="Enter note",
    #     submit_btn_text="Yes, proceed",
    #     submit_btn_class="btn-success",
    #     form="""<div class="input-group input-group-sm mb-3">,
    #     <div class="input-group-prepend">
    #         <span class="input-group-text">Note:</span>
    #     </div>
    #     <textarea name="note" class="form-control" aria-label="With textarea"></textarea>
    #     </div>""",
    # )
    # async def add_note_action(self, request: Request, pks: List[Any]) -> str:
    #     session: Session = request.state.session
    #     for Client in await self.find_by_pks(request, pks):
    #         new_note = Note(content=request.query_params["note"], client_id=Client.id,
    #                         employee_id=request.state.user["id"], employee_name=request.state.user["name"])
    #         session.add(new_note)
    #     session.commit()
    #     return "{} Note was successfully added".format(
    #         len(pks)
    #     )

    # @action(
    #     name="add_note",
    #     text="Add note",
    #     confirmation="Enter note",
    #     submit_btn_text="Yes, proceed",
    #     submit_btn_class="btn-success",
    #     form="""
    #     <form>
    #         <div class="mt-3">
    #             <input type="text" class="form-control" name="value1" placeholder="Enter value" min="1" max="1000">
    #         </div>
    #     </form>
    #             <form>
    #         <div class="mt-3">
    #             <input type="text" class="form-control" name="value2" placeholder="Enter value" min="1" max="1000">
    #         </div>
    #     </form>
    #     """,
    # )
    # async def add_note_action(self, request: Request, pks: List[Any]) -> str:
    #     session: Session = request.state.session
    #     data = await request.form()
    #     # for Client in await self.find_by_pks(request, pks):
    #     #     new_note = Note(content=request.query_params["note"], client_id=Client.id,
    #     #                     employee_id=request.state.user["id"], employee_name=request.state.user["name"])
    #     #     session.add(new_note)
    #     # session.commit()
    #     value1 = data.get("value1")
    #     value2 = data.get("value2")
    #     return f'{value1}, {value2}'


class StatusesView(MyModelView):
    fields = [
        Status.id,
        Status.name,
        BooleanField("hide", label="Hide from clients"),
        # Status.hide,
    ]

    responsive_table = True
    column_visibility = True
    search_builder = True

    def can_delete(self, request: Request) -> bool:
        if request.state.user["sys_admin"]:
            return True
        if request.state.user["head"]:
            return True


class RetainStatusesView(MyModelView):
    responsive_table = True
    column_visibility = True
    search_builder = True

    def is_accessible(self, request: Request) -> bool:
        referer_url = urlparse(request.headers.get("referer"))
        query_dict = parse_qs(referer_url.query)
        self.query = query_dict
        self.id = request.state.user["id"]
        self.desk_id = request.state.user["desk_id"]
        self.department_id = request.state.user["department_id"]
        self.desk_leader = request.state.user["desk_leader"]
        self.department_leader = request.state.user["department_leader"]
        self.head = request.state.user["head"]
        self.sys_admin = request.state.user["sys_admin"]
        self.retain = request.state.user["retain"]

        # with Session(engine) as session:
        #     statement = select(Desk).where(Desk.department_id == request.state.user["department_id"])
        #     desks = session.exec(statement).all()
        #     # self.department_desks = desks
        #     self.department_desks = [desk.id for desk in desks]
        # self.role_name = request.state.user["id"]

        if request.state.user["sys_admin"] is True:
            return True
        if request.state.user["retain"] is True:
            return True
        return False

    def can_delete(self, request: Request) -> bool:
        if request.state.user["sys_admin"]:
            return True
        if request.state.user["retain"]:
            return True


class TypesView(MyModelView):
    responsive_table = True
    column_visibility = True
    search_builder = True

    def can_delete(self, request: Request) -> bool:
        if request.state.user["sys_admin"]:
            return True
        if request.state.user["head"]:
            return True
