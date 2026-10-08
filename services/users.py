from utils.errors import NotFoundError, ValidationError

NOTIFICATION_PREFS = ("email", "sms", "none")
NOTIFICATION_PREF_DEFAULT = "none"

USERS: dict[int, dict] = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com",
        "notification_pref": NOTIFICATION_PREF_DEFAULT},
    2: {"id": 2, "name": "Bob",   "email": "bob@example.com",
        "notification_pref": NOTIFICATION_PREF_DEFAULT},
}

def get_user(user_id: int) -> dict:
    """Retrieve a user by ID.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        The user record as a dictionary.

    Raises:
        NotFoundError: If no user exists with the given ID.
    """
    if user_id not in USERS:
        raise NotFoundError("User")
    return USERS[user_id]

def create_user(name: str, email: str) -> dict:
    """Create a new user.

    Args:
        name: The user's display name.
        email: The user's email address.

    Returns:
        The newly created user record, with notification_pref set to
        NOTIFICATION_PREF_DEFAULT.

    Raises:
        ValidationError: If name or email is empty.
    """
    if not name or not name.strip():
        raise ValidationError("name", "cannot be empty")
    if not email or "@" not in email:
        raise ValidationError("email", "must be a valid email address")
    new_id = max(USERS.keys()) + 1
    USERS[new_id] = {"id": new_id, "name": name, "email": email,
                     "notification_pref": NOTIFICATION_PREF_DEFAULT}
    return USERS[new_id]

def _validate_notification_pref(notification_pref: str) -> None:
    """Validate a user notification preference.

    Args:
        notification_pref: One of NOTIFICATION_PREFS ("email", "sms", "none").

    Returns:
        None.

    Raises:
        ValidationError: If notification_pref is None, not a string, or not
            exactly one of NOTIFICATION_PREFS (case and whitespace are not
            normalized).
    """
    if notification_pref is None:
        raise ValidationError("notification_pref", "cannot be empty")
    if not isinstance(notification_pref, str) or notification_pref not in NOTIFICATION_PREFS:
        raise ValidationError(
            "notification_pref", f"must be one of: {', '.join(NOTIFICATION_PREFS)}"
        )

def list_users() -> list[dict]:
    """Retrieve all users.

    Returns:
        A list of all user records, empty if there are none.
    """
    return list(USERS.values())

def get_notification_pref(user_id: int) -> str:
    """Retrieve a user's notification preference.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        The user's notification preference, one of NOTIFICATION_PREFS.

    Raises:
        NotFoundError: If no user exists with the given ID.
    """
    return get_user(user_id)["notification_pref"]

def update_notification_pref(user_id: int, notification_pref: str) -> dict:
    """Update a user's notification preference.

    The preference is validated before the user is looked up, so invalid
    input leaves the store unchanged.

    Args:
        user_id: The unique identifier for the user.
        notification_pref: The new preference, one of NOTIFICATION_PREFS.

    Returns:
        The updated user record.

    Raises:
        ValidationError: If notification_pref is None, not a string, or not
            one of NOTIFICATION_PREFS.
        NotFoundError: If no user exists with the given ID.
    """
    _validate_notification_pref(notification_pref)
    user = get_user(user_id)
    user["notification_pref"] = notification_pref
    return user
