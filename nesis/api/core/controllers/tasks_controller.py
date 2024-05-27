from flask import request, jsonify

from . import GET, POST, DELETE, PUT
from .api import app, error_message

import logging
import nesis.api.core.services as services
import nesis.api.core.services.util as util
from nesis.api.core.util.common import (
    get_bearer_token,
)
import nesis.api.core.controllers as controllers

_LOG = logging.getLogger(__name__)


@app.route("/v1/tasks", methods=[controllers.POST, controllers.GET])
def operate_tasks():
    """Operate on tasks.
    ---
    get:
      summary: Get all tasks available.
      parameters:
        - in: header
          name: Authorization
          schema:
            type: string
          required: true
      responses:
        200:
          content:
            application/json:
              schema: TasksSchema
        401:
          content:
            application/json:
              schema: MessageSchema
    post:
      summary: Creates a new task.
      requestBody:
        required: true
        content:
          application/json:
            schema: TaskReqSchema
      responses:
        200:
          content:
            application/json:
              schema: TaskResSchema
        400:
          content:
            application/json:
              schema: MessageSchema
        401:
          content:
            application/json:
              schema: MessageSchema
        403:
          content:
            application/json:
              schema: MessageSchema
        409:
          content:
            application/json:
              schema: MessageSchema
        500:
          content:
            application/json:
              schema: MessageSchema
    """
    token = get_bearer_token(request.headers.get("Authorization"))
    try:
        match request.method:
            case controllers.POST:
                result = services.task_service.create(token=token, task=request.json)
                return jsonify(result.to_dict())
            case controllers.GET:
                results = services.task_service.get(token=token)
                return jsonify({"items": [item.to_dict() for item in results]})
    except util.ServiceException as se:
        return jsonify(error_message(str(se))), 400
    except util.UnauthorizedAccess:
        return jsonify(error_message("Unauthorized access")), 401
    except util.PermissionException as ex:
        return jsonify(error_message(str(ex))), 403
    except util.ConflictException as ce:
        return jsonify(error_message(str(ce))), 409
    except:
        _LOG.exception("Error getting user")
        return jsonify(error_message("Server error")), 500


@app.route(
    "/v1/tasks/<task_id>",
    methods=[controllers.GET, controllers.DELETE, controllers.PUT],
)
def operate_task(task_id):
    """Operate on a task.
    ---
    get:
      summary: Get a single task by task_id.
      parameters:
        - in: header
          name: Authorization
          schema:
            type: string
          required: true
          description: The authentication token obtained from a POST /session or POST /apps.
        - in: path
          name: task_id
          schema:
            type: string
          required: true
          description: The task id to get
      responses:
        200:
          content:
            application/json:
              schema: TaskResSchema
        401:
          content:
            application/json:
              schema: MessageSchema
        404:
          content:
            application/json:
              schema: MessageSchema
    delete:
      summary: Delete a single task by task_id.
      parameters:
        - in: header
          name: Authorization
          schema:
            type: string
          required: true
          description: The authentication token obtained from a POST /session or POST /apps.
        - in: path
          name: task_id
          schema:
            type: string
          required: true
          description: The task id to delete
      responses:
        200:
            description: OK
        401:
          content:
            application/json:
              schema: MessageSchema
    put:
      summary: Creates a new task.
      parameters:
        - in: header
          name: Authorization
          schema:
            type: string
          required: true
      requestBody:
        required: true
        content:
          application/json:
            schema: TaskReqSchema
      responses:
        200:
          content:
            application/json:
              schema: TaskResSchema
        400:
          content:
            application/json:
              schema: MessageSchema
        401:
          content:
            application/json:
              schema: MessageSchema
        403:
          content:
            application/json:
              schema: MessageSchema
        409:
          content:
            application/json:
              schema: MessageSchema
        500:
          content:
            application/json:
              schema: MessageSchema
    """
    token = get_bearer_token(request.headers.get("Authorization"))
    try:
        match request.method:
            case controllers.GET:
                results = services.task_service.get(token=token, task_id=task_id)
                if len(results) != 0:
                    return jsonify(results[0].to_dict())
                else:
                    return (
                        jsonify(
                            error_message(
                                f"Task {task_id} not found", message_type="WARN"
                            )
                        ),
                        404,
                    )
            case controllers.DELETE:
                services.task_service.delete(token=token, task_id=task_id)
                return jsonify(success=True)
            case controllers.PUT:
                result = services.task_service.update(
                    token=token, task_id=task_id, task=request.json
                )
                return jsonify(result.to_dict())

    except util.ServiceException as se:
        return jsonify(error_message(str(se))), 400
    except util.UnauthorizedAccess:
        return jsonify(error_message("Unauthorized access")), 401
    except util.PermissionException as ex:
        return jsonify(error_message(str(ex))), 403
    except:
        _LOG.exception("Error getting user")
        return jsonify(error_message("Server error")), 500
