import json
import logging
import random
import string
import time
from typing import Any

import requests
from sqlmodel import Session, select

from src import engine
from src.config import PLATFORM_INTEGRATION_IS_ON, PLATFORM_INTEGRATION_URL
from src.models import Trader, Client, Order, Transaction
from starlette_admin.exceptions import ActionFailed, FormValidationError

logger = logging.getLogger("api")


def generate_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

def register_account(client: Client):
    if PLATFORM_INTEGRATION_IS_ON:
        url = f"https://{PLATFORM_INTEGRATION_URL}/api/client/user/autologin"
        payload = {
            "name": client.first_name,
            "surname": client.second_name,
            "email": client.email,
            "password": generate_password(10),
            "phone": client.phone_number,
            "date": 1685823000002,
            "country": 'RU',
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(url, data=payload)
        # print(response.content)
        if response.status_code == 403:
            logger.warning(f"register account error {client} {response.content}")
            raise ActionFailed("Something went wrong")
            raise HTTPException(status_code=403, detail="Duplicate")
        print(response.content)
        user_data = json.loads(response.content.decode())
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
            date=user_data["date"],
            # date=datetime.fromtimestamp(user_data["date"]/1000),
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
            autologin_link=f"https://{PLATFORM_INTEGRATION_URL}/autoologin?token=" + autologin if autologin else "",
            status_id=1,
        )
        return new_trader


last_execution_time = None


