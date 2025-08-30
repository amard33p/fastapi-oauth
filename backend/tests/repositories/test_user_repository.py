import uuid
import pytest

from app.crud_user import update_user
from app.schemas import UserUpdate


@pytest.mark.asyncio
async def test_update_user_success(async_session, normal_user):
    new_email = f"new-{uuid.uuid4().hex[:8]}@example.com"

    updated_user = await update_user(
        async_session,
        normal_user,
        UserUpdate(email=new_email),
    )

    assert updated_user.email == new_email
