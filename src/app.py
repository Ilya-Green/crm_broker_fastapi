from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, PlainTextResponse
from starlette.routing import Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette_admin.contrib.sqlmodel import Admin
# from starlette_admin import Admin
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from .api.services.api import statusesRouter
from .provider import MyAuthProvider
from sqlmodel import Session, select
import requests
import traceback
import logging
import sentry_sdk
from fastapi import Response, Request
from starlette.background import BackgroundTask
from fastapi.routing import APIRoute
from starlette.types import Message

from sqlmodel import SQLModel

from .config import APP_SECRET, APP_DOMAIN, APP_TYPE, TG_TOKEN, TG_CHAT_ID, SENTRY_TOKEN, SENTRY_RATE, CRM_NAME
from .models import Employee, Role, Client, Note, Desk, Action, Department, Status, Affiliate, Type, Trader, Order, \
    RetainStatus, Transaction
from .seed_database import seed_database
from .views import MyModelView, EmployeeView, ClientsView, RolesView, DepartmentsView, DesksView, AffiliatesView, \
    StatusesView, TypesView, TradersView, OrdersView, RetainStatusesView, TransactionsView
from . import engine
from src.api.v1.api import affApiV1


def init_database() -> None:
    SQLModel.metadata.create_all(engine)
    seed_database()


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
    if APP_TYPE != "DEV":
        logger.warning(f"{APP_DOMAIN} : {APP_TYPE} : server_turned_on")
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage?chat_id={TG_CHAT_ID}&text={APP_DOMAIN} : {APP_TYPE} : server_turned_on"
        print(requests.get(url).json())


# @app.exception_handler(Exception)
# async def handle_exception(request, exc):
#     traceback_error = traceback.format_exc()
#     if APP_TYPE != "DEV":
#         logger.warning(f"{APP_DOMAIN} : {APP_TYPE} : server_turned_on")
#         chunks = [traceback_error[i:i+4086] for i in range(0, len(traceback_error), 4086)]
#         for chunk in chunks:
#             url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage?chat_id={TG_CHAT_ID}&text={APP_TYPE}: {chunk}"
#             print(requests.get(url).json())
#     return PlainTextResponse("Oops! Something went wrong.", status_code=500)


logger_api = logging.getLogger("api")
#
#


def log_info(req_body, res_body, status_code):
    if status_code >= 400:
        logger_api.error(req_body)
        logger_api.error(res_body)


async def set_body(request: Request, body: bytes):
    async def receive() -> Message:
        return {'type': 'http.request', 'body': body}

    request._receive = receive


@app.middleware('http')
async def some_middleware(request: Request, call_next):
    req_body = await request.body()
    await set_body(request, req_body)
    response = await call_next(request)

    res_body = b''
    async for chunk in response.body_iterator:
        res_body += chunk
    path = request.url.path
    if path == '/api/v1/client/create/':
        task = BackgroundTask(log_info, req_body, res_body, response.status_code)
        return Response(content=res_body, status_code=response.status_code,
                        headers=dict(response.headers), media_type=response.media_type, background=task)
    return Response(content=res_body, status_code=response.status_code,
                    headers=dict(response.headers), media_type=response.media_type)


# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     # print(request.)
#     response = await call_next(request)
#     # if response.status_code >= 400:
#
#         # logger_api.error(f'Request to {request.url.path} returned status code {response.status_code}')
#     return response


class CustomAdmin(Admin):
    def custom_render_js(self, request: Request) -> Optional[str]:
        return request.url_for("static", path="js/custom_render.js")


admin = CustomAdmin(engine,
              title=CRM_NAME,
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
admin.add_view(TradersView(Trader, label="Traders"))
admin.add_view(TransactionsView(Transaction, label="Transactions"))
admin.add_view(OrdersView(Order, label="Order"))

admin.add_view(MyModelView(Note))
admin.add_view(MyModelView(Action))
admin.add_view(StatusesView(Status, label="Statuses"))
admin.add_view(RetainStatusesView(RetainStatus, label="Retain Statuses"))
admin.add_view(TypesView(Type, label="Types"))

# Mount to admin to app
admin.mount_to(app)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(affApiV1, prefix="/api",)
app.include_router(statusesRouter, prefix="/api",)


if APP_TYPE != "DEV":
    sentry_sdk.init(
        dsn=SENTRY_TOKEN,

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production,
        traces_sample_rate=SENTRY_RATE,
    )


@app.on_event("shutdown")
async def shutdown_event():
    if APP_TYPE != "DEV":
        logger.warning(f"{APP_TYPE}: server_turned_off")
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage?chat_id={TG_CHAT_ID}&text={APP_DOMAIN} : {APP_TYPE} : server_turned_off"
        print(requests.get(url).json())
