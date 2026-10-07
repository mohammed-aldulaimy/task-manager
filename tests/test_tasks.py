from datetime import date

import pytest

from app import app
from services.tasks import (
    PRIORITY_DEFAULT,
    PRIORITY_MAX,
    PRIORITY_MIN,
    TASKS,
    _validate_priority,
    create_task,
    get_overdue_tasks,
    get_task,
    get_tasks_for_user,
    list_tasks,
    process_order,
    update_task,
)
from utils.errors import NotFoundError, ValidationError


@pytest.fixture(autouse=True)
def restore_tasks():
    snapshot = {task_id: dict(task) for task_id, task in TASKS.items()}
    yield
    TASKS.clear()
    TASKS.update(snapshot)

@pytest.fixture
def client():
    return app.test_client()

def test_process_order_valid():
    result = process_order(1)
    assert result["done"] is True

def test_process_order_invalid():
    with pytest.raises(NotFoundError):
        process_order(999)

def test_get_task_valid():
    result = get_task(2)
    assert result["title"] == "Write report"

def test_get_task_invalid():
    with pytest.raises(NotFoundError):
        get_task(999)

def test_get_task_not_found_raises_not_found_error():
    with pytest.raises(NotFoundError) as exc_info:
        get_task(999)
    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "Task not found"

def test_create_task_valid():
    result = create_task("Plan trip", 2)
    assert result["title"] == "Plan trip"
    assert result["user_id"] == 2
    assert result["done"] is False
    assert get_task(result["id"]) == result

def test_create_task_empty_title_raises_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        create_task("   ", 1)
    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Invalid title: cannot be empty"

def test_create_task_unknown_user_raises_not_found_error():
    with pytest.raises(NotFoundError) as exc_info:
        create_task("Orphan task", 999)
    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "User not found"

def test_get_tasks_for_user_valid():
    result = get_tasks_for_user(1)
    assert [task["id"] for task in result] == [1, 2]
    assert all(task["user_id"] == 1 for task in result)

def test_get_tasks_for_user_unknown_user_raises_not_found_error():
    with pytest.raises(NotFoundError) as exc_info:
        get_tasks_for_user(999)
    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "User not found"

TODAY = date(2026, 10, 6)

def test_create_task_with_due_date():
    result = create_task("Pay rent", 1, "2026-11-01")
    assert result["due_date"] == "2026-11-01"
    assert result["status"] == "todo"
    assert result["done"] is False

def test_create_task_without_due_date_defaults_to_none():
    result = create_task("Someday", 1)
    assert result["due_date"] is None
    assert result["status"] == "todo"

def test_create_task_invalid_due_date_raises_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        create_task("Bad date", 1, "not-a-date")
    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Invalid due_date: must be an ISO-8601 date (YYYY-MM-DD)"

def test_process_order_sets_status_done():
    task = create_task("Finish me", 2)
    result = process_order(task["id"])
    assert result["status"] == "done"
    assert result["done"] is True

def test_get_overdue_tasks_includes_past_due_not_done():
    task = create_task("Late", 1, "2026-10-01")
    overdue_ids = [t["id"] for t in get_overdue_tasks(today=TODAY)]
    assert task["id"] in overdue_ids

def test_get_overdue_tasks_excludes_future_undated_done_and_today():
    future = create_task("Future", 1, "2026-12-01")
    undated = create_task("Undated", 1)
    due_today = create_task("Due today", 1, "2026-10-06")
    finished = create_task("Finished", 1, "2026-09-01")
    process_order(finished["id"])
    overdue_ids = [t["id"] for t in get_overdue_tasks(today=TODAY)]
    for task in (future, undated, due_today, finished):
        assert task["id"] not in overdue_ids

# Priority

PRIORITY_RANGE_MESSAGE = "Invalid priority: must be an integer between 1 and 5"

def test_seed_tasks_have_priority():
    for task in TASKS.values():
        assert isinstance(task["priority"], int)
        assert PRIORITY_MIN <= task["priority"] <= PRIORITY_MAX

@pytest.mark.parametrize("priority", [1, 2, 3, 4, 5])
def test_validate_priority_valid_passes(priority):
    assert _validate_priority(priority) is None

def test_create_task_without_priority_defaults_to_3():
    result = create_task("Default priority", 1)
    assert PRIORITY_DEFAULT == 3
    assert result["priority"] == 3

