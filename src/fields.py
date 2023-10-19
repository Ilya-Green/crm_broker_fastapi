from dataclasses import dataclass
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
from typing import Optional


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


@dataclass
class CopyField(StringField):
    display_template: str = "displays/copy.html"


@dataclass
class NotesField(StringField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    render_function_key: str = "notes"
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"
    display_template: str = "displays/note.html"
    exclude_from_create = True
    exclude_from_edit = True
    exclude_from_list = True


@dataclass
class EmailCopyField(EmailField):
    """This field is used to represent a text content
    that stores a single email address."""

    # input_type: str = "email"
    # render_function_key: str = "email"
    # class_: str = "field-email form-control"
    display_template: str = "displays/emailcopy.html"


@dataclass
class StatusField(StringField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    render_function_key: str = "status"
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"
    display_template: str = "displays/status.html"
    exclude_from_create = True
    exclude_from_edit = True
    exclude_from_list = True


@dataclass
class ResponsibleField(StringField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    render_function_key: str = "responsible"
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"
    display_template: str = "displays/responsible.html"
    exclude_from_create = True
    exclude_from_edit = True
    exclude_from_list = True


@dataclass
class TraderField(StringField):
    """This field is used to represent any kind of long text content.
    For short text contents, use [StringField][starlette_admin.fields.StringField]"""

    rows: int = 6
    render_function_key: str = "trader"
    class_: str = "field-textarea form-control"
    form_template: str = "forms/textarea.html"
    display_template: str = "displays/note.html"
    exclude_from_create = True
    exclude_from_edit = True
    exclude_from_list = True



