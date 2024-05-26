from sqlmodel import Session, select

from src import engine
from src.api.pt_webhook.schemas import OrderUpdate, TransactionUpdate
from src.config import PLATFORM_INTEGRATION_URL
from src.models import Trader, Order, Transaction, Client, WhitelistWebhook


def update_whitelist():
    with Session(engine) as session:
        statement = select(WhitelistWebhook)
        results = session.exec(statement)
        ips = [result.ipaddress for result in results]
        return ips


def create_trader_webhook(trader: Trader):
    trader.autologin_link = f"https://{PLATFORM_INTEGRATION_URL}/autoologin?token=" + trader.autologin if trader.autologin else "",

    with Session(engine) as session:
        statement = select(Trader).where(Trader.id == trader.id)
        existing_trader = session.exec(statement).first()
    if existing_trader is not None:
        trader.responsible_id = existing_trader.responsible_id
        trader.status_id = existing_trader.status_id
        trader.last_note = existing_trader.last_note
        if trader.balance > 0:
            with Session(engine) as session:
                statement = select(Client).where(Client.trader_id == trader.id)
                current_client = session.exec(statement).first()
            if current_client:
                current_client.type_id = 3
                session.merge(current_client)
                session.commit()

    with Session(engine) as session:
        session.merge(trader)
        session.commit()


def create_order_webhook(order: Order):
    with Session(engine) as session:
        session.merge(order)
        session.commit()


def update_order_webhook(order: OrderUpdate):
    with Session(engine) as session:
        session.merge(order)
        session.commit()


def create_transaction_webhook(transaction: Transaction):
    with Session(engine) as session:
        session.merge(transaction)
        session.commit()


def update_transaction_webhook(transaction: TransactionUpdate):
    with Session(engine) as session:
        session.merge(transaction)
        session.commit()
