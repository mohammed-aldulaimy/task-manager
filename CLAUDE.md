# Task Manager

# Goal
Python Flask API for managing tasks and users.
# Commands
Run all three before declaring any task done:
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
Missing join row (e.g. removing a tag the task doesn't have): raise NotFoundError("<Resource>"), e.g. NotFoundError("Tag")
Check foreign keys by calling the owning module's getter (get_task, get_user) so it raises NotFoundError
Tests: pytest.raises(<specific AppError subclass>), never pytest.raises(Exception) (ruff B017)
Tests that mutate a store: autouse fixture snapshots it and restores in place (store.clear(); store.update(snapshot)); see tests/test_tags.py
API tests: app.test_client() from app.py; routes are under /api

# Architecture
Layered pattern: routes -> services. Services are the data layer; there is no repositories layer
Routes (routes/api.py): Parse the request, call one service function, return jsonify(___). 
    Blueprint mounted at /api in app.py
    Read bodies with request.get_json(silent=True) or {} and data.get(...), so missing fields reach service validation (422) instead of a 500
    Creating something returns 201; mutating a task's tags returns {"task_id": ..., "tags": [...]}
Services (services/tasks.py, services/users.py, services/tags.py): All validation and data access. Each module owns its store
    Stores are module-level in-memory structures (USERS, TASKS dicts); data resets on server restart
    Join tables are sets of tuples, e.g. TASK_TAGS: set[tuple[int, str]] in services/tags.py stands in for task_tags
    tags.py imports get_task from tasks.py at the top; tasks.py imports from services.tags inside the function body (list_tasks) to avoid a circular import. Follow this for any new cross-service dependency
    List/filter functions return an empty list when nothing matches (not an error). Tag lists are returned sorted alphabetically
Errors: services raise AppError subclasses from utils/errors.py; handle_app_error in routes/api.py turns them into JSON responses.
Canonical example: get_user in services/users.py
# Do Not Touch
Signatures of get_task, create_task, process_order, list_tasks, add_tag, remove_tag, imported directly by routes/api.py
utils/errors.py constructors and message / status_code attributes. Add subclasses when needed but don't edit these.
Never raise plain Exception, ValueError, or KeyError from services
Never create a repositories/ package or add a database
Never delete an existing test assertion to make tests pass
DRILL_PROMPTS.md, not project code, dont touch