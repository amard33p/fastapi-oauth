from fastapi import APIRouter, Depends

from app.db import User
from app.auth.user_setup import current_active_user
from .auth import router as auth_router
from .users import router as users_router

router = APIRouter()

# Mount sub-routers
router.include_router(auth_router)
router.include_router(users_router)


@router.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}
