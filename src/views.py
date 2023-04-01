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
)
from starlette_admin.fields import FileField, RelationField
from .fields import PasswordField, CopyField, NotesField
from starlette_admin.contrib.sqlmodel import ModelView
from starlette.requests import Request
from sqlalchemy.orm import Session
from sqlmodel import Session, select
from starlette.requests import Request
from sqlalchemy import or_, and_
from typing import Optional, Dict
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

from starlette_admin.helpers import html_params
from .models import Employee, Role, Client, Desk, Affiliate, Department, Note
from . import engine


class MyModelView(ModelView):
    include_relationships: bool = True
    page_size = 20
    page_size_options = [5, 10, 25, 50, 100]
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
            return super().get_list_query().where(Employee.role_id != 1)
        if self.department_leader:
            return super().get_list_query().where(Employee.role_id != 1).where(Employee.department_id != 0).where(Employee.department_id == self.department_id)
        if self.desk_leader:
            return super().get_list_query().where(Employee.role_id != 1).where(Employee.desk_id != 0).where(Employee.department_id == self.department_id).where(Employee.desk_id == self.desk_id)

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
            return super().get_list_query().where(Client.department_id != 0).where(Client.department_id == self.department_id)
        if self.desk_leader:
            return super().get_list_query().where(Client.desk_id != 0).where(Client.department_id == self.department_id).where(Client.desk_id == self.desk_id)
        return super().get_list_query().where(Client.department_id != 0).where(Client.desk_id != 0).where(Client.department_id == self.department_id).where(Client.desk_id == self.desk_id).where(Client.responsible_id == self.id)

    def get_count_query(self) -> Select:
        if self.sys_admin:
            return super().get_count_query()
        if self.head:
            return super().get_count_query()
        if self.department_leader:
            return super().get_count_query().where(Client.department_id == self.department_leader)
        if self.desk_leader:
            return super().get_count_query().where(Client.desk_id == self.desk_id)
        return super().get_count_query().where(Client.responsible_id == self.id).where(Client.desk_id == self.desk_id)
        # return select(func.count(self._pk_column))

    fields = [
        Client.id,
        Client.first_name,
        Client.email,
        CopyField("phone_number"),
        NotesField("notes"),
        Client.notes,
        Client.status,
    ]

    exclude_fields_from_list = [Employee.notes]
    exclude_fields_from_edit = [Employee.notes]

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
        confirmation="Enter note",
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

