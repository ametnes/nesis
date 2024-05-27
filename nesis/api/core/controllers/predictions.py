from flask import request, jsonify
from . import GET, POST, DELETE, PUT
from .api import app, error_message

from nesis.api.core.models.entities import Module
import logging
import nesis.api.core.services as services
import nesis.api.core.services.util as util
from nesis.api.core.util.common import (
    get_bearer_token,
)

_LOG = logging.getLogger(__name__)


@app.route("/v1/modules/<module>/predictions", methods=[GET, POST])
def operate_module_predictions(module):
    """Operate on predictions.
    ---
    get:
      summary: Get all predictions available.
      parameters:
        - in: header
          name: Authorization
          schema:
            type: string
          required: true
          description: The authentication token obtained from a POST /session or POST /apps.
        - in: path
          name: module
          schema:
            type: string
          required: true
          description: The module. Must be 'qanda'
      responses:
        200:
          content:
            application/json:
              schema: PredictionsSchema
        401:
          content:
            application/json:
              schema: MessageSchema
    post:
      summary: Creates a new prediction.
      parameters:
        - in: header
          name: Authorization
          schema:
            type: string
          required: true
          description: The authentication token obtained from a POST /session or POST /apps.
        - in: header
          name: X-Nesis-Request-UserKey
          description: The user_id to inherit permissions from. This is useful when the Authorization header is an app API token.
          schema:
            type: string
          required: false
      requestBody:
        required: true
        content:
          application/json:
            schema: PredictionReqSchema
      responses:
        200:
          content:
            application/json:
              schema: PredictionResSchema
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
            match Module[module]:
                case Module.qanda:
                    results = services.qanda_prediction_service.get(
                        token=token, module=module
                    )
                    return jsonify(
                        {"items": [item.to_dict(exclude="data") for item in results]}
                    )
                case _:
                    raise util.ServiceException("Invalid module")
        else:
            match Module[module]:
                case Module.qanda:
                    result = services.qanda_prediction_service.create(
                        token=token,
                        module=module,
                        payload=request.json,
                        user_id=request.headers.get("X-Nesis-Request-UserKey"),
                    )
                case _:
                    raise util.ServiceException("Invalid module")
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
