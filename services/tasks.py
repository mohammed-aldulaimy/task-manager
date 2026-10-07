from datetime import date, datetime
from enum import Enum

from services.users import get_user
from utils.errors import NotFoundError, ValidationError

TASK_STATUSES = ("todo", "in_progress", "done")

PRIORITY_MIN = 1
PRIORITY_MAX = 5
PRIORITY_DEFAULT = 3

class _Unset(Enum):
    """Marker type for an update_task field that was not provided."""
    UNSET = "UNSET"

_UNSET = _Unset.UNSET

TASKS: dict[int, dict] = {
    1: {"id": 1, "title": "Buy groceries", "done": False, "status": "todo",
        "due_date": "2026-01-15", "user_id": 1, "priority": 3},
    2: {"id": 2, "title": "Write report",  "done": False, "status": "todo",
        "due_date": "2099-12-31", "user_id": 1, "priority": 2},
    3: {"id": 3, "title": "Call dentist",  "done": True,  "status": "done",
        "due_date": "2026-01-01", "user_id": 2, "priority": 3},
}

def process_order(task_id: int) -> dict:
    """Mark a task as done.

    Args:
        task_id: The unique identifier for the task.

    Returns:
        The updated task record as a dictionary.

    Raises:
        NotFoundError: If no task exists with the given ID.
    """
    if task_id not in TASKS:
        raise NotFoundError("Task")
    task = TASKS[task_id]
    task["done"] = True
    task["status"] = "done"
    return task

def get_task(task_id: int) -> dict:
    """Retrieve a task by ID.

    Args:
        task_id: The unique identifier for the task.

    Returns:
        The task record as a dictionary.

    Raises:
        NotFoundError: If no task exists with the given ID.
    """
    if task_id not in TASKS:
        raise NotFoundError("Task")
    return TASKS[task_id]

def _validate_title(title: str) -> None:
    """Validate a task title.

    Args:
        title: The task's title. Must be a string with at least one
            non-whitespace character.

    Returns:
        None.

    Raises:
        ValidationError: If title is None, not a string, or blank.
    """
    if not isinstance(title, str) or not title.strip():
        raise ValidationError("title", "cannot be empty")

def _validate_due_date(due_date: str | None) -> None:
    """Validate an optional ISO-8601 due date.

    Args:
        due_date: A date string in YYYY-MM-DD format, or None.

    Returns:
        None.

    Raises:
        ValidationError: If due_date is not None and not a valid ISO-8601 date.
    """
    if due_date is None:
        return
    if not isinstance(due_date, str):
        raise ValidationError("due_date", "must be an ISO-8601 date (YYYY-MM-DD)")
    try:
        date.fromisoformat(due_date)
    except ValueError:
        raise ValidationError("due_date", "must be an ISO-8601 date (YYYY-MM-DD)") from None

def _validate_priority(priority: int) -> None:
    """Validate a task priority.

    Args:
        priority: An integer from PRIORITY_MIN (urgent) to PRIORITY_MAX (low).

    Returns:
        None.

    Raises:
        ValidationError: If priority is None, not an integer (bools and
            numeric strings are rejected), or outside PRIORITY_MIN..PRIORITY_MAX.
    """
    if priority is None:
        raise ValidationError("priority", "cannot be empty")
    if (
        not isinstance(priority, int)
        or isinstance(priority, bool)
        or not PRIORITY_MIN <= priority <= PRIORITY_MAX
    ):
        raise ValidationError(
            "priority", f"must be an integer between {PRIORITY_MIN} and {PRIORITY_MAX}"
        )

