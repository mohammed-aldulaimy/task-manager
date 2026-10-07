from datetime import date

import pytest

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
    process_order,
)
from utils.errors import NotFoundError, ValidationError


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
