from flask import Blueprint, jsonify, request

from services.tags import add_tag, remove_tag
from services.tasks import (  # noqa: F401
    create_task,
    get_overdue_tasks,
    get_task,
    list_tasks,
    process_order,
)
from services.users import get_user
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

@api.route("/tasks", methods=["POST"])
def create_task_route():
    data = request.get_json()
    return jsonify(create_task(data["title"], data["user_id"], data.get("due_date"))), 201

@api.route("/tasks", methods=["GET"])
def list_tasks_route():
    return jsonify(list_tasks(request.args.get("tag")))

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
