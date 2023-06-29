from sqlmodel import Session, select, asc, desc
from typing import Any, Dict, List, Optional, Set, Union
import logging

from .models import Employee, Role, Client, Status, Affiliate, Type
from . import engine

from .schemas import ClientCreate, ClientList


logger_api = logging.getLogger("api")

def api_get_statuses():
    with Session(engine) as session:
        statement = select(Status)
        statuses = session.exec(statement).all()
    return statuses

def api_get_types():
    with Session(engine) as session:
        statement = select(Type)
        types = session.exec(statement).all()
    return types


def api_client_create(data: ClientCreate):
    with Session(engine) as session:
        statement = select(Affiliate).where(Affiliate.auth_key == data.auth_key)
        auth = session.exec(statement).first()
    if auth:
        with Session(engine) as session:
            new_client = Client(**data.dict(), affiliate_id=auth.id)
            session.add(new_client)
            session.commit()
            session.refresh(new_client)
        logger_api.warning(f"created {new_client}")
        return 'success', new_client
    else:
        logger_api.warning(f"incorrect auth_key {auth}")
        return 'incorrect auth_key'


def api_client_list(data: ClientList) -> Union[List[Dict[str, str]], int]:
    with Session(engine) as session:
        statement = select(Affiliate).where(Affiliate.auth_key == data.auth_key)
        auth = session.exec(statement).first()
    if auth:
        with Session(engine) as session:
            sorting_order = desc if data.sorting_order == 'desc' else asc
            statement = select(Client).where(Client.affiliate_id == auth.id).where(Client.id.notin_(data.ignoreClientIds)).order_by(sorting_order(data.sorting_field)).offset(data.offset).limit(data.limit)
            if data.count == 0:
                result = session.exec(statement).all()
                return result
            else:
                result = session.exec(statement).all()
                count = len(result)
                return count
        return result
    else:
        return 'incorrect auth_key'
