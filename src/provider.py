from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminUser, AuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlmodel import Session, select, join
import pprint

from .models import Employee, Role, Desk, Department
from . import engine


logger = logging.getLogger("crm")


class MyAuthProvider(AuthProvider):
    """
    This is for demo purpose, it's not a better
    way to save and validate user credentials
    """

    async def login(
            self,
            username: str,
            password: str,
            remember_me: bool,
            request: Request,
            response: Response,
    ) -> Response:
        if len(username) < 3:
            """Form data validation"""
            raise FormValidationError(
                {"username": "Ensure username has at least 03 characters"}
            )

        with Session(engine) as session:
            statement = select(Employee).where(Employee.login == username, Employee.password == password)
            result = session.exec(statement).first()
        if result:
            """Save `username` in session"""
            if result.role_id is None:
                raise FormValidationError(
                    {"username": "the role must be assigned by the system administrator"}
                )
            request.session.update({"username": username})
            request.session.update({"password": password})
            logger.info("User %s logged in successfully", username)
            logger.info("Browser fingerprint: %s", request.headers.get('User-Agent'))
            logger.info("User IP: %s", request.client.host)
            return response
        logger.warning("Login failed for user: %s", username, password)
        raise LoginFailed("Invalid username or password")

    async def is_authenticated(self, request) -> bool:
        # with Session(engine) as session:
        #     new_client = Client(first_name="Test", status_id=1, email="mail@mail.com", phone_number="+12431412312")
        #     session.add(new_client)
        #     session.commit()
        # request.state.user = users.get(request.session["username"])
        username = request.session.get("username", None)
        password = request.session.get("password", None)
        with Session(engine) as session:
            user = select(Employee).where(Employee.login == username, Employee.password == password)
            result = session.exec(user).first()
        if result:
            """
            Save current `user` object in the request state. Can be used later
            to restrict access to connected user.
            """
            data = {"id": result.id,
                    "name": result.login,
                    "role_id": result.role_id,
                    "desk_id": None,
                    "department_id": result.department_id,
                    # "department_head": result.department_head
                    }
            with Session(engine) as session:
                # print(result.desk_id)
                user = select(Desk).where(Desk.id == result.desk_id)
                desk = session.exec(user).first()
            if desk:
                data["desk_id"] = desk.id
                data["department_id"] = desk.department_id
            # with Session(engine) as session:
            #     user = select(Department).where(Department.leader_id == result.id)
            #     department = session.exec(user).first()
            # if department:
            #     data["department_id"] = department.id

            with Session(engine) as session:
                user = select(Role).where(Role.id == result.role_id)
                test = session.exec(user).first()
                if test:
                    test_dict = test.to_dict()
                    data.update(test_dict)
            request.state.user = data
            return True
        return False

    def get_admin_user(self, request: Request) -> AdminUser:
        user = request.state.user  # Retrieve current user
        photo_url = None
        # if user["avatar"] is not None:
        #     photo_url = request.url_for("static", path=user["avatar"])
        return AdminUser(username=user["name"], photo_url=photo_url, role=user["role"])

    async def logout(self, request: Request, response: Response) -> Response:
        request.session.clear()
        return response
