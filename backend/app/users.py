import os
import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, models
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from httpx_oauth.clients.google import GoogleOAuth2
from fastapi_users.authentication.strategy.db import (
    AccessTokenDatabase,
    DatabaseStrategy,
)

from .db import User, get_user_db, AccessToken, get_access_token_db

SECRET = "SECRET"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
# Set to true in production
SECURE_COOKIES = os.getenv("SECURE_COOKIES", "false").lower() in {"1", "true", "yes"}


google_oauth_client = GoogleOAuth2(
    os.getenv("GOOGLE_CLIENT_ID", ""),
    os.getenv("GOOGLE_CLIENT_SECRET", ""),
)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


def get_database_strategy(
    access_token_db: AccessTokenDatabase[AccessToken] = Depends(get_access_token_db),
):
    # Tokens are persisted in DB and invalidated on logout
    return DatabaseStrategy(database=access_token_db, lifetime_seconds=3600)


class OAuthCookieTransport(CookieTransport):
    async def get_login_response(self, token: str):  # type: ignore[override]
        # After successful OAuth, set HttpOnly cookie and redirect to SPA
        from fastapi.responses import RedirectResponse

        response = RedirectResponse(
            url=f"{FRONTEND_URL}/oauth-callback",
            status_code=302,
        )
        return self._set_login_cookie(response, token)


oauth_cookie_transport = OAuthCookieTransport(
    cookie_name="access_token",
    cookie_max_age=3600,
    cookie_secure=SECURE_COOKIES,
    cookie_httponly=True,
)

cookie_oauth_auth_backend = AuthenticationBackend(
    name="cookie_oauth",
    transport=oauth_cookie_transport,
    get_strategy=get_database_strategy,
)


fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [cookie_oauth_auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)