@pytest.mark.parametrize("priority", [PRIORITY_MIN, PRIORITY_MAX], ids=["urgent", "low"])
def test_create_task_with_priority(priority):
    result = create_task("Prioritized", 1, priority=priority)
    assert result["priority"] == priority
    assert get_task(result["id"])["priority"] == priority

@pytest.mark.parametrize(
    "bad_priority",
    [0, 6, -1, "3", 2.5, True],
    ids=["zero", "six", "negative", "string", "float", "bool"],
)
def test_create_task_invalid_priority_raises_validation_error(bad_priority):
    with pytest.raises(ValidationError) as exc_info:
        create_task("Bad priority", 1, priority=bad_priority)
    assert exc_info.value.status_code == 422
    assert exc_info.value.message == PRIORITY_RANGE_MESSAGE

def test_create_task_none_priority_raises_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        create_task("No priority", 1, priority=None)
    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "Invalid priority: cannot be empty"

def test_create_task_invalid_priority_checked_before_user():
    with pytest.raises(ValidationError) as exc_info:
        create_task("Orphan", 999, priority=0)
    assert exc_info.value.message == PRIORITY_RANGE_MESSAGE

# update_task

DUE_DATE_MESSAGE = "Invalid due_date: must be an ISO-8601 date (YYYY-MM-DD)"

def test_update_task_priority():
    result = update_task(2, priority=1)
    assert result["priority"] == 1
    assert get_task(2)["priority"] == 1
    assert result["title"] == "Write report"
    assert result["due_date"] == "2099-12-31"

def test_update_task_title_and_due_date():
    result = update_task(2, title="Write summary", due_date="2027-01-01")
    assert result["title"] == "Write summary"
    assert result["due_date"] == "2027-01-01"
    assert result["priority"] == 2

def test_update_task_no_fields_returns_unchanged():
    before = dict(get_task(2))
    assert update_task(2) == before

def test_update_task_clears_due_date():
    result = update_task(2, due_date=None)
    assert result["due_date"] is None
    assert get_task(2)["due_date"] is None

@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("title", "", "Invalid title: cannot be empty"),
        ("title", None, "Invalid title: cannot be empty"),
        ("priority", None, "Invalid priority: cannot be empty"),
        ("priority", 0, PRIORITY_RANGE_MESSAGE),
        ("priority", 6, PRIORITY_RANGE_MESSAGE),
        ("priority", "3", PRIORITY_RANGE_MESSAGE),
        ("priority", True, PRIORITY_RANGE_MESSAGE),
        ("due_date", "nope", DUE_DATE_MESSAGE),
    ],
    ids=[
        "empty_title", "none_title", "none_priority", "zero_priority",
        "six_priority", "string_priority", "bool_priority", "bad_due_date",
    ],
)
def test_update_task_invalid_field_raises_validation_error(field, value, message):
    before = dict(get_task(2))
    with pytest.raises(ValidationError) as exc_info:
        update_task(2, **{field: value})
    assert exc_info.value.status_code == 422
    assert exc_info.value.message == message
    assert get_task(2) == before

def test_update_task_unknown_task_raises_not_found_error():
    with pytest.raises(NotFoundError) as exc_info:
        update_task(999, priority=1)
    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "Task not found"

def test_update_task_invalid_field_checked_before_task():
    with pytest.raises(ValidationError) as exc_info:
        update_task(999, priority=0)
    assert exc_info.value.message == PRIORITY_RANGE_MESSAGE

# list_tasks priority filter

def test_list_tasks_filters_by_priority():
    assert [task["id"] for task in list_tasks(priority=3)] == [1, 3]

def test_list_tasks_priority_and_tag_combined():
    assert [task["id"] for task in list_tasks("errand", priority=3)] == [1]
    assert list_tasks("work", priority=3) == []

def test_list_tasks_priority_no_match_returns_empty():
    assert list_tasks(priority=5) == []

def test_list_tasks_reflects_updated_priority():
    update_task(2, priority=3)
    assert [task["id"] for task in list_tasks(priority=3)] == [1, 2, 3]

@pytest.mark.parametrize(
    "bad_priority",
    [0, 6, "3", True],
    ids=["zero", "six", "string", "bool"],
)
def test_list_tasks_invalid_priority_raises_validation_error(bad_priority):
    with pytest.raises(ValidationError) as exc_info:
        list_tasks(priority=bad_priority)
    assert exc_info.value.status_code == 422
    assert exc_info.value.message == PRIORITY_RANGE_MESSAGE