def update_platform_data():
    global last_execution_time
    current_time = time.time()
    if last_execution_time is None or current_time - last_execution_time > 30:
        pass
    else:
        return
    last_execution_time = time.time()
    if PLATFORM_INTEGRATION_IS_ON:
        params = {'token': 'value1'}
        response = requests.get(url=f'https://{PLATFORM_INTEGRATION_URL}/api/admin/user/all', params=params)
        data = response.json()
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
                date=user_data["date"],
                # date=datetime.fromtimestamp(user_data["date"]/1000),
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
                autologin_link=f"https://{PLATFORM_INTEGRATION_URL}/autoologin?token=" + autologin if autologin else "",
                status_id=1,
            )
            if current_trader is not None:
                new_trader.responsible_id = current_trader.responsible_id
                new_trader.status_id = current_trader.status_id
                new_trader.last_note = current_trader.last_note
                if user_data["balance"] is not None and user_data["balance"] > 0:
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
        response = requests.get(url=f'https://{PLATFORM_INTEGRATION_URL}/api/admin/order/all', params=params)
        data = response.json()
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
                spread=user_data["spread"],
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
        response = requests.get(url=f'https://{PLATFORM_INTEGRATION_URL}/api/admin/transaction/all', params=params)
        data = response.json()
        for transaction_data in data:
            new_transaction = Transaction(
                id=transaction_data["id"],
                content=transaction_data.get("content").encode('utf-8'),
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


def update_platform_data_by_id(ids: list):
    if PLATFORM_INTEGRATION_IS_ON:
        params = {'token': 'value1'}
        response = requests.get(url=f'https://{PLATFORM_INTEGRATION_URL}/api/admin/user/all', params=params)
        data = response.json()
        for user_data in data:
            if user_data["id"] in ids:
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
                    date=user_data["date"],
                    # date=datetime.fromtimestamp(user_data["date"]/1000),
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
                    autologin_link=f"https://{PLATFORM_INTEGRATION_URL}/autoologin?token=" + autologin if autologin else "",
                    status_id=1,
                )
                if current_trader is not None:
                    new_trader.responsible_id = current_trader.responsible_id
                    new_trader.status_id = current_trader.status_id
                    new_trader.last_note = current_trader.last_note
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
        response = requests.get(url=f'https://{PLATFORM_INTEGRATION_URL}/api/admin/order/all', params=params)
        data = response.json()
        for user_data in data:
            if user_data["userId"] in ids:
                new_order = Order(
                    wid=user_data["_id"],
                    id=user_data["id"],
                    asset_name=user_data["assetName"],
                    amount=user_data["amount"],
                    opening_price=user_data["openingPrice"],
                    pledge=user_data["pledge"],
                    user_id=user_data["userId"],
                    type=user_data["type"],
                    spread=user_data["spread"],
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
        response = requests.get(url=f'https://{PLATFORM_INTEGRATION_URL}/api/admin/transaction/all', params=params)
        data = response.json()
        for transaction_data in data:
            if transaction_data["userId"] in ids:
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


def update_orders():
    if PLATFORM_INTEGRATION_IS_ON:
        params = {'token': 'value1'}
        response = requests.get(url=f'https://{PLATFORM_INTEGRATION_URL}/api/admin/order/all', params=params)
        data = response.json()
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
                spread=user_data["spread"],
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


def update_order(id: int):
    if PLATFORM_INTEGRATION_IS_ON:
        params = {'token': 'value1'}
        response = requests.get(url=f'https://{PLATFORM_INTEGRATION_URL}/api/admin/order/all', params=params)
        data = response.json()
        order_to_update = None
        for order_data in data:
            if order_data["id"] == id:
                order_to_update = Order(
                    wid=order_data["_id"],
                    id=order_data["id"],
                    asset_name=order_data["assetName"],
                    amount=order_data["amount"],
                    opening_price=order_data["openingPrice"],
                    pledge=order_data["pledge"],
                    user_id=order_data["userId"],
                    type=order_data["type"],
                    spread=order_data["spread"],
                    is_closed=order_data["isClosed"],
                    created_at=order_data["createdAt"],
                    take_profit=order_data["takeProfit"],
                    stop_loss=order_data["stopLoss"],
                    auto_close=order_data["autoClose"],
                    v=order_data["__v"],
                    closed_at=order_data.get("closedAt"),
                    closed_price=order_data.get("closedPrice")
                )
                break
        if order_to_update:
            with Session(engine) as session:
                session.merge(order_to_update)
                session.commit()


def edit_order_platform(obj: Any,):
    if PLATFORM_INTEGRATION_IS_ON:
        if obj.stop_loss is not None and obj.stop_loss == 0:
            raise FormValidationError({'stop_loss': 'not 0'})
        if obj.take_profit is not None and obj.take_profit == 0:
            raise FormValidationError({'take_profit': 'not 0'})
        if obj.stop_loss is not None and obj.stop_loss < 0:
            raise FormValidationError({'stop_loss': 'positive number only'})
        if obj.take_profit is not None and obj.take_profit < 0:
            raise FormValidationError({'take_profit': 'positive number only'})

        url = f"https://{PLATFORM_INTEGRATION_URL}/api/admin/order/edit"
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
            "spread": obj.spread,
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
    if PLATFORM_INTEGRATION_IS_ON:
        url = f"https://{PLATFORM_INTEGRATION_URL}/api/admin/user/edit"
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
            logger.info(f'Обновлены данные трейдера: {obj}')
        else:
            print(response.status_code)
            print(response.content)
            logger.info(f'Неудачная попытка обновить данные трейдера: {obj}')
            print("Ошибка при выполнении запроса")


def change_account_password_platform(trader: Trader, password: str):
    if PLATFORM_INTEGRATION_IS_ON:
        url = f"https://{PLATFORM_INTEGRATION_URL}/api/admin/user/edit"
        query_params = {
            "token": "value1",
        }
        body = {
            # "name": trader.name,
            # "surname": trader.surname,
            # "accountNumber": trader.accountNumber,
            # "email": trader.email,
            # "phone": trader.phone_number,
            # "country": trader.country,
            # "city": obj.city,
            # "address": obj.address,
            # "dirName": obj.dirName,
            # "blocked": trader.blocked,
            # "accountStatus": trader.accountStatus,
            "password": password,
            # "isActive": trader.isActive,
            # "isVipStatus": trader.isVipStatus,
            # "docs": {
            #     "others": []
            # },
            "id": trader.id
        }
        response = requests.put(url, params=query_params, json=body)
        if response.status_code == 200:
            print("Запрос успешно выполнен")
            print(response.content)
            logger.info(f'Обновлены пароль трейдера: {trader}')
        else:
            print(response.status_code)
            print(response.content)
            logger.info(f'Неудачная попытка обновить пароль трейдера: {trader}')
            print("Ошибка при выполнении запроса")


def change_account_balance_platform(trader: Trader, mainBalance: str, bonuses: str, credFacilities: str):
    if PLATFORM_INTEGRATION_IS_ON:
        url = f"https://{PLATFORM_INTEGRATION_URL}/api/admin/user/edit"
        query_params = {
            "token": "value1",
        }
        body = {
            "id": trader.id
        }

        if mainBalance is not None:
            try:
                body["mainBalance"] = int(mainBalance)
                body["balance"] = int(mainBalance)
            except ValueError:
                pass

        if bonuses is not None:
            try:
                body["bonuses"] = int(bonuses)
            except ValueError:
                pass

        if credFacilities is not None:
            try:
                body["credFacilities"] = int(credFacilities)
            except ValueError:
                pass

        response = requests.put(url, params=query_params, json=body)
        if response.status_code == 200:
            print("Запрос успешно выполнен")
            print(response.content)
            logger.info(f'Обновлен баланс трейдера: {trader} {mainBalance},  {bonuses}, {credFacilities}')
        else:
            print(response.status_code)
            print(response.content)
            logger.info(f'Неудачная попытка обновить баланс трейдера: {trader}')
            print("Ошибка при выполнении запроса")
            raise ActionFailed("Sorry, something went wrong")


def create_transaction(trader: Trader, value: int, type: str, description: str):
    if PLATFORM_INTEGRATION_IS_ON:
        url = f"https://{PLATFORM_INTEGRATION_URL}/api/admin/transaction/save?token=token"
        payload = json.dumps({
            "dirName": "1lsalz1zn",
            "value": str(value),
            "content": description,
            "userId": trader.id,
            "type": type,
        })
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            print("Запрос успешно выполнен")
            print(response.content)
            logger.info(f'Добавлена транзакция: {trader} : {value}$ {type} {description}')
        else:
            print(response.status_code)
            print(response.content)
            logger.info(f'Неудачная попытка добавления транзакции: {trader} : {value}$ {type} {description}')
            print("Ошибка при выполнении запроса")