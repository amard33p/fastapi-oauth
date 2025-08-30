from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import User, OAuthAccount, AccessToken
from .schemas import UserCreate, UserUpdate
from .auth.user_manager import UserManager
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.authentication.strategy.db import DatabaseStrategy
from fastapi_users_db_sqlalchemy.access_token import SQLAlchemyAccessTokenDatabase


async def get_or_create_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    is_superuser: bool = False,
) -> User:
    # Fetch existing user if present
    result = await session.execute(select(User).where(User.email == email))
    user = result.unique().scalar_one_or_none()
    if user is None:
        # Create via UserManager using our UserCreate schema
        user_db = SQLAlchemyUserDatabase(session, User, OAuthAccount)
        user_manager = UserManager(user_db)
        user_create = UserCreate(
            email=email,
            password=password,
            is_superuser=is_superuser,
            is_verified=True,
        )
        user = await user_manager.create(user_create, safe=True)
    return user


async def issue_access_token(session: AsyncSession, user: User) -> str:
    """Issue a DB-backed access token for the given user.

    Uses the same DatabaseStrategy as the application for consistency.
    """
    access_token_db = SQLAlchemyAccessTokenDatabase(session, AccessToken)
    strategy = DatabaseStrategy(database=access_token_db, lifetime_seconds=3600)
    token = await strategy.write_token(user)
    return token


async def update_user(
    session: AsyncSession,
    user: User,
    update: UserUpdate,
) -> User:
    # Apply updatable fields from the schema
    if update.email is not None:
        user.email = update.email

    await session.commit()
    await session.refresh(user)
    return user
