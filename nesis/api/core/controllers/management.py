from flask import request, jsonify

from . import GET, POST, DELETE, PUT
from .api import app, error_message

import logging
import nesis.api.core.services as services
import nesis.api.core.services.util as util
from nesis.api.core.util.common import (
    get_bearer_token,
)


_LOG = logging.getLogger(__name__)


@app.route("/v1/users", methods=[POST, GET])
def operate_users():
    """Operate on users.
    ---
    get:
      summary: Get all users available.
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
              schema: UsersSchema
        401:
          content:
            application/json:
              schema: MessageSchema
    post:
      summary: Creates a new user.
      requestBody:
        required: true
        content:
          application/json:
            schema: UserReqSchema
      responses:
        200:
          content:
            application/json:
              schema: UserResSchema
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
        if request.method == POST:
            result = services.user_service.create(token=token, user=request.json)
            return jsonify(result.to_dict())
        else:
            results = services.user_service.get(token=token)
            return jsonify({"items": [item.to_dict() for item in results]})
    except util.ServiceException as se:
        return jsonify(error_message(str(se))), 400
    except util.ConflictException as se:
        return jsonify(error_message(str(se))), 409
    except util.UnauthorizedAccess:
        return jsonify(error_message("Unauthorized access")), 401
    except util.PermissionException as ex:
        return jsonify(error_message(str(ex))), 403
    except:
        _LOG.exception("Error getting user")
        return jsonify(error_message("Server error")), 500


@app.route("/v1/users/<user_id>", methods=[GET, DELETE, PUT])
def operate_user(user_id):
    """Operate on a user.
    ---
    get:
      summary: Get a single user by user_id.
      parameters:
        - in: header
          name: Authorization
          schema:
            type: string
          required: true
          description: The authentication token obtained from a POST /session or POST /apps.
        - in: path
          name: user_id
          schema:
            type: string
          required: true
          description: The user id to get
      responses:
        200:
          content:
            application/json:
              schema: UserResSchema
        401:
          content:
            application/json:
              schema: MessageSchema
        404:
          content:
            application/json:
              schema: MessageSchema
    delete:
      summary: Delete a single user by user_id.
      parameters:
        - in: header
          name: Authorization
          schema:
            type: string
          required: true
          description: The authentication token obtained from a POST /session or POST /apps.
        - in: path
          name: user_id
          schema:
            type: string
          required: true
          description: The user id to delete
      responses:
        200:
            description: OK
        401:
          content:
            application/json:
              schema: MessageSchema
    put:
      summary: Updates a new user.
      parameters:
        - in: header
          name: Authorization
          schema:
            type: string
          required: true
          description: The authentication token obtained from a POST /session or POST /apps.
      requestBody:
        required: true
        content:
          application/json:
            schema: UserReqSchema
      responses:
        200:
          content:
            application/json:
              schema: UserResSchema
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
        if request.method == GET:
            results = services.user_service.get(token=token, user_id=user_id)
            if len(results) != 0:
                return jsonify(results[0].to_dict())
            else:
                return (
                    jsonify(
                        error_message(f"User {user_id} not found", message_type="WARN")
                    ),
                    404,
                )

        elif request.method == PUT:
            result = services.user_service.update(
                token=token, user_id=user_id, user=request.json
            )
            return jsonify(result.to_dict())
        else:
            services.user_service.delete(token=token, user_id=user_id)
            return jsonify(success=True)
    except util.ServiceException as se:
        return jsonify(error_message(str(se))), 400
    except util.UnauthorizedAccess:
        return jsonify(error_message("Unauthorized access")), 401
    except util.PermissionException as ex:
        return jsonify(error_message(str(ex))), 403
    except:
        _LOG.exception("Error getting user")
        return jsonify(error_message("Server error")), 500


@app.route("/v1/users/<user_id>/roles", methods=[POST, GET])
def operate_user_roles(user_id):
    token = get_bearer_token(request.headers.get("Authorization"))
    try:
        if request.method == POST:
            result = services.user_service.update(
                token=token, user_id=user_id, user={"roles": [request.json.get("id")]}
            )
            return jsonify(result.to_dict())
        else:
            results = services.user_service.get_roles(token=token, user_id=user_id)
            return jsonify({"items": [item.to_dict() for item in results]})
    except util.ServiceException as se:
        return jsonify(error_message(str(se))), 400
    except util.ConflictException as se:
        return jsonify(error_message(str(se))), 409
    except util.UnauthorizedAccess:
        return jsonify(error_message("Unauthorized access")), 401
    except util.PermissionException as ex:
        return jsonify(error_message(str(ex))), 403
    except:
        _LOG.exception("Error getting user")
        return jsonify(error_message("Server error")), 500


@app.route("/v1/users/<user_id>/roles/<role_id>", methods=[DELETE])
def operate_user_role(user_id, role_id):
    token = get_bearer_token(request.headers.get("Authorization"))
    try:
        services.user_service.delete_role(token=token, user_id=user_id, role_id=role_id)
        return jsonify(success=True)
    except util.ServiceException as se:
        return jsonify(error_message(str(se))), 400
    except util.UnauthorizedAccess:
        return jsonify(error_message("Unauthorized access")), 401
    except util.PermissionException as ex:
        return jsonify(error_message(str(ex))), 403
    except:
        _LOG.exception("Error getting user")
        return jsonify(error_message("Server error")), 500


