from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, PlainTextResponse
from starlette.routing import Route
from starlette_admin.contrib.sqlmodel import Admin, ModelView
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from .provider import MyAuthProvider
from sqlmodel import Session, select
import requests
import traceback
import logging

from sqlmodel import SQLModel

from .config import APP_SECRET, APP_NAME, TG_TOKEN, TG_CHAT_ID
from .models import Employee, Role, Client, Note, Desk, Action, Department, Status, Affiliate
from .views import MyModelView, EmployeeView, ClientsView, RolesView, DepartmentsView, DesksView, AffiliatesView, StatusesView
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
)


# url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

logger = logging.getLogger("uvicorn.access")


@app.on_event("startup")
async def startup_event():
    init_database()
    if APP_NAME != "DEV":
        logger.warning(f"{APP_NAME}: server_turned_on")
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage?chat_id={TG_CHAT_ID}&text={APP_NAME}: server_turned_on"
        print(requests.get(url).json())


@app.exception_handler(Exception)
async def handle_exception(request, exc):
    traceback_error = traceback.format_exc()
    if APP_NAME != "DEV":
        chunks = [traceback_error[i:i+4086] for i in range(0, len(traceback_error), 4086)]
        for chunk in chunks:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage?chat_id={TG_CHAT_ID}&text={APP_NAME}: {chunk}"
            print(requests.get(url).json())
    return PlainTextResponse("Oops! Something went wrong.", status_code=500)


# logger_api = logging.getLogger("api")
#
#
# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     response = await call_next(request)
#     if response.status_code >= 400:
#         print(request.body)
#         logger_api.error(f'Request to {request.url.path} returned status code {response.status_code}')
#     return response


# Create admin
admin = Admin(engine,
              title="CRM Broker",
              auth_provider=MyAuthProvider(),
              middlewares=[Middleware(SessionMiddleware, secret_key=APP_SECRET, max_age=60*60)],
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
admin.add_view(StatusesView(Status, label="Statuses"))

# Mount to admin to app
admin.mount_to(app)

app.include_router(apiRouter, prefix="/api/v1",)


@app.on_event("shutdown")
async def shutdown_event():
    if APP_NAME != "DEV":
        logger.warning(f"{APP_NAME}: server_turned_off")
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage?chat_id={TG_CHAT_ID}&text={APP_NAME}: server_turned_off"
        print(requests.get(url).json())
