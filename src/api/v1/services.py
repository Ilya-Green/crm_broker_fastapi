import json
from fastapi import HTTPException
import requests
from sqlalchemy.orm import aliased, joinedload, load_only
from sqlmodel import Session, select, asc, desc
import logging
from src.views import update_platform_data
from src.config import PLATFORM_INTEGRATION_IS_ON, PLATFORM_INTEGRATION_URL

from src.models import Client, Affiliate, Status, Type
from src import engine

from src.api.v1.schemas import ClientCreateIn, ClientListIn, ClientListOut, ClientCreateOut
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
        if PLATFORM_INTEGRATION_IS_ON:
            url = f"{PLATFORM_INTEGRATION_URL}/api/client/user/autologin"
            payload = {
                "name": data.first_name,
                "surname": data.second_name,
                "email": data.email,
                "password": generate_password(10),
                "phone": data.phone_number,
                "date": 1685823000002,
                "country": data.country_code,
            }
            headers = {
                "Content-Type": "application/json"
            }
            response = requests.post(url, data=payload)
            response_json = json.loads(response.content.decode())
            if response.status_code == 403:
                logger_api.warning(f"already registered in platform {data}")
                raise HTTPException(status_code=403, detail="Duplicate")
            update_platform_data()

            with Session(engine) as session:
                new_client = Client(**data.dict(),
                                    affiliate_id=auth.id,
                                    status_id=1,
                                    type_id=1,
                                    trader_id=response_json["userId"],
                                    )
                session.add(new_client)
                session.commit()
                session.refresh(new_client)
            logger_api.warning(f"created {new_client}")
            # return JSONResponse(['success',
            #                        {new_client},
            #                        "https://general-investment.com/autologin?token="])
            autologin = response_json["autologin"]
            return ClientCreateOut(detail='success', autologin=f"{PLATFORM_INTEGRATION_URL}/autoologin?token={autologin}")
        else:
            with Session(engine) as session:
                new_client = Client(**data.dict(),
                                    affiliate_id=auth.id,
                                    status_id=1,
                                    type_id=1
                                    )
                session.add(new_client)
                session.commit()
                session.refresh(new_client)
            logger_api.warning(f"created {new_client}")
            return ClientCreateOut(detail='success', autologin='disabled')
    else:
        logger_api.warning(f"incorrect auth_key {auth}")
        raise HTTPException(status_code=401, detail="there is no such auth_key")


def filter_sqlalchemy_attributes(data):
    return {key: value for key, value in data.items() if not key.startswith('_sa_')}


def api_client_list(data: ClientListIn) -> ClientListOut:
    with Session(engine) as session:
        statement = select(Affiliate).where(Affiliate.auth_key == data.auth_key)
        auth = session.exec(statement).first()
    if auth:
        with Session(engine) as session:
            sorting_order = desc if data.sorting_order == 'desc' else asc
            status_alias = aliased(Status)
            statement = select(Client, Status.name, Type.name).join(Status, Client.status_id == Status.id).join(Type, Client.type_id == Type.id).where(Client.affiliate_id == auth.id).where(Client.id.notin_(data.ignoreClientIds)).order_by(sorting_order(data.sorting_field)).offset(data.offset)
            if data.limit > 0:
                statement.limit(data.limit)
            if data.return_count == 0:
                result = session.exec(statement).all()
                response_data = [
                    {**filter_sqlalchemy_attributes(item[0].__dict__), "status": item[1], "type": item[2]} for item in result
                ]
                return ClientListOut(detail='success', data=response_data)
            else:
                result = session.exec(statement).all()
                count = len(result)
                return ClientListOut(detail='success', data=count)
    else:
        raise HTTPException(status_code=401, detail="there is no such  auth_key")
