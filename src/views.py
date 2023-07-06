import json
from datetime import datetime

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
from starlette_admin.fields import FileField, RelationField
from .fields import PasswordField, CopyField, NotesField, EmailCopyField, StatusField
from starlette_admin.contrib.sqlmodel import ModelView
from starlette.requests import Request
from sqlalchemy.orm import Session
from sqlmodel import Session, select
from starlette.requests import Request
from sqlalchemy import or_, and_
from typing import Optional, Dict, Union
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

from starlette_admin.helpers import html_params
from .models import Employee, Role, Client, Desk, Affiliate, Department, Note, Trader, Order, Transaction
from . import engine


logger = logging.getLogger("api")


class MyModelView(ModelView):
    include_relationships: bool = True
    page_size = 20
    page_size_options = [5, 10, 25, 50, 100, 500, 1000]
    export_types = [ExportType.EXCEL, ExportType.CSV, ExportType.PDF, ExportType.PRINT]


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
        Employee.clients_responsible,
        Employee.department,
        Employee.notes,
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


def update_platform_data():
    params = {'token': 'value1'}
    response = requests.get(url='https://general-investment.com/api/admin/user/all', params=params)
    data = json.loads(response.content)
    for user_data in data:
        with Session(engine) as session:
            statement = select(Trader).where(Trader.id == user_data["id"])
            current_trader = session.exec(statement).first()
        autologin = user_data.get("autologin")
        new_trader = Trader(
            # id=user_data["id"],
            # name=user_data["name"],
            # email=user_data["email"],
            # phone_number=user_data["phone"],
            # balance=user_data["mainBalance"],
            # created_at_tp=datetime.fromtimestamp(user_data["createdAt"]/1000),
            id=user_data["id"],
            name=user_data["name"],
            surname=user_data["surname"],
            email=user_data["email"],
            phone_number=user_data["phone"],
            date=datetime.fromtimestamp(user_data["date"]/1000),
            password=user_data["password"],
            country=user_data["country"],
            accountNumber=user_data["accountNumber"],
            created_at_tp=user_data["createdAt"],
            # created_at_tp=datetime.fromtimestamp(user_data["createdAt"]/1000),
            balance=user_data["balance"],
            mainBalance=user_data["mainBalance"],
            bonuses=user_data["bonuses"],
            credFacilities=user_data["credFacilities"],
            accountStatus=user_data["accountStatus"],
            blocked=user_data["blocked"],
            isActive=user_data["isActive"],
            isVipStatus=user_data["isVipStatus"],
            autologin=user_data.get("autologin"),
            autologin_link="https://general-investment.com/autoologin?token=" + autologin if autologin else ""
        )
        if current_trader is not None:
            new_trader.responsible_id = current_trader.responsible_id
            new_trader.status_id = current_trader.status_id
            if user_data["balance"] > 0:
                with Session(engine) as session:
                    statement = select(Client).where(Client.trader_id == new_trader.id)
                    current_client = session.exec(statement).first()
                if current_client:
                    current_client.type_id = 3
                    session.merge(current_client)
                    session.commit()
            # if (user_data["balance"] == 0) and ((user_data["credFacilities"] > 0) or (user_data["bonuses"] > 0)):
            #     new_trader.type_id = 2

        with Session(engine) as session:
            session.merge(new_trader)
            session.commit()

    params = {'token': 'value1'}
    response = requests.get(url='https://general-investment.com/api/admin/order/all', params=params)
    data = json.loads(response.content)
    for user_data in data:
        new_order = Order(
            wid=user_data["_id"],
            id=user_data["id"],
            asset_name=user_data["assetName"],
            amount=user_data["amount"],
            opening_price=user_data["openingPrice"],
            pledge=user_data["pledge"],
            user_id=user_data["userId"],
            type=user_data["type"],
            is_closed=user_data["isClosed"],
            created_at=user_data["createdAt"],
            take_profit=user_data["takeProfit"],
            stop_loss=user_data["stopLoss"],
            auto_close=user_data["autoClose"],
            v=user_data["__v"],
            closed_at=user_data.get("closedAt"),
            closed_price=user_data.get("closedPrice")
        )
        with Session(engine) as session:
            session.merge(new_order)
            session.commit()

    params = {'token': 'value1'}
    response = requests.get(url='https://general-investment.com/api/admin/transaction/all', params=params)
    data = json.loads(response.content)
    for transaction_data in data:
        new_transaction = Transaction(
            id=transaction_data["id"],
            content=transaction_data.get("content"),
            createdAt=transaction_data["createdAt"],
            dirName=transaction_data.get("dirName"),
            type=transaction_data["type"],
            value=transaction_data["value"],
            v=transaction_data.get("__v"),
            trader_id=transaction_data["userId"],
        )
        with Session(engine) as session:
            session.merge(new_transaction)
            session.commit()


