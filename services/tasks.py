from datetime import date, datetime

from services.users import get_user
from utils.errors import NotFoundError, ValidationError

TASK_STATUSES = ("todo", "in_progress", "done")

TASKS: dict[int, dict] = {
    1: {"id": 1, "title": "Buy groceries", "done": False, "status": "todo",
        "due_date": "2026-01-15", "user_id": 1},
    2: {"id": 2, "title": "Write report",  "done": False, "status": "todo",
        "due_date": "2099-12-31", "user_id": 1},
    3: {"id": 3, "title": "Call dentist",  "done": True,  "status": "done",
        "due_date": "2026-01-01", "user_id": 2},
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

def create_task(title: str, user_id: int, due_date: str | None = None) -> dict:
    """Create a new task.

    Args:
        title: The task's title.
        user_id: The ID of the user who owns the task.
        due_date: Optional ISO-8601 due date (YYYY-MM-DD), or None.

    Returns:
        The newly created task record.

    Raises:
        ValidationError: If title is empty or due_date is not a valid ISO-8601 date.
        NotFoundError: If no user exists with the given user_id.
    """
    if not title or not title.strip():
        raise ValidationError("title", "cannot be empty")
    _validate_due_date(due_date)
    get_user(user_id)
    new_id = max(TASKS.keys()) + 1
    TASKS[new_id] = {
        "id": new_id,
        "title": title,
        "done": False,
        "status": "todo",
        "due_date": due_date,
        "user_id": user_id,
    }
    return TASKS[new_id]

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

def list_tasks(tag: str | None = None) -> list[dict]:
    """Retrieve all tasks, optionally filtered by tag.

    Args:
        tag: If given, only tasks carrying this tag are returned; if None,
            every task is returned.

    Returns:
        A list of task records, empty if no task has the given tag.

    Raises:
        ValidationError: If tag is not None and not a valid tag name.
    """
    from services.tags import TASK_TAGS, _validate_tag

    if tag is None:
        return list(TASKS.values())
    _validate_tag(tag)
    tagged_ids = {task_id for task_id, t in TASK_TAGS if t == tag}
    return [task for task in TASKS.values() if task["id"] in tagged_ids]
