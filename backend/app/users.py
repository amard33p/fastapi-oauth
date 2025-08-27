import os
import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, models
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from httpx_oauth.clients.google import GoogleOAuth2

from .db import User, get_user_db

SECRET = "SECRET"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


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


class RedirectBearerTransport(BearerTransport):
    def __init__(self, redirect_url: str, tokenUrl: str = "auth/jwt/login"):
        super().__init__(tokenUrl=tokenUrl)
        self.redirect_url = redirect_url

    async def get_login_response(self, token: str):  # type: ignore[override]
        # Redirect back to the SPA with the token in query for POC purposes
        return RedirectResponse(
            url=f"{self.redirect_url}?access_token={token}", status_code=302
        )


oauth_redirect_transport = RedirectBearerTransport(
    redirect_url=f"{FRONTEND_URL}/oauth-callback",
    tokenUrl="auth/jwt/login",
)

oauth_redirect_auth_backend = AuthenticationBackend(
    name="jwt_oauth_redirect",
    transport=oauth_redirect_transport,
    get_strategy=get_jwt_strategy,
)


fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
