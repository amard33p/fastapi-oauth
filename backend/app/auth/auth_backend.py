from fastapi_users.authentication import AuthenticationBackend

from app.auth.auth_transport import oauth_cookie_transport
from app.auth.token_strategy import get_database_strategy

# OAuth cookie backend sets cookie and redirects back to SPA after OAuth login
cookie_oauth_auth_backend = AuthenticationBackend(
    name="cookie_oauth",
    transport=oauth_cookie_transport,
    get_strategy=get_database_strategy,
)
