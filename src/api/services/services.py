from sqlmodel import Session, select

from src import engine
from src.models import Status, Type


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
