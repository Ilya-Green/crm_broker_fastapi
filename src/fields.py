import ast
import json
from dataclasses import dataclass

from starlette.datastructures import FormData
from starlette.requests import Request
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
    RelationField,
)
from typing import Optional, Any

from starlette_admin.fields import CustomRelationField, FloatField


@dataclass
class PasswordField(StringField):
    """A StringField, except renders an `<input type="password">`."""

    input_type: str = "password"
    class_: str = "field-password form-control"
    # exclude_from_list: Optional[bool] = True
    # exclude_from_detail: Optional[bool] = True
    # exclude_from_create: Optional[bool] = False
    # exclude_from_edit: Optional[bool] = False

    exclude_from_list: Optional[bool] = True
    exclude_from_detail: Optional[bool] = True
    exclude_from_create: Optional[bool] = False
    exclude_from_edit: Optional[bool] = False
    searchable: Optional[bool] = False
    orderable: Optional[bool] = False
    render_function_key: str = "file"

    async def serialize_value(
            self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        if request.state.user["sys_admin"] is False:
            return "********"
        # return "********"
        return value


@dataclass
class CopyField(StringField):
    display_template: str = "displays/copy.html"


@dataclass
class CustomPhoneField(StringField):
    display_template: str = "displays/phone.html"

    input_type: str = "phone"
    class_: str = "field-phone form-control"

    render_function_key: str = "phone"



@dataclass
class FloatRoundedField(FloatField):
    async def serialize_value(
        self, request: Request, value: Any, action: RequestAction
    ) -> float:
        return round(float(value), 2)


@dataclass
class NotesField(CustomRelationField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    render_function_key: str = "notes"
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"
    display_template: str = "displays/note.html"
    exclude_from_create: Optional[bool] = True
    exclude_from_edit: Optional[bool] = True
    exclude_from_list: Optional[bool] = False

    # надо бы прописать эти функции что бы:
    # 1. не доставать данные для листа
    # 2. в сериализованном виде отадавать их для details что бы было удобно по им итерироваться для отображения в html
    # async def parse_form_data(
    # async def parse_obj(self, request: Request, obj: Any) -> Any:


@dataclass
class LeadField(CustomRelationField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    render_function_key: str = "lead"
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"
    display_template: str = "displays/lead.html"
    exclude_from_create: Optional[bool] = True
    exclude_from_edit: Optional[bool] = True
    exclude_from_list: Optional[bool] = False
    exclude_from_detail: Optional[bool] = False


@dataclass
class OrderField(CustomRelationField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    render_function_key: str = "order"
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"
    display_template: str = "displays/order.html"
    exclude_from_create: Optional[bool] = True
    exclude_from_edit: Optional[bool] = True
    exclude_from_list: Optional[bool] = False
    exclude_from_detail: Optional[bool] = False


@dataclass
class TransactionField(CustomRelationField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    render_function_key: str = "transaction"
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"
    display_template: str = "displays/transaction.html"
    exclude_from_create: Optional[bool] = True
    exclude_from_edit: Optional[bool] = True
    exclude_from_list: Optional[bool] = False
    exclude_from_detail: Optional[bool] = False


@dataclass
class LeadWithCommentsField(StringField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    render_function_key: str = "lead"
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"
    display_template: str = "displays/lead_with_comments.html"
    exclude_from_create: Optional[bool] = True
    exclude_from_edit: Optional[bool] = True
    exclude_from_list: Optional[bool] = False


@dataclass
class RoleField(CustomRelationField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    render_function_key: str = "status"
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"
    display_template: str = "displays/role.html"
    exclude_from_create: Optional[bool] = True
    exclude_from_edit: Optional[bool] = True
    exclude_from_list: Optional[bool] = False
    exclude_from_detail: Optional[bool] = False


@dataclass
class LeadCompactField(CustomRelationField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    render_function_key: str = "lead"
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"
    display_template: str = "displays/lead_compact.html"
    exclude_from_create: Optional[bool] = True
    exclude_from_edit: Optional[bool] = True
    exclude_from_list: Optional[bool] = False
    exclude_from_detail: Optional[bool] = False

    async def serialize_value(
            self, request: Request, value: Any, action: RequestAction
    ) -> Any:
        return str('123')


@dataclass
class DeskField(CustomRelationField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    render_function_key: str = "desk"
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"
    display_template: str = "displays/role.html"
    exclude_from_create: Optional[bool] = True
    exclude_from_edit: Optional[bool] = True
    exclude_from_list: Optional[bool] = False
    exclude_from_detail: Optional[bool] = False


@dataclass
class DepartmentField(StringField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    render_function_key: str = "status"
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"
    display_template: str = "displays/lead.html"
    exclude_from_create: Optional[bool] = True
    exclude_from_edit: Optional[bool] = True
    exclude_from_list: Optional[bool] = False


@dataclass
class AffiliateField(CustomRelationField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    render_function_key: str = "status"
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"
    display_template: str = "displays/role.html"
    exclude_from_create: Optional[bool] = True
    exclude_from_edit: Optional[bool] = True
    exclude_from_list: Optional[bool] = False
    exclude_from_detail: Optional[bool] = False

    async def parse_form_data(
        self, request: Request, form_data: FormData, action: RequestAction
    ) -> Any:
        """
        Extracts the value of this field from submitted form data.
        """
        if action == RequestAction.LIST:
            return '123'
        return form_data.get(self.id)


@dataclass
class EmailCopyField(EmailField):
    """This field is used to represent a text content
    that stores a single email address."""

    # input_type: str = "email"
    # render_function_key: str = "email"
    # class_: str = "field-email form-control"
    display_template: str = "displays/emailcopy.html"


@dataclass
class TraderStatusField(CustomRelationField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    render_function_key: str = "status"
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"
    display_template: str = "displays/status.html"
    exclude_from_create: Optional[bool] = True
    exclude_from_edit: Optional[bool] = True
    exclude_from_list: Optional[bool] = False
    exclude_from_detail: Optional[bool] = False


@dataclass
class StatusField(CustomRelationField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    render_function_key: str = "status"
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"
    display_template: str = "displays/status.html"
    exclude_from_create: Optional[bool] = True
    exclude_from_edit: Optional[bool] = True
    exclude_from_list: Optional[bool] = False


@dataclass
class ResponsibleField(CustomRelationField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    render_function_key: str = "responsible"
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"
    display_template: str = "displays/responsible.html"
    exclude_from_create: Optional[bool] = True
    exclude_from_edit: Optional[bool] = True
    exclude_from_list: Optional[bool] = False


@dataclass
class EmployeesField(CustomRelationField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    render_function_key: str = "responsible"
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"
    display_template: str = "displays/responsible.html"
    exclude_from_create: Optional[bool] = True
    exclude_from_edit: Optional[bool] = True
    exclude_from_list: Optional[bool] = False
    exclude_from_detail: Optional[bool] = False


@dataclass
class TraderField(CustomRelationField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    render_function_key: str = "trader"
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"
    display_template: str = "displays/trader.html"
    exclude_from_create: Optional[bool] = True
    exclude_from_edit: Optional[bool] = True
    exclude_from_list: Optional[bool] = False
    exclude_from_detail: Optional[bool] = False