def create_task(
    title: str,
    user_id: int,
    due_date: str | None = None,
    priority: int = PRIORITY_DEFAULT,
) -> dict:
    """Create a new task.

    Args:
        title: The task's title.
        user_id: The ID of the user who owns the task.
        due_date: Optional ISO-8601 due date (YYYY-MM-DD), or None.
        priority: Integer from 1 (urgent) to 5 (low); defaults to 3.

    Returns:
        The newly created task record.

    Raises:
        ValidationError: If title is empty, due_date is not a valid ISO-8601
            date, or priority is not an integer from 1 to 5.
        NotFoundError: If no user exists with the given user_id.
    """
    _validate_title(title)
    _validate_due_date(due_date)
    _validate_priority(priority)
    get_user(user_id)
    new_id = max(TASKS.keys()) + 1
    TASKS[new_id] = {
        "id": new_id,
        "title": title,
        "done": False,
        "status": "todo",
        "due_date": due_date,
        "user_id": user_id,
        "priority": priority,
    }
    return TASKS[new_id]

def update_task(
    task_id: int,
    title: str | _Unset = _UNSET,
    due_date: str | None | _Unset = _UNSET,
    priority: int | _Unset = _UNSET,
) -> dict:
    """Update a task's title, due date, and/or priority.

    A field that is omitted is not changed. All provided fields are
    validated before any is applied, so an invalid field leaves the task
    unchanged. Passing no fields returns the task as-is.

    Args:
        task_id: The unique identifier for the task.
        title: The new title; omit to keep the current one.
        due_date: The new ISO-8601 due date (YYYY-MM-DD), or None to remove
            the due date; omit to keep the current one.
        priority: The new priority from 1 (urgent) to 5 (low); omit to keep
            the current one.

    Returns:
        The updated task record.

    Raises:
        ValidationError: If title is None or empty, due_date is not None and
            not a valid ISO-8601 date, or priority is None or not an integer
            from 1 to 5.
        NotFoundError: If no task exists with the given ID.
    """
    if title is not _UNSET:
        _validate_title(title)
    if due_date is not _UNSET:
        _validate_due_date(due_date)
    if priority is not _UNSET:
        _validate_priority(priority)
    task = get_task(task_id)
    if title is not _UNSET:
        task["title"] = title
    if due_date is not _UNSET:
        task["due_date"] = due_date
    if priority is not _UNSET:
        task["priority"] = priority
    return task

def get_tasks_for_user(user_id: int) -> list[dict]:
    """Retrieve all tasks owned by a user.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        A list of task records belonging to the user, empty if they have none.

    Raises:
        NotFoundError: If no user exists with the given ID.
    """
    get_user(user_id)
    return [task for task in TASKS.values() if task["user_id"] == user_id]

def get_overdue_tasks(today: date | None = None) -> list[dict]:
    """Retrieve all tasks that are past their due date and not done.

    Args:
        today: The reference date; defaults to the current local date.

    Returns:
        A list of task records whose due_date is before today and whose
        status is not "done", empty if there are none.

    Raises:
        None.
    """
    today = today or datetime.now().astimezone().date()
    return [
        task for task in TASKS.values()
        if task["due_date"] is not None
        and date.fromisoformat(task["due_date"]) < today
        and task["status"] != "done"
    ]

def list_tasks(tag: str | None = None, priority: int | None = None) -> list[dict]:
    """Retrieve all tasks, optionally filtered by tag and/or priority.

    When both filters are given, a task must match both.

    Args:
        tag: If given, only tasks carrying this tag are returned.
        priority: If given, only tasks with this priority are returned.

    Returns:
        A list of task records, empty if no task matches the filters.

    Raises:
        ValidationError: If tag is not None and not a valid tag name, or
            priority is not None and not an integer from 1 to 5.
    """
    from services.tags import TASK_TAGS, _validate_tag

    if tag is not None:
        _validate_tag(tag)
    if priority is not None:
        _validate_priority(priority)
    tasks = list(TASKS.values())
    if tag is not None:
        tagged_ids = {task_id for task_id, t in TASK_TAGS if t == tag}
        tasks = [task for task in tasks if task["id"] in tagged_ids]
    if priority is not None:
        tasks = [task for task in tasks if task["priority"] == priority]
    return tasks