def edit_order_platform(obj: Any,):
    url = "https://general-investment.com/api/admin/order/edit"
    query_params = {
        "token": "value1",
    }
    body = {
        "_id": obj.wid,
        "assetName": obj.asset_name,
        "amount": obj.amount,
        "openingPrice": obj.opening_price,
        "pledge": obj.pledge,
        "userId": obj.user_id,
        "type": obj.type,
        "id": obj.id,
        "isClosed": obj.is_closed,
        "createdAt": int(obj.created_at.timestamp() * 1000),
        "takeProfit": obj.take_profit,
        "stopLoss": obj.stop_loss,
        "autoClose": obj.auto_close,
        "__v": obj.v,
        "closedAt": int(obj.closed_at.timestamp() * 1000) if obj.closed_at else None,
        "closedPrice": obj.closed_price
    }
    response = requests.put(url, params=query_params, json=body)
    if response.status_code == 200:
        print("Запрос успешно выполнен")
        logger.info(f'Обновлены данные ордера: {obj}')
    else:
        print(response.status_code)
        logger.info(f'Неудачная попытка обновить данные ордера: {obj}')
        print("Ошибка при выполнении запроса")


def edit_account_platform(obj: Any,):
    url = "https://general-investment.com/api/admin/user/edit"
    query_params = {
        "token": "value1",
    }
    body = {
        "name": obj.name,
        "surname": obj.surname,
        "accountNumber": obj.accountNumber,
        "email": obj.email,
        "phone": obj.phone_number,
        "country": obj.country,
        # "city": obj.city,
        # "address": obj.address,
        # "dirName": obj.dirName,
        "blocked": obj.blocked,
        "accountStatus": obj.accountStatus,
        # "password": obj.password,
        "isActive": obj.isActive,
        "isVipStatus": obj.isVipStatus,
        # "docs": {
        #     "others": []
        # },
        "id": obj.id
    }
    response = requests.put(url, params=query_params, json=body)
    if response.status_code == 200:
        print("Запрос успешно выполнен")
        print(response.content)
        logger.info(f'Обновлены данные ордера: {obj}')
    else:
        print(response.status_code)
        print(response.content)
        logger.info(f'Неудачная попытка обновить данные ордера: {obj}')
        print("Ошибка при выполнении запроса")


def change_account_password_platform(trader: Trader, password: str):
    url = "https://general-investment.com/api/admin/user/edit"
    query_params = {
        "token": "value1",
    }
    body = {
        "name": trader.name,
        "surname": trader.surname,
        "accountNumber": trader.accountNumber,
        "email": trader.email,
        "phone": trader.phone_number,
        "country": trader.country,
        # "city": obj.city,
        # "address": obj.address,
        # "dirName": obj.dirName,
        "blocked": trader.blocked,
        "accountStatus": trader.accountStatus,
        "password": password,
        "isActive": trader.isActive,
        "isVipStatus": trader.isVipStatus,
        # "docs": {
        #     "others": []
        # },
        "id": trader.id
    }
    response = requests.put(url, params=query_params, json=body)
    if response.status_code == 200:
        print("Запрос успешно выполнен")
        print(response.content)
        logger.info(f'Обновлены данные ордера: {trader}')
    else:
        print(response.status_code)
        print(response.content)
        logger.info(f'Неудачная попытка обновить данные ордера: {trader}')
        print("Ошибка при выполнении запроса")


