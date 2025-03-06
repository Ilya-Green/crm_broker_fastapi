"""
production integration backend tests
"""

import random

import httpx
import pytest
import pytest_asyncio
from pydantic import ValidationError
from sqlalchemy import create_engine, text

from src.config import Settings

BASE_URL = "http://127.0.0.1:8000"


@pytest.mark.asyncio
@pytest.mark.production
async def test_base():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/")
        assert response.status_code == 404
        response = await client.get("/admin")
        assert response.status_code == 307


@pytest_asyncio.fixture(scope="module")
async def env_vars():
    settings = Settings()
    return settings


@pytest.mark.production
def test_env_variables_load_correctly(env_vars):
    try:
        settings = env_vars
        assert isinstance(settings.db_uri, str)
        assert isinstance(settings.db_file, str)
        assert isinstance(settings.platform_integration_url, str)
        assert isinstance(settings.platform_integration_sync, bool)
    except ValidationError as e:
        pytest.fail(f"Env Validation error: {e}")


@pytest_asyncio.fixture(scope="module")
async def engine(env_vars):
    settings = env_vars
    engine = create_engine(settings.db_uri+settings.db_file, execution_options={"batch_mode": True}, echo=False)
    return engine


@pytest_asyncio.fixture(scope="module")
async def auth_cookie(engine):
    query = text("SELECT login, password FROM employee LIMIT 1")
    with engine.connect() as conn:
        user = conn.execute(query).fetchone()

    assert user
    assert user.login
    assert user.password

    payload = {"username": user.login, "password": user.password}

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/admin/login", data=payload)

    assert response.status_code == 303, "Ошибка аутентификации: неверный статус-код"

    cookies = response.cookies
    assert cookies, "Cookie is not received."

    return cookies


@pytest.mark.asyncio
@pytest.mark.production
async def test_api_login(auth_cookie):
    async with httpx.AsyncClient(base_url=BASE_URL, cookies=auth_cookie) as client:
        response = await client.get("/admin/api/client")

    assert response.status_code == 200, "Cookie is not working"


@pytest.mark.asyncio
@pytest.mark.production
async def test_main(auth_cookie, env_vars, engine):
    # create affiliate
    affiliate_name = f"test{random.randint(1,99999)}"
    payload = {"name": affiliate_name}
    async with httpx.AsyncClient(base_url=BASE_URL, cookies=auth_cookie) as client:
        response = await client.post("/admin/affiliate/create", data=payload)

    assert response.status_code == 303

    # get affiliate
    async with httpx.AsyncClient(base_url=BASE_URL, cookies=auth_cookie) as client:
        response = await client.get(f"/admin/api/affiliate?skip=0&limit=20&order_by=id%20asc&where={affiliate_name}")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data

    auth_key = next((item["auth_key"] for item in data["items"] if item["name"] == affiliate_name), None)
    assert auth_key is not None

    # create lead as affiliate by api
    payload = {
        "auth_key": auth_key,
        "first_name": "test",
        "second_name": "test",
        "email": f"test{random.randint(1,99999)}@example.com",
        "phone_number": f"{random.randint(1,9999999999)}",
    }

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/api/v1/client/create/", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "detail" in data

    # get leads list as affiliate by api
    email = payload.get("email")

    payload = {"auth_key": auth_key}

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/api/v1/client/list/", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "detail" in data

    client = next((item for item in data["data"] if item.get("email") == email), None)

    assert client

    # create note as admin
    note_content = f"test{random.randint(1,99999)}"
    client_id = client["id"]
    async with httpx.AsyncClient(base_url=BASE_URL, cookies=auth_cookie) as client:
        response = await client.post(f"/admin/api/client/action?pks={client_id}&name=add_note&note={note_content}&=&=")
    assert response.status_code == 200

    # get note as admin
    async with httpx.AsyncClient(base_url=BASE_URL, cookies=auth_cookie) as client:
        response = await client.get(f"/admin/api/client?skip=0&limit=20&order_by=id%20desc&where={email}")
    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    items = data["items"]

    client = next((item for item in items if item.get("email") == email), None)
    assert client

    assert "notes" in client

    assert client["notes"]

    note = next((note for note in client["notes"] if note.get("content") == note_content), None)
    assert note

    # pt integration tests section
    settings = env_vars
    if settings.platform_integration_is_on:
        # pt is available
        async with httpx.AsyncClient(base_url=f"https://{settings.platform_integration_url}", cookies=auth_cookie) as client:
            response = await client.get("/")

        assert response.status_code == 200

        # search for created trader by webhook
        if not settings.platform_integration_sync:
            query = text(f"SELECT id FROM trader WHERE email = '{email}' LIMIT 1")
            with engine.connect() as conn:
                user = conn.execute(query).fetchone()
            assert user

        # search for created trader by api
        async with httpx.AsyncClient(base_url=BASE_URL, cookies=auth_cookie) as client:
            headers = {"Referer": f"{BASE_URL}/admin/trader/list?hide=false"}
            response = await client.get(f"/admin/api/trader?skip=0&limit=20&order_by=id%20asc&where={email}&hide=false", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        trader = next((item for item in data["items"] if item["email"] == email), None)
        assert trader

        # create deposit for trader
        trader_id = trader["id"]
        deposit_summ = random.randint(1,3000)
        async with httpx.AsyncClient(base_url=BASE_URL, cookies=auth_cookie) as client:
            response = await client.post(f"/admin/api/trader/action?pks={trader_id}&name=create_deposit&value={deposit_summ}&selectOption=deposit&description=test", data=payload)
        assert response.status_code == 200

        async with httpx.AsyncClient(base_url=BASE_URL, cookies=auth_cookie) as client:
            headers = {"Referer": f"{BASE_URL}/admin/trader/list?hide=false"}
            response = await client.get(f"/admin/api/trader?skip=0&limit=20&order_by=id%20asc&where={email}&hide=false", headers=headers)

        async with httpx.AsyncClient(base_url=BASE_URL, cookies=auth_cookie) as client:
            headers = {"Referer": f"{BASE_URL}/admin/trader/list?hide=false"}
            response = await client.get(f"/admin/api/trader?skip=0&limit=20&order_by=id%20asc&where={email}&hide=false", headers=headers)

        assert response.status_code == 200

        data = response.json()
        trader = next((item for item in data["items"] if item["email"] == email), None)
        print(trader)
        assert trader
        assert float(trader["balance"]) >= deposit_summ
        transaction = next((item for item in trader["transactions"] if item["value"] == deposit_summ), None)
        assert transaction

