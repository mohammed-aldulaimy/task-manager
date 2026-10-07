import pytest

from app import app
from services.tags import (
    TAG_MAX_LEN,
    TASK_TAGS,
    _validate_tag,
    add_tag,
    get_tags_for_task,
    remove_tag,
)
from services.tasks import TASKS, list_tasks
from utils.errors import NotFoundError, ValidationError


@pytest.fixture(autouse=True)
def restore_task_tags():
    snapshot = set(TASK_TAGS)
    yield
    TASK_TAGS.clear()
    TASK_TAGS.update(snapshot)

@pytest.fixture
def client():
    return app.test_client()

# Validator

@pytest.mark.parametrize(
    "bad_tag",
    ["Work", "", "   ", None, "a" * (TAG_MAX_LEN + 1), "two words"],
    ids=["uppercase", "empty", "whitespace", "none", "too_long", "space"],
)
def test_validate_tag_invalid_raises_validation_error(bad_tag):
    with pytest.raises(ValidationError) as exc_info:
        _validate_tag(bad_tag)
    assert exc_info.value.status_code == 422

def test_validate_tag_empty_message():
    with pytest.raises(ValidationError) as exc_info:
        _validate_tag("")
    assert exc_info.value.message == "Invalid tag: cannot be empty"

def test_validate_tag_max_length_passes():
    assert TAG_MAX_LEN == 32
    assert _validate_tag("a" * 32) is None

def test_validate_tag_allowed_characters_pass():
    assert _validate_tag("x_y-1") is None

# Service

def test_add_tag_new():
    result = add_tag(1, "home")
    assert result == ["errand", "home"]
    assert (1, "home") in TASK_TAGS

def test_add_tag_duplicate_is_noop():
    before = set(TASK_TAGS)
    result = add_tag(2, "work")
    assert result == ["work"]
    assert TASK_TAGS == before

def test_add_tag_invalid_raises_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        add_tag(1, "Bad Tag")
    assert exc_info.value.status_code == 422

def test_remove_tag_valid():
    result = remove_tag(2, "work")
    assert result == []
    assert (2, "work") not in TASK_TAGS

def test_remove_tag_missing_raises_not_found_error():
    with pytest.raises(NotFoundError) as exc_info:
        remove_tag(1, "work")
    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "Tag not found"

def test_add_tag_unknown_task_raises_not_found_error():
    with pytest.raises(NotFoundError) as exc_info:
        add_tag(999, "work")
    assert exc_info.value.message == "Task not found"

def test_remove_tag_unknown_task_raises_not_found_error():
    with pytest.raises(NotFoundError) as exc_info:
        remove_tag(999, "work")
    assert exc_info.value.message == "Task not found"

def test_get_tags_for_task_unknown_task_raises_not_found_error():
    with pytest.raises(NotFoundError) as exc_info:
        get_tags_for_task(999)
    assert exc_info.value.message == "Task not found"

def test_get_tags_for_task_sorted():
    add_tag(1, "zeta")
    add_tag(1, "alpha")
    assert get_tags_for_task(1) == ["alpha", "errand", "zeta"]

def test_list_tasks_no_tag_returns_all():
    result = list_tasks()
    assert [task["id"] for task in result] == list(TASKS.keys())

def test_list_tasks_filters_by_tag():
    result = list_tasks("work")
    assert [task["id"] for task in result] == [2]

def test_list_tasks_unknown_tag_returns_empty():
    assert list_tasks("nosuch") == []

def test_list_tasks_invalid_tag_raises_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        list_tasks("Bad Tag")
    assert exc_info.value.status_code == 422

# API

def test_api_add_tag(client):
    response = client.post("/api/tasks/1/tags", json={"tag": "home"})
    assert response.status_code == 201
    assert response.get_json() == {"task_id": 1, "tags": ["errand", "home"]}

def test_api_add_tag_invalid(client):
    response = client.post("/api/tasks/1/tags", json={"tag": "Bad Tag"})
    assert response.status_code == 422
    assert "error" in response.get_json()

def test_api_add_tag_empty_body(client):
    response = client.post("/api/tasks/1/tags")
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid tag: cannot be empty"}

def test_api_add_tag_unknown_task(client):
    response = client.post("/api/tasks/999/tags", json={"tag": "work"})
    assert response.status_code == 404
    assert response.get_json() == {"error": "Task not found"}

def test_api_remove_tag(client):
    response = client.delete("/api/tasks/2/tags/work")
    assert response.status_code == 200
    assert response.get_json() == {"task_id": 2, "tags": []}

def test_api_remove_missing_tag(client):
    response = client.delete("/api/tasks/1/tags/work")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Tag not found"}

def test_api_list_tasks(client):
    response = client.get("/api/tasks")
    assert response.status_code == 200
    assert [task["id"] for task in response.get_json()] == list(TASKS.keys())

def test_api_list_tasks_filtered_by_tag(client):
    response = client.get("/api/tasks?tag=work")
    assert response.status_code == 200
    assert [task["id"] for task in response.get_json()] == [2]