class TradersView(MyModelView):
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
        update_platform_data()
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
        # update_platform_data()
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
        update_platform_data()
        return True

    # def get_list_query(self):
    #     # update_platform_data()
    #     return super().get_list_query()
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


class OrdersView(MyModelView):
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
        update_platform_data()
        if request.state.user["sys_admin"] is True:
            return True
        if request.state.user["retain"] is True:
            return True

    def can_delete(self, request: Request) -> bool:
        if request.state.user["sys_admin"] is True:
            return True

    def can_view_details(self, request: Request) -> bool:
        update_platform_data()
        return True

    fields = [
        Order.trader,
        Order.asset_name,
        Order.amount,
        Order.opening_price,
        Order.closed_price,
        Order.type,
        Order.pledge,
        Order.take_profit,
        Order.stop_loss,
        Order.created_at,
        Order.closed_at,
        Order.is_closed,
        Order.auto_close,
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
        update_platform_data()
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

    # list_template = "client_list_template.html"
    detail_template: str = "clients_detail.html"

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
        if self.sys_admin:
        #     if self.query:
        #         query = super().get_list_query()
        #         for key, value in self.query.items():
        #             # query = query.where(Client.key == 'HOT')
        #             query = query.where(getattr(Client, key).in_(value))
        #         return query
        #     else:
        #         return super().get_list_query()
            query = super().get_list_query().where()
            if "responsible_id" in self.query:
                query = query.where(Client.responsible_id == self.query["responsible_id"][0])
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

            query = super().get_list_query()
            if "responsible_id" in self.query:
                query = query.where(Client.responsible_id == self.query["responsible_id"][0])
            return query
        if self.department_leader:
            query = super().get_list_query().where(Client.department_id != 0).where(Client.department_id == self.department_id)
            if "responsible_id" in self.query:
                query = query.where(Client.responsible_id == self.query["responsible_id"][0])
            return query
        if self.desk_leader:
            query = super().get_list_query().where(Client.desk_id != 0).where(Client.department_id == self.department_id).where(Client.desk_id == self.desk_id)
            if "responsible_id" in self.query:
                query = query.where(Client.responsible_id == self.query["responsible_id"][0])
            return query
        query = super().get_list_query().where(Client.department_id != 0).where(Client.desk_id != 0).where(Client.department_id == self.department_id).where(Client.desk_id == self.desk_id).where(Client.responsible_id == self.id)
        if "responsible_id" in self.query:
            query = query.where(Client.responsible_id == self.query["responsible_id"][0])
        return query

    def get_count_query(self) -> Select:
        if self.sys_admin:
            return super().get_count_query()
        if self.head:
            return super().get_count_query()
        if self.department_leader:
            return super().get_count_query().where(Client.department_id == self.department_leader)
        if self.desk_leader:
            return super().get_count_query().where(Client.desk_id == self.desk_id)
        return super().get_count_query().where(Client.department_id != 0).where(Client.desk_id != 0).where(Client.department_id == self.department_id).where(Client.responsible_id == self.id).where(Client.desk_id == self.desk_id)
        # return select(func.count(self._pk_column))

    fields = [

        Client.id,
        Client.first_name,
        EmailCopyField("email"),
        CopyField("phone_number"),
        NotesField("notes"),
        StatusField("status"),
        CountryField("country_code"),
        Client.creation_date,

        Client.status,
        Client.type,
        Client.title,
        Client.second_name,
        Client.patronymic,
        Client.city,
        Client.region,
        Client.address,
        Client.postcode,
        Client.description,
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
    ]

    # exclude_fields_from_list = [
    #     Client.notes,
    # ]
    exclude_fields_from_edit = [
        Client.notes,
        Client.creation_date,
    ]
    exclude_fields_from_create = [
        Client.notes,
        Client.creation_date,
        Client.actions,
    ]

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
        session.commit()
        return "{} Note was successfully added".format(
            len(pks)
        )

    @action(
        name="change_status",
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
