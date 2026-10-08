import pytest

from app import app
from services.users import (
    NOTIFICATION_PREF_DEFAULT,
    NOTIFICATION_PREFS,
    USERS,
    create_user,
    get_notification_pref,
    get_user,
    list_users,
    update_notification_pref,
)
from utils.errors import NotFoundError, ValidationError

PREF_CHOICES_MESSAGE = "Invalid notification_pref: must be one of: email, sms, none"
PREF_EMPTY_MESSAGE = "Invalid notification_pref: cannot be empty"


@pytest.fixture(autouse=True)
def restore_users():
    snapshot = {user_id: dict(user) for user_id, user in USERS.items()}
    yield
    USERS.clear()
    USERS.update(snapshot)

@pytest.fixture
def client():
    return app.test_client()

def test_notification_pref_default_is_none():
    assert NOTIFICATION_PREF_DEFAULT == "none"
    assert NOTIFICATION_PREFS == ("email", "sms", "none")

@pytest.mark.parametrize("user_id", [1, 2])
def test_seed_users_default_notification_pref(user_id):
    assert get_user(user_id)["notification_pref"] == NOTIFICATION_PREF_DEFAULT

def test_create_user_default_notification_pref():
    user = create_user("Carol", "carol@example.com")
    assert user["notification_pref"] == NOTIFICATION_PREF_DEFAULT
    assert get_user(user["id"])["notification_pref"] == NOTIFICATION_PREF_DEFAULT

@pytest.mark.parametrize("pref", NOTIFICATION_PREFS)
def test_update_notification_pref_valid(pref):
    user = update_notification_pref(1, pref)
    assert user["id"] == 1
    assert user["notification_pref"] == pref
    assert get_notification_pref(1) == pref

def test_update_notification_pref_returns_full_record():
    user = update_notification_pref(2, "email")
    assert user == {
        "id": 2,
        "name": "Bob",
        "email": "bob@example.com",
        "notification_pref": "email",
    }

@pytest.mark.parametrize(
    ("bad_pref", "message"),
    [
        (None, PREF_EMPTY_MESSAGE),
        ("", PREF_CHOICES_MESSAGE),
        ("Email", PREF_CHOICES_MESSAGE),
        (" sms", PREF_CHOICES_MESSAGE),
        ("push", PREF_CHOICES_MESSAGE),
        (1, PREF_CHOICES_MESSAGE),
        (True, PREF_CHOICES_MESSAGE),
    ],
    ids=["none", "empty", "capitalized", "whitespace", "unknown", "int", "bool"],
)
def test_update_notification_pref_invalid(bad_pref, message):
    before = {user_id: dict(user) for user_id, user in USERS.items()}
    with pytest.raises(ValidationError) as exc_info:
        update_notification_pref(1, bad_pref)
    assert exc_info.value.status_code == 422
    assert exc_info.value.message == message
    assert USERS == before

def test_update_notification_pref_unknown_user():
    before = {user_id: dict(user) for user_id, user in USERS.items()}
    with pytest.raises(NotFoundError) as exc_info:
        update_notification_pref(999, "email")
    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "User not found"
    assert USERS == before

def test_update_notification_pref_validates_before_lookup():
    with pytest.raises(ValidationError):
        update_notification_pref(999, "push")

def test_get_notification_pref():
    assert get_notification_pref(1) == NOTIFICATION_PREF_DEFAULT

def test_get_notification_pref_unknown_user():
    with pytest.raises(NotFoundError):
        get_notification_pref(999)

def test_list_users_includes_notification_pref():
    users = list_users()
    assert [user["id"] for user in users] == [1, 2]
    assert all(user["notification_pref"] == NOTIFICATION_PREF_DEFAULT for user in users)

def test_list_users_empty():
    USERS.clear()
    assert list_users() == []

def test_api_list_users(client):
    response = client.get("/api/users")
    assert response.status_code == 200
    users = response.get_json()
    assert [user["id"] for user in users] == [1, 2]
    assert all("notification_pref" in user for user in users)

def test_api_get_user_includes_notification_pref(client):
    response = client.get("/api/users/1")
    assert response.status_code == 200
    assert response.get_json()["notification_pref"] == NOTIFICATION_PREF_DEFAULT

def test_api_get_notification_pref(client):
    response = client.get("/api/users/1/notifications")
    assert response.status_code == 200
    assert response.get_json() == {"user_id": 1, "notification_pref": "none"}

def test_api_get_notification_pref_unknown_user(client):
    response = client.get("/api/users/999/notifications")
    assert response.status_code == 404
    assert response.get_json() == {"error": "User not found"}

@pytest.mark.parametrize("pref", NOTIFICATION_PREFS)
def test_api_update_notification_pref(client, pref):
    response = client.patch("/api/users/1/notifications", json={"notification_pref": pref})
    assert response.status_code == 200
    assert response.get_json() == {"user_id": 1, "notification_pref": pref}
    assert client.get("/api/users/1/notifications").get_json()["notification_pref"] == pref

@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"json": {"notification_pref": "push"}}, PREF_CHOICES_MESSAGE),
        ({"json": {"notification_pref": "Email"}}, PREF_CHOICES_MESSAGE),
        ({"json": {"notification_pref": None}}, PREF_EMPTY_MESSAGE),
        ({"json": {}}, PREF_EMPTY_MESSAGE),
        ({}, PREF_EMPTY_MESSAGE),
    ],
    ids=["unknown", "capitalized", "null", "empty_json", "no_body"],
)
def test_api_update_notification_pref_invalid(client, kwargs, message):
    before = dict(get_user(1))
    response = client.patch("/api/users/1/notifications", **kwargs)
    assert response.status_code == 422
    assert response.get_json() == {"error": message}
    assert get_user(1) == before

def test_api_update_notification_pref_unknown_user(client):
    response = client.patch("/api/users/999/notifications", json={"notification_pref": "sms"})
    assert response.status_code == 404
    assert response.get_json() == {"error": "User not found"}