# User role management
@app.route("/v1/roles", methods=[POST, GET])
def operate_roles():
    """Operate on roles.
    ---
    get:
      summary: Get all roles available.
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
              schema: RolesSchema
        401:
          content:
            application/json:
              schema: MessageSchema
    post:
      summary: Creates a new role.
      requestBody:
        required: true
        content:
          application/json:
            schema: RoleReqSchema
      responses:
        200:
          content:
            application/json:
              schema: RoleResSchema
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
        if request.method == POST:
            result = services.role_service.create(token=token, role=request.json)
            return jsonify(result.to_dict())
        else:
            results = services.role_service.get(token=token)
            return jsonify({"items": [item.to_dict() for item in results]})
    except util.ConflictException as se:
        return jsonify(error_message(str(se))), 409
    except util.ServiceException as se:
        return jsonify(error_message(str(se))), 400
    except util.UnauthorizedAccess:
        return jsonify(error_message("Unauthorized access")), 401
    except util.PermissionException as ex:
        return jsonify(error_message(str(ex))), 403
    except:
        _LOG.exception("Error getting user")
        return jsonify(error_message("Server error")), 500


@app.route("/v1/roles/<role_id>", methods=[GET, DELETE, PUT])
def operate_role(role_id):
    """Operate on a role.
    ---
    get:
      summary: Get a single role by roleId.
      parameters:
        - in: header
          name: Authorization
          schema:
            type: string
          required: true
        - in: path
          name: roleId
          schema:
            type: string
          required: true
          description: The role id to get
      responses:
        200:
          content:
            application/json:
              schema: RoleResSchema
        401:
          content:
            application/json:
              schema: MessageSchema
        404:
          content:
            application/json:
              schema: MessageSchema
    delete:
      summary: Delete a single role by roleId.
      parameters:
        - in: header
          name: Authorization
          schema:
            type: string
          required: true
        - in: path
          name: taskId
          schema:
            type: string
          required: true
          description: The role id to delete
      responses:
        200:
            description: OK
        401:
          content:
            application/json:
              schema: MessageSchema
    put:
      summary: Creates a new task.
      requestBody:
        required: true
        content:
          application/json:
            schema: RoleReqSchema
      responses:
        200:
          content:
            application/json:
              schema: RoleResSchema
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
        if request.method == GET:
            try:
                results = services.role_service.get(token=token, role_id=role_id)
                if len(results) != 0:
                    return jsonify(results[0].to_dict())
                else:
                    return (
                        jsonify(
                            error_message(
                                f"Role {role_id} not found", message_type="WARN"
                            )
                        ),
                        404,
                    )
            except:
                _LOG.exception("Error getting user")
                return jsonify(error_message("Server error")), 500
        elif request.method == DELETE:
            try:
                services.role_service.delete(token=token, user_id=role_id)
                return jsonify(success=True)
            except:
                _LOG.exception("Error getting role")
                return jsonify(error_message("Server error")), 500
        else:
            result = services.role_service.update(
                token=token, id=role_id, role=request.json
            )
            return jsonify(result.to_dict())
    except util.ConflictException as se:
        return jsonify(error_message(str(se))), 409
    except util.ServiceException as se:
        return jsonify(error_message(str(se))), 400
    except util.PermissionException as ex:
        return jsonify(error_message(str(ex))), 403
    except util.UnauthorizedAccess:
        return jsonify(error_message("Unauthorized access")), 401


@app.route("/v1/sessions", methods=[POST, DELETE])
def operate_sessions():
    """Operate on a user session.
    ---
    post:
      summary: Creates a new user session.
      requestBody:
        required: true
        content:
          application/json:
            schema: SessionReqSchema
      responses:
        200:
          content:
            application/json:
              schema: SessionResSchema
        400:
          content:
            application/json:
              schema: MessageSchema
        401:
          content:
            application/json:
              schema: MessageSchema
    delete:
      summary: Delete a session.
      parameters:
        - in: header
          name: Authorization
          schema:
            type: string
          required: true
      responses:
        200:
            description: OK
        401:
          content:
            application/json:
              schema: MessageSchema
    """
    token = get_bearer_token(request.headers.get("Authorization"))
    try:
        if request.method == POST:
            result = services.user_session_service.create(session=request.json)
            return jsonify(result.to_dict())
        else:
            services.user_session_service.delete(token=token)
            return jsonify(success=True)
    except util.ServiceException as se:
        return jsonify(error_message(str(se))), 400
    except util.UnauthorizedAccess:
        return jsonify(error_message("Unauthorized access")), 401
    except util.PermissionException as ex:
        return jsonify(error_message(str(ex))), 403
    except:
        _LOG.exception("Error operating session")
        return jsonify(error_message("Server error")), 500
