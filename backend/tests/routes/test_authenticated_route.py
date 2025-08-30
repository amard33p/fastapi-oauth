import pytest
from app.crud_user import get_or_create_user


def test_authenticated_route_e2e(client_with_normal_user):
    r = client_with_normal_user.get("/authenticated-route")

    assert r.status_code == 200
    assert r.json() == {"message": "Hello user@example.com!"}


@pytest.mark.asyncio
async def test_authenticated_route_with_created_user(
    client, async_session, auth_client
):
    # Create a user directly in the DB, then authenticate the base client as that user

    email = "created_user@example.com"
    password = "createdpass"

    user = await get_or_create_user(
        async_session,
        email=email,
        password=password,
        is_superuser=False,
    )

    authed_client = await auth_client(client, user)

    r = authed_client.get("/authenticated-route")
    assert r.status_code == 200
    assert r.json() == {"message": f"Hello {email}!"}
