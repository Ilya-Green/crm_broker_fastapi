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
    PasswordField,
)
from .fields import PasswordField
from starlette_admin.contrib.sqlmodel import ModelView
from starlette.requests import Request
from sqlalchemy.orm import Session
from sqlmodel import Session, select
from starlette.requests import Request
from sqlalchemy import or_, and_
from typing import Optional
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

from starlette_admin.helpers import html_params
from .models import Employee, Role, Client, Desk, Affiliate
from . import engine


class MyModelView(ModelView):
    include_relationships: bool = True
    page_size = 20
    page_size_options = [5, 10, 25, 50, 100]
    export_types = [ExportType.EXCEL, ExportType.CSV, ExportType.PDF, ExportType.PRINT]


class EmployeeView(MyModelView):
    list_template = "employee_list_template.html"

    responsive_table = True
    column_visibility = True
    search_builder = True

    def is_accessible(self, request: Request) -> bool:
        if "accounts_can_access" in request.state.user:
            if request.state.user["sys_admin"] is True:
                return True
        return False

    fields = [
        Employee.id,
        Employee.login,
        PasswordField("password"),
        Employee.role,
        Employee.desk,
        Employee.clients_responsible,
        Employee.department_head,
        Employee.notes,
        Employee.actions,
    ]

    exclude_fields_from_create = [Employee.actions]


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
        if request.state.user["sys_admin"] is True:
            return True
        if request.state.user["head"] is True:
            return True
        return False

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
        return False

    def get_list_query(self):
        if self.sys_admin:
            return super().get_list_query()
        if self.head:
            return super().get_list_query()
        if self.department_leader:
            return super().get_list_query().where(Desk.department_id == self.department_id)

    def get_count_query(self):
        if self.sys_admin:
            return super().get_count_query()
        if self.head:
            return super().get_count_query()
        if self.department_leader:
            return super().get_count_query().where(Desk.department_id == self.department_id)

class AffiliatesView(MyModelView):
    exclude_fields_from_create = [Affiliate.auth_key]

    def is_accessible(self, request: Request) -> bool:
        if request.state.user["sys_admin"] is True:
            return True
        return False


class ClientsView(MyModelView):
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

        with Session(engine) as session:
            statement = select(Desk).where(Desk.department_id == request.state.user["department_id"])
            desks = session.exec(statement).all()
            # self.department_desks = desks
            self.department_desks = [desk.id for desk in desks]
        # self.role_name = request.state.user["id"]

        if "clients_can_access" in request.state.user:
            if request.state.user["clients_can_access"] is True:
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

    def can_change_responsible(self, request: Request) -> bool:
        if request.state.user["sys_admin"] is True:
            return True
        if request.state.user["head"] is True:
            return True
        if request.state.user["desk_leader"] is True:
            return True
        if request.state.user["head"] is True:
            return True
        return False

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
            return super().get_list_query()
        # if self.head:
        #     with Session(engine) as session:
        #         statement = select(Desk).where(Desk.department_id == self.department_id)
        #         desks = session.exec(statement).all()
        #         desk_ids = [desk.id for desk in desks]
        #         clients = super().get_list_query().where(Client.desk_id.in_(desk_ids))
        #         return clients
        if self.head:
            # test = super().get_list_query().where(Desk.department_id == self.department_id)
            return super().get_list_query()
        if self.department_leader:
            return super().get_list_query().where(Client.desk_id.in_(self.department_desks))
        if self.desk_leader:
            return super().get_list_query().where((Client.desk_id == self.desk_id))
        return super().get_list_query().where(Client.responsible_id == self.id).where(Client.desk_id == self.desk_id)

    def get_count_query(self) -> Select:
        if self.sys_admin:
            return super().get_count_query()
        if self.head:
            return super().get_count_query()
        if self.department_leader:
            return super().get_count_query().where(Client.desk_id.in_(self.department_desks))
        if self.desk_leader:
            return super().get_count_query().where(Client.desk_id == self.desk_id)
        return super().get_count_query().where(Client.responsible_id == self.id).where(Client.desk_id == self.desk_id)
        # return select(func.count(self._pk_column))

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
    async def make_published_action(self, request: Request, pks: List[Any]) -> str:
        session: Session = request.state.session
        for Client in await self.find_by_pks(request, pks):
            Client.responsible_id = request.query_params["id"]
            session.add(Client)
        session.commit()
        return "{} clients were successfully changed to responsible with id: {}".format(
            len(pks), request.query_params["id"]
        )

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        if name == "change_responsible":
            return self.can_delete(request)
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
