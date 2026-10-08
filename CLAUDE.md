# Task Manager

# Goal
Python Flask API for managing tasks and users.
# Commands
Run all three before declaring any task done:
    Activate venv first: source .venv/bin/activate (pytest and ruff are only installed there; or call .venv/bin/pytest, .venv/bin/ruff directly)
    Install: pip install -r requirements.txt
    Tests: pytest -v (All must pass)
    Lint: ruff check .
    Run server: python app.py
# Conventions
Follow services/users.py as the pattern for every service function
Include type hints on all parameters
Google-style docstrings with Args, Returns, Raises sections, formatted like get_user
Bad input: Raise ValidationError(field, reason), reference create_user
Tests go in tests/test_<module>.py and import from services.*
Always use ValidationError for empty input fields and NotFoundError for missing foreign keys, mirroring the exact error handling pattern in services/users.py to ensure this behavior persists across all future service functions.
Field validation: private _validate_<field>(value) -> None helper that raises ValidationError, with rules as module constants (e.g. TAG_MAX_LEN, TAG_PATTERN). Match regexes with fullmatch. Reject bad input; don't normalize it (e.g. "Work" is rejected, not lowercased)
Integer fields (e.g. priority): bounds and default are module constants (PRIORITY_MIN = 1, PRIORITY_MAX = 5, PRIORITY_DEFAULT = 3); None -> ValidationError(field, "cannot be empty"); bools, floats and numeric strings ("3") are rejected, not coerced
Validate every field first, then check foreign keys / look up the record, then mutate, so bad input leaves the store unchanged (see create_task, update_task)
Partial updates (update_task): each optional field defaults to the private _UNSET marker (_Unset enum in services/tasks.py) meaning "not sent", so None stays a real value (due_date=None clears the date). Only fields that are not _UNSET are validated and applied
Filters on list functions are optional keyword params defaulting to None and combine with AND (list_tasks(tag, priority))
Missing join row (e.g. removing a tag the task doesn't have): raise NotFoundError("<Resource>"), e.g. NotFoundError("Tag")
Check foreign keys by calling the owning module's getter (get_task, get_user) so it raises NotFoundError
Tests: pytest.raises(<specific AppError subclass>), never pytest.raises(Exception) (ruff B017)
Tests that mutate a store: autouse fixture snapshots it and restores in place (store.clear(); store.update(snapshot)); see tests/test_tags.py. For dict-of-dict stores copy each record ({k: dict(v) for k, v in TASKS.items()}), since services mutate records in place; see tests/test_tasks.py
API tests: app.test_client() from app.py; routes are under /api

# Architecture
Layered pattern: routes -> services. Services are the data layer; there is no repositories layer
Routes (routes/api.py): Parse the request, call one service function, return jsonify(___). 
    Blueprint mounted at /api in app.py
    Read bodies with request.get_json(silent=True) or {} and data.get(...), so missing fields reach service validation (422) instead of a 500
    Exception, PATCH: pass only the keys present in the body (e.g. update_task(task_id, **{k: data[k] for k in (...) if k in data})), since data.get turns an omitted field into None, and None is a real value (null due_date clears it). Routes never import the service's private _UNSET marker
    Optional create fields with a service default: data.get("<field>", <DEFAULT constant>) (e.g. data.get("priority", PRIORITY_DEFAULT)), so an omitted field gets the default but an explicit null reaches validation (422)
    Integer query params (e.g. GET /tasks?priority=): convert with int() only if value.isdecimal(); otherwise pass the raw string through so the service returns 422, never a 500
    Creating something returns 201; mutating a task's tags returns {"task_id": ..., "tags": [...]}
    Sub-resource of a user (e.g. /users/<id>/notifications) returns {"user_id": ..., "<field>": ...}, built from the service's return value; GET /users/<id> returns the full record
Layer boundary (routes/ <-> services/), following services/users.py as the canonical pattern:
    Routes import only public service functions and public constants (e.g. PRIORITY_DEFAULT); never stores (USERS, TASKS, TASK_TAGS), private helpers (_validate_*), or _UNSET
    Routes do no validation, no store reads/writes, and raise no errors; anything a route would check belongs in a services/ function that raises ValidationError / NotFoundError
    Routes import only AppError from utils/errors.py (for handle_app_error); services import the specific subclasses
    Services never import flask (no request, jsonify, or status codes); they take plain Python args and return plain dicts, lists, or values, so they are callable from tests without app.test_client()
    One route calls one service function; if a route needs two, add a service function that combines them (e.g. get_notification_pref wraps get_user)
Services (services/tasks.py, services/users.py, services/tags.py): All validation and data access. Each module owns its store
    Stores are module-level in-memory structures (USERS, TASKS dicts); data resets on server restart
    Join tables are sets of tuples, e.g. TASK_TAGS: set[tuple[int, str]] in services/tags.py stands in for task_tags
    tags.py imports get_task from tasks.py at the top; tasks.py imports from services.tags inside the function body (list_tasks) to avoid a circular import. Follow this for any new cross-service dependency
    List/filter functions return an empty list when nothing matches (not an error). Tag lists are returned sorted alphabetically
Errors: services raise AppError subclasses from utils/errors.py; handle_app_error in routes/api.py turns them into JSON responses.
Canonical example: get_user in services/users.py
# Do Not Touch
Signatures of get_task, process_order, add_tag, remove_tag, imported directly by routes/api.py
    create_task and list_tasks may gain new parameters, but only appended at the end with a default, so existing callers keep working
    update_task(task_id, ...) is called by the PATCH route with keyword args; new fields are added as keyword params defaulting to _UNSET
Signatures of get_user, list_users, get_notification_pref(user_id), update_notification_pref(user_id, notification_pref), imported directly by routes/api.py
    create_user(name, email) may gain new parameters, but only appended at the end with a default
NOTIFICATION_PREFS values ("email", "sms", "none") and NOTIFICATION_PREF_DEFAULT = "none": tests and API clients depend on them; add new values only by appending
Every user record has a notification_pref key (seed users and create_user); don't remove it
utils/errors.py constructors and message / status_code attributes. Add subclasses when needed but don't edit these.
Never raise plain Exception, ValueError, or KeyError from services
Never create a repositories/ package or add a database
Never delete an existing test assertion to make tests pass
DRILL_PROMPTS.md, not project code, dont touch