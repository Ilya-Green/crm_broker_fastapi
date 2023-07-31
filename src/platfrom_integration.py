import json
import logging
import time
from typing import Any

import requests
from sqlmodel import Session, select

from src import engine
from src.models import Trader, Client, Order, Transaction

logger = logging.getLogger("api")


def update_platform_data():
    params = {'token': 'value1'}
    response = requests.get(url='https://general-investment.com/api/admin/user/all', params=params)
    data = json.loads(response.content)
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
            autologin_link="https://general-investment.com/autoologin?token=" + autologin if autologin else ""
        )
        if current_trader is not None:
            new_trader.responsible_id = current_trader.responsible_id
            new_trader.status_id = current_trader.status_id
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
    response = requests.get(url='https://general-investment.com/api/admin/order/all', params=params)
    data = json.loads(response.content)
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
    response = requests.get(url='https://general-investment.com/api/admin/transaction/all', params=params)
    data = json.loads(response.content)
    for transaction_data in data:
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
    print("updated")


def update_platform_data_by_id(ids: list):
    start_time = time.time()
    params = {'token': 'value1'}
    response = requests.get(url='https://general-investment.com/api/admin/user/all', params=params)
    data = json.loads(response.content)
    for user_data in data:
        if user_data["id"] in ids:
            print(user_data["id"])
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
                autologin_link="https://general-investment.com/autoologin?token=" + autologin if autologin else ""
            )
            if current_trader is not None:
                new_trader.responsible_id = current_trader.responsible_id
                new_trader.status_id = current_trader.status_id
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
    response = requests.get(url='https://general-investment.com/api/admin/order/all', params=params)
    data = json.loads(response.content)
    for user_data in data:
        if user_data["userId"] in ids:
            print(user_data["userId"])
            new_order = Order(
                wid=user_data["_id"],
                id=user_data["id"],
                asset_name=user_data["assetName"],
                amount=user_data["amount"],
                opening_price=user_data["openingPrice"],
                pledge=user_data["pledge"],
                user_id=user_data["userId"],
                type=user_data["type"],
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
    response = requests.get(url='https://general-investment.com/api/admin/transaction/all', params=params)
    data = json.loads(response.content)
    for transaction_data in data:
        if user_data["userId"] in ids:
            print(user_data["userId"])
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
    print("updated: ", time.time() - start_time)


def update_orders():
    params = {'token': 'value1'}
    response = requests.get(url='https://general-investment.com/api/admin/order/all', params=params)
    data = json.loads(response.content)
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
    start_time = time.time()
    params = {'token': 'value1'}
    response = requests.get(url='https://general-investment.com/api/admin/order/all', params=params)
    data = json.loads(response.content)
    for user_data in data:
        if user_data["id"] == id:
            order_to_update = Order(
                wid=user_data["_id"],
                id=user_data["id"],
                asset_name=user_data["assetName"],
                amount=user_data["amount"],
                opening_price=user_data["openingPrice"],
                pledge=user_data["pledge"],
                user_id=user_data["userId"],
                type=user_data["type"],
                is_closed=user_data["isClosed"],
                created_at=user_data["createdAt"],
                take_profit=user_data["takeProfit"],
                stop_loss=user_data["stopLoss"],
                auto_close=user_data["autoClose"],
                v=user_data["__v"],
                closed_at=user_data.get("closedAt"),
                closed_price=user_data.get("closedPrice")
            )
            break
    if order_to_update:
        with Session(engine) as session:
            session.merge(order_to_update)
            session.commit()
    print(f'{id}: ', time.time() - start_time)


def edit_order_platform(obj: Any,):
    url = "https://general-investment.com/api/admin/order/edit"
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
    url = "https://general-investment.com/api/admin/user/edit"
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
        logger.info(f'Обновлены данные ордера: {obj}')
    else:
        print(response.status_code)
        print(response.content)
        logger.info(f'Неудачная попытка обновить данные ордера: {obj}')
        print("Ошибка при выполнении запроса")


def change_account_password_platform(trader: Trader, password: str):
    url = "https://general-investment.com/api/admin/user/edit"
    query_params = {
        "token": "value1",
    }
    body = {
        "name": trader.name,
        "surname": trader.surname,
        "accountNumber": trader.accountNumber,
        "email": trader.email,
        "phone": trader.phone_number,
        "country": trader.country,
        # "city": obj.city,
        # "address": obj.address,
        # "dirName": obj.dirName,
        "blocked": trader.blocked,
        "accountStatus": trader.accountStatus,
        "password": password,
        "isActive": trader.isActive,
        "isVipStatus": trader.isVipStatus,
        # "docs": {
        #     "others": []
        # },
        "id": trader.id
    }
    response = requests.put(url, params=query_params, json=body)
    if response.status_code == 200:
        print("Запрос успешно выполнен")
        print(response.content)
        logger.info(f'Обновлены данные ордера: {trader}')
    else:
        print(response.status_code)
        print(response.content)
        logger.info(f'Неудачная попытка обновить данные ордера: {trader}')
        print("Ошибка при выполнении запроса")


def create_transaction(trader: Trader, password: str):
    url = "https://general-investment.com/api/admin/user/edit"
    query_params = {
        "token": "value1",
    }
    body = {
        "name": trader.name,
        "surname": trader.surname,
        "accountNumber": trader.accountNumber,
        "email": trader.email,
        "phone": trader.phone_number,
        "country": trader.country,
        # "city": obj.city,
        # "address": obj.address,
        # "dirName": obj.dirName,
        "blocked": trader.blocked,
        "accountStatus": trader.accountStatus,
        "password": password,
        "isActive": trader.isActive,
        "isVipStatus": trader.isVipStatus,
        # "docs": {
        #     "others": []
        # },
        "id": trader.id
    }
    response = requests.put(url, params=query_params, json=body)
    if response.status_code == 200:
        print("Запрос успешно выполнен")
        print(response.content)
        logger.info(f'Обновлены данные ордера: {trader}')
    else:
        print(response.status_code)
        print(response.content)
        logger.info(f'Неудачная попытка обновить данные ордера: {trader}')
        print("Ошибка при выполнении запроса")