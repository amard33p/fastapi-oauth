import uuid

from fastapi_users import FastAPIUsers

from app.db import User
from app.auth.user_manager import get_user_manager
from app.auth.auth_backend import cookie_oauth_auth_backend, cookie_auth_backend


fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [cookie_oauth_auth_backend, cookie_auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)
