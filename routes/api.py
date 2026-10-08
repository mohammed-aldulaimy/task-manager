from flask import Blueprint, jsonify, request

from services.tags import add_tag, remove_tag
from services.tasks import (  # noqa: F401
    PRIORITY_DEFAULT,
    create_task,
    get_overdue_tasks,
    get_task,
    list_tasks,
    process_order,
    update_task,
)
from services.users import (
    get_notification_pref,
    get_user,
    list_users,
    update_notification_pref,
)
from utils.errors import AppError

api = Blueprint("api", __name__)

@api.errorhandler(AppError)
def handle_app_error(e):
    return jsonify({"error": e.message}), e.status_code

@api.route("/tasks/overdue", methods=["GET"])
def get_overdue_tasks_route():
    return jsonify(get_overdue_tasks())

@api.route("/tasks/<int:task_id>", methods=["GET"])
def get_task_route(task_id):
    return jsonify(get_task(task_id))

@api.route("/tasks/<int:task_id>", methods=["PATCH"])
def update_task_route(task_id):
    data = request.get_json(silent=True) or {}
    fields = {k: data[k] for k in ("title", "due_date", "priority") if k in data}
    return jsonify(update_task(task_id, **fields))

@api.route("/tasks", methods=["POST"])
def create_task_route():
    data = request.get_json(silent=True) or {}
    task = create_task(
        data.get("title"),
        data.get("user_id"),
        data.get("due_date"),
        data.get("priority", PRIORITY_DEFAULT),
    )
    return jsonify(task), 201

@api.route("/tasks", methods=["GET"])
def list_tasks_route():
    priority = request.args.get("priority")
    if priority is not None and priority.isdecimal():
        priority = int(priority)
    return jsonify(list_tasks(request.args.get("tag"), priority=priority))

@api.route("/tasks/<int:task_id>/tags", methods=["POST"])
def add_tag_route(task_id):
    data = request.get_json(silent=True) or {}
    tags = add_tag(task_id, data.get("tag"))
    return jsonify({"task_id": task_id, "tags": tags}), 201

@api.route("/tasks/<int:task_id>/tags/<tag>", methods=["DELETE"])
def remove_tag_route(task_id, tag):
    tags = remove_tag(task_id, tag)
    return jsonify({"task_id": task_id, "tags": tags})

@api.route("/users/<int:user_id>", methods=["GET"])
def get_user_route(user_id):
    return jsonify(get_user(user_id))

@api.route("/users", methods=["GET"])
def list_users_route():
    return jsonify(list_users())

@api.route("/users/<int:user_id>/notifications", methods=["GET"])
def get_notification_pref_route(user_id):
    return jsonify(
        {"user_id": user_id, "notification_pref": get_notification_pref(user_id)}
    )

@api.route("/users/<int:user_id>/notifications", methods=["PATCH"])
def update_notification_pref_route(user_id):
    data = request.get_json(silent=True) or {}
    user = update_notification_pref(user_id, data.get("notification_pref"))
    return jsonify({"user_id": user["id"], "notification_pref": user["notification_pref"]})
