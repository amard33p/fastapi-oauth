import os
import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, models
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from httpx_oauth.clients.google import GoogleOAuth2

from .db import User, get_user_db

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


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy[models.UP, models.ID]:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


class OAuthCookieTransport(CookieTransport):
    async def get_login_response(self, token: str):  # type: ignore[override]
        # After successful OAuth, set HttpOnly cookie and redirect to SPA
        from fastapi.responses import RedirectResponse

        response = RedirectResponse(
            url=f"{FRONTEND_URL}/oauth-callback",
            status_code=302,
        )
        return self._set_login_cookie(response, token)


cookie_transport = CookieTransport(
    cookie_name="access_token",
    cookie_max_age=3600,
    cookie_secure=SECURE_COOKIES,
    cookie_httponly=True,
)

oauth_cookie_transport = OAuthCookieTransport(
    cookie_name="access_token",
    cookie_max_age=3600,
    cookie_secure=SECURE_COOKIES,
    cookie_httponly=True,
)

cookie_auth_backend = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

cookie_oauth_auth_backend = AuthenticationBackend(
    name="cookie_oauth",
    transport=oauth_cookie_transport,
    get_strategy=get_jwt_strategy,
)


fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend, cookie_auth_backend, cookie_oauth_auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)
