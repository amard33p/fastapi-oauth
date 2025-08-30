from fastapi import APIRouter

from app.auth.auth_backend import cookie_oauth_auth_backend
from app.auth.user_setup import fastapi_users
from app.auth.oauth_client import google_oauth_client
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# Cookie-based login/logout endpoints under /auth/cookie
router.include_router(
    fastapi_users.get_auth_router(cookie_oauth_auth_backend),
    prefix="/cookie",
)


# OAuth2: Google flow under /auth/google
router.include_router(
    fastapi_users.get_oauth_router(
        google_oauth_client,
        cookie_oauth_auth_backend,
        settings.SECRET,
    ),
    prefix="/google",
)
