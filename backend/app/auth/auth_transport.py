from fastapi_users.authentication import CookieTransport

from app.config import settings


class OAuthCookieTransport(CookieTransport):
    async def get_login_response(self, token: str):  # type: ignore[override]
        # After successful OAuth, set HttpOnly cookie and redirect to SPA
        from fastapi.responses import RedirectResponse

        response = RedirectResponse(
            url=f"{settings.FRONTEND_URL}/oauth-callback",
            status_code=302,
        )
        return self._set_login_cookie(response, token)


oauth_cookie_transport = OAuthCookieTransport(
    cookie_name="access_token",
    cookie_max_age=settings.COOKIE_MAX_AGE,
    cookie_secure=settings.SECURE_COOKIES,
    cookie_httponly=True,
)

# Non-redirecting transport for classic username/password cookie login
cookie_transport = CookieTransport(
    cookie_name="access_token",
    cookie_max_age=settings.COOKIE_MAX_AGE,
    cookie_secure=settings.SECURE_COOKIES,
    cookie_httponly=True,
)
