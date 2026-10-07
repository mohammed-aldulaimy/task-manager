# Task Manager

Python Flask API for managing tasks and users.

# Goal
Add a new function to @services/tasks.py that returns all
tasks for a given user_id. Follow the same pattern as the existing functions. Add a test for it. Run pytest -v when done.
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

# Architecture
Layered pattern: routes -> services -> repositories
Routes (routes/api.py): Parse the request, call one service function, return jsonify(___). 
Services (services/tasks.py, services/users.py): All validation and data access. Each module owns its store
Errors: services raise AppError subclasses from utils/errors.py; handle_app_error in routes/api.py turns them into JSON responses.
Canonical example: get_user in services/users.py
# Do Not Touch
Signatures of get_task, create_task, process_order, imported directly by routes/api.py
utils/errors.py constructors and message / status_code attributes. Add subclasses when needed but don't edit these.
Never raise plain Exception, ValueError, or KeyError from services
Never create a repositories/ package or add a database
Never delete an existing test assertion to make tests pass
DRILL_PROMPTS.md, not project code, dont touch