# Notification Preference — Subagent Decomposition

Feature: users can set `notification_pref` to `email`, `sms`, or `none` (default `none`).
Endpoints: `GET /api/users/<id>/notifications`, `PATCH /api/users/<id>/notifications`; `GET /api/users` and `GET /api/users/<id>` include `notification_pref`.
Gate between subagents: run `pytest -q` and `ruff check .`, fix failures, pause for review.

### Subagent 1 — Data layer
- **Role:** Data-layer engineer for the users store.
- **Input:** `CLAUDE.md`; `services/users.py` (`USERS`, `create_user`); `services/tasks.py` (module-constant style: `PRIORITY_MIN/MAX/DEFAULT`).
- **Task:** Add module constants `NOTIFICATION_PREFS = ("email", "sms", "none")` and `NOTIFICATION_PREF_DEFAULT = "none"`. Add `"notification_pref": NOTIFICATION_PREF_DEFAULT` to both seed users and to the record built in `create_user`; update `create_user` docstring Returns if needed.
- **Output:** `services/users.py` (modified).
- **Constraints:** No database, no `repositories/` package, no new model class; don't change `get_user`/`create_user` signatures; don't touch `utils/errors.py`; existing tests stay green.
- **Hand-off:** Constant names `NOTIFICATION_PREFS`, `NOTIFICATION_PREF_DEFAULT`, and the guarantee that every user dict has a `notification_pref` key.

### Subagent 2 — Service layer
- **Role:** Service-layer engineer.
- **Input:** Subagent 1 hand-off; `services/users.py`; `_validate_priority` and `update_task` in `services/tasks.py` (validate → look up → mutate pattern); `utils/errors.py`.
- **Task:** Add to `services/users.py`:
  - `_validate_notification_pref(notification_pref: str) -> None` — `None` → `ValidationError("notification_pref", "cannot be empty")`; non-str or not in `NOTIFICATION_PREFS` → `ValidationError("notification_pref", "must be one of: email, sms, none")`.
  - `list_users() -> list[dict]` — all user records (empty list if none).
  - `get_notification_pref(user_id: int) -> str` — via `get_user` (raises `NotFoundError("User")`).
  - `update_notification_pref(user_id: int, notification_pref: str) -> dict` — validate first, then `get_user`, then mutate; returns the updated user record.
  - All with type hints and Google-style docstrings (Args/Returns/Raises) like `get_user`.
- **Output:** `services/users.py` (modified).
- **Constraints:** Only `ValidationError`/`NotFoundError` (never plain `Exception`/`ValueError`/`KeyError`); no normalization (`"Email"`, `" sms"` rejected); invalid input leaves the store unchanged; don't alter existing function signatures.
- **Hand-off:** Exact signatures `list_users()`, `get_notification_pref(user_id)`, `update_notification_pref(user_id, notification_pref)` and their error messages/status codes (422, 404).

### Subagent 3 — API layer
- **Role:** Route/API engineer.
- **Input:** Subagent 2 hand-off; `routes/api.py` (route style, `handle_app_error`); `app.py` (blueprint at `/api`); CLAUDE.md Routes section.
- **Task:** Import the new service functions and add:
  - `GET /users` → `jsonify(list_users())`.
  - `GET /users/<int:user_id>/notifications` → `{"user_id": ..., "notification_pref": ...}`.
  - `PATCH /users/<int:user_id>/notifications` → body via `request.get_json(silent=True) or {}`, call `update_notification_pref(user_id, data.get("notification_pref"))`, return `{"user_id": ..., "notification_pref": ...}` (200).
  - `GET /users/<id>` already returns the full record, so it includes `notification_pref` without changes.
- **Output:** `routes/api.py` (modified).
- **Constraints:** Routes parse → call one service → `jsonify`; no validation in routes; missing/null field must reach the service (422, never 500); don't change signatures of `get_task`, `process_order`, `add_tag`, `remove_tag`; no edits to `app.py`.
- **Hand-off:** Route table (method, path, success status, response JSON shape, error statuses) for the test subagent.

### Subagent 4 — Tests
- **Role:** Test engineer.
- **Input:** Hand-offs from subagents 1–3; `tests/test_tasks.py` (autouse snapshot fixture, `client` fixture, parametrized error cases).
- **Task:** Create service + API tests:
  - Autouse fixture snapshotting `USERS` as `{k: dict(v) for k, v in USERS.items()}` and restoring in place.
  - Service: default is `"none"` on seed and `create_user`; `update_notification_pref` for each valid value; parametrized invalid values (`None`, `""`, `"Email"`, `"push"`, `1`, `True`) → `ValidationError` with store unchanged; unknown user → `NotFoundError`; `get_notification_pref`; `list_users` includes the field.
  - API: GET/PATCH notifications 200 + shape; PATCH invalid/null/missing body → 422; unknown user → 404; `GET /api/users` and `GET /api/users/<id>` include `notification_pref`.
- **Output:** `tests/test_users.py` (new).
- **Constraints:** Import from `services.*` and `app`; `pytest.raises(NotFoundError|ValidationError)`, never `Exception`; don't delete or weaken existing assertions; tests must pass `ruff check .`.
- **Hand-off:** Green `pytest -v` and `ruff check .` output for final sign-off.

## Divergence
- Did Claude follow the constraint field for every subagent? If not, which constraint was violated and what did Claude do instead?
     - Claude followed the constraint field for every subagent except the test subagent, where the subagent exited early and the main agent implemented the rest of the tests as "this step only needed one new file." This went against my instructions for the subagent.
- Did any subagent's output break the next subagent's assumption? How did you recover?
     - Subagent 3 (API layer engineer), wrote new tests in a throwaway script, which I'm unsure if this broke the test subagent's assumption. I didn't instruct this subagent to write tests, however this didn't affect the final output.
- Would you write the decomposition differently a second time? What would you change?
     - I would rewrite my decomposition with stricter constraints; I treated the constraints as a guide rail for each subagent however I wasn't specific enough. For example, for subagents 1-3, I would constraint them further by explicitly instructing not to write new tests or modify tests to weaken them. 