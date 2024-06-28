import logging

from flask import request, jsonify

import nesis.api.core.controllers as controllers
import nesis.api.core.services as services
import nesis.api.core.services.util as util
from nesis.api.core.util.common import (
    get_bearer_token,
)
from .api import app, error_message

_LOG = logging.getLogger(__name__)


@app.route("/v1/apps", methods=[controllers.POST, controllers.GET])
def operate_apps():
    """Operate apps.
    ---
    get:
      parameters:
        - in: header
          name: Authorization
          schema:
            type: string
          required: true
          description: The authentication token obtained from a POST /session or POST /apps.
      responses:
        200:
          content:
            application/json:
              schema: AppsSchema
        401:
          content:
            application/json:
              schema: MessageSchema
    post:
      summary: Creates a new app.
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
            schema: AppReqSchema
      responses:
        200:
          content:
            application/json:
              schema: AppPostResSchema
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
                result = services.app_service.create(token=token, app=request.json)
                return jsonify(result.to_dict(include="secret"))
            case controllers.GET:
                results = services.app_service.get(token=token)
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
        _LOG.exception("Error getting app")
        return jsonify(error_message("Server error")), 500


@app.route(
    "/v1/apps/<app_id>",
    methods=[controllers.GET, controllers.DELETE, controllers.PUT],
)
def operate_app(app_id):
    """Operate on a app.
    ---
    get:
      summary: Get a single app by app_id.
      parameters:
        - in: header
          name: Authorization
          schema:
            type: string
          required: true
          description: The authentication token obtained from a POST /session or POST /apps.
        - in: path
          name: app_id
          schema:
            type: string
          required: true
          description: The app id to get
      responses:
        200:
          content:
            application/json:
              schema: DatasourceResSchema
        401:
          content:
            application/json:
              schema: MessageSchema
        404:
          content:
            application/json:
              schema: MessageSchema
    delete:
      summary: Delete a single app by app_id.
      parameters:
        - in: header
          name: Authorization
          schema:
            type: string
          required: true
          description: The authentication token obtained from a POST /session or POST /apps.
        - in: path
          name: app_id
          schema:
            type: string
          required: true
          description: The app id to delete
      responses:
        200:
            description: OK
        401:
          content:
            application/json:
              schema: MessageSchema
    put:
      summary: Creates a new app.
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
            schema: DatasourceReqSchema
      responses:
        200:
          content:
            application/json:
              schema: DatasourceResSchema
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
                results = services.app_service.get(token=token, app_id=app_id)
                if len(results) != 0:
                    return jsonify(results[0].to_dict())
                else:
                    return (
                        jsonify(
                            error_message(
                                f"App {app_id} not found", message_type="WARN"
                            )
                        ),
                        404,
                    )
            case controllers.DELETE:
                services.app_service.delete(token=token, app_id=app_id)
                return jsonify(success=True)
            case controllers.PUT:
                result = services.app_service.update(
                    token=token, app_id=app_id, app=request.json
                )
                return jsonify(result.to_dict())

    except util.ServiceException as se:
        return jsonify(error_message(str(se))), 400
    except util.UnauthorizedAccess:
        return jsonify(error_message("Unauthorized access")), 401
    except util.PermissionException as ex:
        return jsonify(error_message(str(ex))), 403
    except:
        _LOG.exception("Error getting app")
        return jsonify(error_message("Server error")), 500


@app.route("/v1/apps/<app_id>/roles", methods=[controllers.POST, controllers.GET])
def operate_app_roles(app_id):
    token = get_bearer_token(request.headers.get("Authorization"))
    try:
        match request.method:
            case controllers.POST:
                result = services.app_service.update(
                    token=token,
                    app_id=app_id,
                    app={"roles": [request.json.get("id")]},
                )
                return jsonify(result.to_dict())
            case controllers.GET:
                results = services.app_service.get_roles(token=token, app_id=app_id)
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
