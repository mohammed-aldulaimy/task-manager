import re

from services.tasks import get_task
from utils.errors import NotFoundError, ValidationError

TAG_MAX_LEN = 32

TAG_PATTERN = re.compile(r"^[a-z0-9_-]+$")

TASK_TAGS: set[tuple[int, str]] = {
    (1, "errand"),
    (2, "work"),
    (3, "health"),
}

def _validate_tag(tag: str) -> None:
    """Validate a tag name.

    Args:
        tag: The tag to validate. Must be a non-empty string of at most
            TAG_MAX_LEN characters made of lowercase letters, digits,
            "_" or "-".

    Returns:
        None.

    Raises:
        ValidationError: If tag is empty, longer than TAG_MAX_LEN characters,
            not a string, or not lowercase with no spaces.
    """
    if tag is None:
        raise ValidationError("tag", "cannot be empty")
    if not isinstance(tag, str):
        raise ValidationError("tag", "must be lowercase with no spaces")
    if not tag.strip():
        raise ValidationError("tag", "cannot be empty")
    if len(tag) > TAG_MAX_LEN:
        raise ValidationError("tag", f"must be at most {TAG_MAX_LEN} characters")
    if not TAG_PATTERN.fullmatch(tag):
        raise ValidationError("tag", "must be lowercase with no spaces")

def _sorted_tags(task_id: int) -> list[str]:
    """Return a task's tags sorted alphabetically.

    Args:
        task_id: The unique identifier for the task.

    Returns:
        The task's tags in alphabetical order, empty if it has none.

    Raises:
        None.
    """
    return sorted(tag for tid, tag in TASK_TAGS if tid == task_id)

def get_tags_for_task(task_id: int) -> list[str]:
    """Retrieve all tags attached to a task.

    Args:
        task_id: The unique identifier for the task.

    Returns:
        The task's tags sorted alphabetically, empty if it has none.

    Raises:
        NotFoundError: If no task exists with the given ID.
    """
    get_task(task_id)
    return _sorted_tags(task_id)

def add_tag(task_id: int, tag: str) -> list[str]:
    """Attach a tag to a task.

    Adding a tag the task already has is a no-op and raises no error.

    Args:
        task_id: The unique identifier for the task.
        tag: The tag to attach.

    Returns:
        The task's tags sorted alphabetically, including the new tag.

    Raises:
        ValidationError: If tag is empty or not a valid tag name.
        NotFoundError: If no task exists with the given ID.
    """
    _validate_tag(tag)
    get_task(task_id)
    TASK_TAGS.add((task_id, tag))
    return _sorted_tags(task_id)

def remove_tag(task_id: int, tag: str) -> list[str]:
    """Detach a tag from a task.

    Args:
        task_id: The unique identifier for the task.
        tag: The tag to detach.

    Returns:
        The task's remaining tags sorted alphabetically.

    Raises:
        ValidationError: If tag is empty or not a valid tag name.
        NotFoundError: If no task exists with the given ID, or the task
            does not have the given tag.
    """
    _validate_tag(tag)
    get_task(task_id)
    if (task_id, tag) not in TASK_TAGS:
        raise NotFoundError("Tag")
    TASK_TAGS.remove((task_id, tag))
    return _sorted_tags(task_id)
