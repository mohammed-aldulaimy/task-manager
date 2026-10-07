import pytest

from services.tasks import create_task, get_task, get_tasks_for_user, process_order
from utils.errors import NotFoundError, ValidationError


def test_process_order_valid():
    result = process_order(1)
    assert result["done"] is True

def test_process_order_invalid():
    with pytest.raises(Exception):
        process_order(999)

def test_get_task_valid():
    result = get_task(2)
    assert result["title"] == "Write report"

def test_get_task_invalid():
    with pytest.raises(Exception):
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
