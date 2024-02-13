from sqlmodel import select, Session

from src import engine
from src.config import ADMIN_PSWD
from src.models import Role, Employee, Type, Status


def seed_database():
    with Session(engine) as session:
        statement = select(Role).where(Role.id == 1)
        result = session.exec(statement).first()
        if result is None:
            session.add(
                Role(
                    name="sys_admin",
                    sys_admin=1,
                    head=1,
                    department_leader=1,
                    desk_leader=1,
                    accounts_can_access=1,
                    roles_can_access=1,
                    clients_can_access=1,
                    retain=1,
                )
            )
            session.add(
                Role(
                    name="ceo",
                    sys_admin=1,
                    head=0,
                    department_leader=0,
                    desk_leader=0,
                    accounts_can_access=1,
                    roles_can_access=1,
                    clients_can_access=1,
                    retain=1,
                )
            )
            session.add(
                Role(
                    name="Head",
                    sys_admin=0,
                    head=1,
                    department_leader=0,
                    desk_leader=0,
                    accounts_can_access=1,
                    roles_can_access=0,
                    clients_can_access=1,
                    retain=1,
                )
            )
            session.add(
                Role(
                    name="Department leader",
                    sys_admin=0,
                    head=0,
                    department_leader=1,
                    desk_leader=0,
                    accounts_can_access=1,
                    roles_can_access=0,
                    clients_can_access=1,
                    retain=1,
                )
            )
            session.add(
                Role(
                    name="Desk leader",
                    sys_admin=0,
                    head=0,
                    department_leader=0,
                    desk_leader=1,
                    accounts_can_access=1,
                    roles_can_access=0,
                    clients_can_access=1,
                    retain=0,
                )
            )
            session.add(
                Role(
                    name="Sale",
                    sys_admin=0,
                    head=0,
                    department_leader=0,
                    desk_leader=0,
                    accounts_can_access=0,
                    roles_can_access=0,
                    clients_can_access=1,
                    retain=0,
                )
            )
            session.add(
                Role(
                    name="Retain",
                    sys_admin=0,
                    head=0,
                    department_leader=0,
                    desk_leader=0,
                    accounts_can_access=0,
                    roles_can_access=0,
                    clients_can_access=1,
                    retain=1,
                )
            )
            session.commit()

            session.add(
                Status(
                    name="New",
                    hide=0,
                )
            )
            session.add(
                Status(
                    name="No answer",
                    hide=0,
                )
            )
            session.add(
                Status(
                    name="Call back",
                    hide=0,
                )
            )
            session.add(
                Status(
                    name="Never answer",
                    hide=0,
                )
            )
            session.add(
                Status(
                    name="Wrong language",
                    hide=0,
                )
            )
            session.add(
                Status(
                    name="Wrong number",
                    hide=0,
                )
            )
            session.add(
                Status(
                    name="Wrong person",
                    hide=0,
                )
            )
            session.add(
                Status(
                    name="No potential",
                    hide=0,
                )
            )
            session.add(
                Status(
                    name="Low potential",
                    hide=0,
                )
            )
            session.add(
                Status(
                    name="Deposit",
                    hide=0,
                )
            )
            session.add(
                Status(
                    name="Archived",
                    hide=1,
                )
            )
            session.commit()
            session.add(
                Type(
                    name="Lead"
                )
            )
            session.add(
                Type(
                    name="Demo"
                )
            )
            session.add(
                Type(
                    name="Live"
                )
            )
            session.commit()

            session.add(
                Employee(
                    login="admin",
                    password=ADMIN_PSWD,
                    role_id=1,
                    name="sys_admin"
                )
            )
            session.commit()
