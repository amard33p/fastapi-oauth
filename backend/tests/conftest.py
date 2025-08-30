import pytest_asyncio
from fastapi.testclient import TestClient

from app.app import app as fastapi_app
from app.db import (
    AccessToken,
    engine,
    get_async_session as app_get_async_session,
)
from app.crud_user import get_or_create_user
from fastapi_users.authentication.strategy.db import DatabaseStrategy
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyAccessTokenDatabase
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
    """Authenticated TestClient that uses the same transactional async_session.

    - Overrides app's get_async_session to return our per-test session
    - Ensures a normal user exists and issues a DB-backed token
    - Sets the cookie expected by the app's CookieTransport
    """

    async def override():
        yield async_session

    fastapi_app.dependency_overrides[app_get_async_session] = override

    with TestClient(fastapi_app) as c:
        # Ensure a normal user exists in this session
        user = await get_or_create_user(
            async_session,
            email="user@example.com",
            password="password123",
            is_superuser=False,
        )
        # Issue token and set cookie
        access_token_db = SQLAlchemyAccessTokenDatabase(async_session, AccessToken)
        strategy = DatabaseStrategy(database=access_token_db, lifetime_seconds=3600)
        token = await strategy.write_token(user)
        c.cookies.set("access_token", token)

        yield c

    fastapi_app.dependency_overrides.pop(app_get_async_session, None)


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
