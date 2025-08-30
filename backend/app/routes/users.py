from fastapi import APIRouter

from app.schemas import UserRead, UserUpdate
from app.auth.user_setup import fastapi_users

router = APIRouter(prefix="/users", tags=["users"])

router.include_router(fastapi_users.get_users_router(UserRead, UserUpdate))
