from sqlmodel import Session, select, asc, desc
from typing import Any, Dict, List, Optional, Set, Union

from .models import Employee, Role, Client, Status
from . import engine

from .schemas import ClientCreate


def api_get_statuses():
    with Session(engine) as session:
        statement = select(Status)
        statuses = session.exec(statement).all()
        return statuses


def api_client_create(data: ClientCreate):
    with Session(engine) as session:

        new_client = Client(**data.dict())
        session.add(new_client)
        session.commit()
        session.refresh(new_client)
        return 'success', new_client
