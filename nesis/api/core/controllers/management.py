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
