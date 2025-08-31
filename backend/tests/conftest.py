import pytest_asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.db import (
    engine,
    get_async_session as app_get_async_session,
)
from app.config import settings
from app.crud_user import get_or_create_user, issue_access_token

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession


@pytest_asyncio.fixture
async def async_session():
    # Transactional session with rollback after each test
    async with engine.connect() as conn:
        trans = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)

        # Start a SAVEPOINT so session.commit() doesn't end outer transaction
        await conn.begin_nested()

        @event.listens_for(session.sync_session, "after_transaction_end")
        def restart_savepoint(sess, transaction):
            if transaction.nested and not transaction._parent.nested:
                sess.begin_nested()

        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(async_session):
    """Unauthenticated TestClient bound to the per-test async_session."""

    async def override():
        yield async_session

    app.dependency_overrides[app_get_async_session] = override

    with TestClient(app, base_url=f"http://testserver{settings.API_V1_STR}") as c:
        yield c

    app.dependency_overrides.pop(app_get_async_session, None)


@pytest_asyncio.fixture
async def auth_client(async_session):
    """Factory to authenticate a TestClient as a given User via cookie token."""

    async def _auth(c: TestClient, user):
        token = await issue_access_token(async_session, user)
        c.cookies.set("access_token", token)
        return c

    return _auth


@pytest_asyncio.fixture(scope="function")
async def client_with_normal_user(client, async_session, auth_client):
    """Convenience fixture: client logged in as a normal user."""
    user = await get_or_create_user(
        async_session,
        email="user@example.com",
        password="normalpass",
        is_superuser=False,
    )
    return await auth_client(client, user)


@pytest_asyncio.fixture(scope="function")
async def client_with_superuser(client, async_session, auth_client):
    """Convenience fixture: client logged in as a superuser."""
    user = await get_or_create_user(
        async_session,
        email="admin@example.com",
        password="supersecret",
        is_superuser=True,
    )
    return await auth_client(client, user)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def superuser(async_session):
    # Ensure a superuser exists for each test function
    email = "admin@example.com"
    password = "supersecret"
    user = await get_or_create_user(
        async_session, email=email, password=password, is_superuser=True
    )
    return user


@pytest_asyncio.fixture(scope="function")
async def normal_user(async_session):
    # Ensure a normal user exists for tests
    user = await get_or_create_user(
        async_session,
        email="user@example.com",
        password="password123",
        is_superuser=False,
    )
    return user
