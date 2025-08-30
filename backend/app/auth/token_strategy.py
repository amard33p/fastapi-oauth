from fastapi import Depends
from fastapi_users.authentication.strategy.db import (
    AccessTokenDatabase,
    DatabaseStrategy,
)

from app.db import AccessToken, get_access_token_db


def get_database_strategy(
    access_token_db: AccessTokenDatabase[AccessToken] = Depends(get_access_token_db),
):
    """DB-backed token strategy used for cookie auth and OAuth flows.

    Tokens are persisted and invalidated on logout.
    """
    return DatabaseStrategy(database=access_token_db, lifetime_seconds=3600)
