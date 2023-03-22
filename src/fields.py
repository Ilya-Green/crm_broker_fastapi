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
)
from typing import Optional


@dataclass
class PasswordField(StringField):
    """A StringField, except renders an `<input type="password">`."""

    input_type: str = "password"
    class_: str = "field-password form-control"
    exclude_from_list: Optional[bool] = True
    exclude_from_detail: Optional[bool] = True
    exclude_from_create: Optional[bool] = False
    exclude_from_edit: Optional[bool] = True
