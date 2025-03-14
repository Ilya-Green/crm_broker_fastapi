import json
from datetime import datetime, timedelta

from fastapi import HTTPException
import requests
from sqlalchemy.orm import aliased, joinedload, load_only
from sqlmodel import Session, select, asc, desc
import logging

from src.platfrom_integration import register_account
from src.views import update_platform_data
from src.config import PLATFORM_INTEGRATION_IS_ON, PLATFORM_INTEGRATION_URL

from src.models import Client, Affiliate, Status, Type
from src import engine

from src.api.v1.schemas import ClientCreateIn, ClientListIn, ClientListOut, ClientCreateOut, ClientListInPydantic
import string
import random


def generate_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(length))
    return password


logger_api = logging.getLogger("api")


def api_client_create(data: ClientCreateIn) -> ClientCreateOut:
    with Session(engine) as session:
        statement = select(Affiliate).where(Affiliate.auth_key == data.auth_key)
        auth = session.exec(statement).first()
    if auth:
        with Session(engine) as session:
            statement = select(Client).where(Client.email == data.email)
            unique_email = session.exec(statement).first()
        if unique_email:
            raise HTTPException(status_code=403, detail="Email Duplicate")
        with Session(engine) as session:
            statement = select(Client).where(Client.phone_number == data.phone_number)
            unique_phone = session.exec(statement).first()
        if unique_phone:
            raise HTTPException(status_code=403, detail="Phone Duplicate")
        new_client = Client(**data.dict(),
                            affiliate_id=auth.id,
                            department_id=auth.department_id,
                            desk_id=auth.desk_id,
                            responsible_id=auth.employee_id,
                            status_id=1,
                            type_id=1
                            )
        if PLATFORM_INTEGRATION_IS_ON:
            new_trader = register_account(new_client)
            new_client.trader_id = new_trader.id
            autologin = new_trader.autologin
            session.add(new_trader)
            session.commit()

            with Session(engine) as session:
                session.add(new_client)
                session.commit()
                session.refresh(new_client)
            logger_api.warning(f"created {new_client}")

            return ClientCreateOut(detail='success', autologin=f"https://{PLATFORM_INTEGRATION_URL}/autoologin?token={autologin}", data=new_client)
        else:
            with Session(engine) as session:
                session.add(new_client)
                session.commit()
                session.refresh(new_client)
            logger_api.warning(f"created {new_client}")
            return ClientCreateOut(detail='success', autologin='disabled', data=new_client)
    else:
        logger_api.warning(f"incorrect auth_key {auth}")
        raise HTTPException(status_code=401, detail="there is no such auth_key")


def filter_sqlalchemy_attributes(data):
    return {key: value for key, value in data.items() if not key.startswith('_sa_')}


def api_client_list(data: ClientListInPydantic) -> ClientListOut:
    with Session(engine) as session:
        statement = select(Affiliate).where(Affiliate.auth_key == data.auth_key)
        auth = session.exec(statement).first()
    if auth:
        with Session(engine) as session:
            sorting_order = asc if data.sorting_order == 'asc' else desc
            status_alias = aliased(Status)
            statement = select(Client, Status.name, Type.name).join(Status, Client.status_id == Status.id).join(Type, Client.type_id == Type.id).where(Client.affiliate_id == auth.id).where(Client.id.notin_(data.ignoreClientIds)).order_by(sorting_order(Client.id)).offset(data.offset)
            if data.limit > 0:
                statement = statement.limit(data.limit)
            if data.date_from:
                statement = statement.where(Client.creation_date >= data.date_from)
            if data.date_to:
                statement = statement.where(Client.creation_date <= data.date_to)
            if data.during_last_minutes:
                now = datetime.utcnow()
                time_threshold = now - timedelta(minutes=data.during_last_minutes)
                statement = statement.where(Client.creation_date >= time_threshold)
            if data.return_count == 0:
                result = session.exec(statement).all()
                count = len(result)
                response_data = [
                    {**filter_sqlalchemy_attributes(item[0].__dict__), "status": item[1], "type": item[2]} for item in result
                ]
                return ClientListOut(detail='success', count=count, data=response_data)
            else:
                result = session.exec(statement).all()
                count = len(result)
                return ClientListOut(detail='success', count=count)
    else:
        raise HTTPException(status_code=401, detail="there is no such  auth_key")
