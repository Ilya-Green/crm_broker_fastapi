from fastapi import FastAPI
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
from starlette_admin.contrib.sqlmodel import Admin, ModelView
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from .provider import MyAuthProvider
from sqlmodel import Session, select

from sqlmodel import SQLModel

from .config import SECRET
from .models import Employee, Role, Client, Note, Desk, Action, Department, Status, Affiliate
from .views import MyModelView, EmployeeView, ClientsView, RolesView, DepartmentsView, DesksView, AffiliatesView
from . import engine
from .api import apiRouter


def init_database() -> None:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        statement = select(Role).where(Role.id == 1)
        result = session.exec(statement).first()
        if result is None:
            session.add(
                Role(
                    id=1,
                    name="sys_admin",
                    sys_admin=1,
                    head=1,
                    desk_leader=1,
                    accounts_can_access=1,
                    role_can_access=1,
                    clients_can_access=1,
                    roles_can_access=1,
                )
            )
            session.commit()
            with Session(engine) as session:
                session.add(
                    Employee(
                        id=1,
                        login="admin",
                        password="12345678",
                        role_id=1,
                    )
                )
                session.commit()



app = FastAPI(
    routes=[
        # Route(
        #     "/",
        #     lambda r: HTMLResponse('<a href="/admin/">Click me to get to Admin!</a>'),
        # )
    ],
    on_startup=[init_database],
)

# Create admin
admin = Admin(engine,
              title="CRM Broker",
              auth_provider=MyAuthProvider(),
              middlewares=[Middleware(SessionMiddleware, secret_key=SECRET, max_age=60*60)],
              base_url="/admin",
              templates_dir='src/templates',
              )

# Add views
admin.add_view(EmployeeView(Employee, label="Employees"))
admin.add_view(RolesView(Role, label="Roles"))
admin.add_view(DepartmentsView(Department))
admin.add_view(DesksView(Desk))

admin.add_view(AffiliatesView(Affiliate, label="Affiliates"))

admin.add_view(ClientsView(Client, label="Clients"))

admin.add_view(MyModelView(Note))
admin.add_view(MyModelView(Action))
admin.add_view(MyModelView(Status))

# Mount to admin to app
admin.mount_to(app)

app.include_router(apiRouter, prefix="/api/v1",)