# API

def test_api_create_task_default_priority(client):
    response = client.post("/api/tasks", json={"title": "x", "user_id": 1})
    assert response.status_code == 201
    assert response.get_json()["priority"] == 3

def test_api_create_task_with_priority(client):
    response = client.post("/api/tasks", json={"title": "x", "user_id": 1, "priority": 5})
    assert response.status_code == 201
    task = response.get_json()
    assert task["priority"] == 5
    assert client.get(f"/api/tasks/{task['id']}").get_json()["priority"] == 5

@pytest.mark.parametrize(
    ("bad_priority", "message"),
    [
        (0, PRIORITY_RANGE_MESSAGE),
        ("3", PRIORITY_RANGE_MESSAGE),
        (None, "Invalid priority: cannot be empty"),
    ],
    ids=["zero", "string", "null"],
)
def test_api_create_task_invalid_priority(client, bad_priority, message):
    response = client.post(
        "/api/tasks", json={"title": "x", "user_id": 1, "priority": bad_priority}
    )
    assert response.status_code == 422
    assert response.get_json() == {"error": message}

def test_api_create_task_empty_body(client):
    response = client.post("/api/tasks")
    assert response.status_code == 422
    assert response.get_json() == {"error": "Invalid title: cannot be empty"}

def test_api_create_task_unknown_user(client):
    response = client.post("/api/tasks", json={"title": "x", "user_id": 999})
    assert response.status_code == 404
    assert response.get_json() == {"error": "User not found"}

def test_api_update_task_priority(client):
    response = client.patch("/api/tasks/2", json={"priority": 1})
    assert response.status_code == 200
    task = response.get_json()
    assert task["priority"] == 1
    assert task["title"] == "Write report"
    assert task["due_date"] == "2099-12-31"

def test_api_update_task_null_due_date_clears(client):
    response = client.patch("/api/tasks/2", json={"due_date": None})
    assert response.status_code == 200
    assert response.get_json()["due_date"] is None

@pytest.mark.parametrize("kwargs", [{"json": {}}, {}], ids=["empty_json", "no_body"])
def test_api_update_task_no_fields_unchanged(client, kwargs):
    before = dict(get_task(2))
    response = client.patch("/api/tasks/2", **kwargs)
    assert response.status_code == 200
    assert response.get_json() == before

@pytest.mark.parametrize(
    ("body", "message"),
    [
        ({"title": ""}, "Invalid title: cannot be empty"),
        ({"priority": None}, "Invalid priority: cannot be empty"),
    ],
    ids=["empty_title", "null_priority"],
)
def test_api_update_task_invalid_field(client, body, message):
    before = dict(get_task(2))
    response = client.patch("/api/tasks/2", json=body)
    assert response.status_code == 422
    assert response.get_json() == {"error": message}
    assert get_task(2) == before

def test_api_update_task_unknown_task(client):
    response = client.patch("/api/tasks/999", json={"priority": 1})
    assert response.status_code == 404
    assert response.get_json() == {"error": "Task not found"}

def test_api_list_tasks_filtered_by_priority(client):
    response = client.get("/api/tasks?priority=3")
    assert response.status_code == 200
    assert [task["id"] for task in response.get_json()] == [1, 3]

def test_api_list_tasks_filtered_by_priority_and_tag(client):
    response = client.get("/api/tasks?priority=3&tag=errand")
    assert response.status_code == 200
    assert [task["id"] for task in response.get_json()] == [1]

def test_api_list_tasks_priority_no_match(client):
    response = client.get("/api/tasks?priority=5")
    assert response.status_code == 200
    assert response.get_json() == []

def test_api_get_task_includes_priority(client):
    response = client.get("/api/tasks/1")
    assert response.status_code == 200
    assert response.get_json()["priority"] == 3

@pytest.mark.parametrize(
    "query",
    ["abc", "", "9", "-1", "²"],
    ids=["letters", "empty", "out_of_range", "negative", "superscript"],
)
def test_api_list_tasks_invalid_priority(client, query):
    response = client.get("/api/tasks", query_string={"priority": query})
    assert response.status_code == 422
    assert "error" in response.get_json()
