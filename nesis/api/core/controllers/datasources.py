from flask import request, jsonify

import nesis.api.core.controllers as controllers
from .api import app, error_message

import logging
import nesis.api.core.services as services
import nesis.api.core.services.util as util
from nesis.api.core.util.common import (
    get_bearer_token,
)


_LOG = logging.getLogger(__name__)


@app.route("/v1/datasources", methods=[controllers.POST, controllers.GET])
def operate_datasources():
    """Operate on datasources.
    ---
    get:
      summary: Get all datasources available.
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
              schema: DatasourcesSchema
        401:
          content:
            application/json:
              schema: MessageSchema
    post:
      summary: Creates a new datasource.
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
            case controllers.POST:
                result = services.datasource_service.create(
                    token=token, datasource=request.json
                )
                return jsonify(result.to_dict())
            case controllers.GET:
                results = services.datasource_service.get(token=token)
                return jsonify({"items": [item.to_dict() for item in results]})
            case _:
                raise Exception("Should never be reached")
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


@app.route(
    "/v1/datasources/<datasource_id>",
    methods=[controllers.GET, controllers.DELETE, controllers.PUT],
)
def operate_datasource(datasource_id):
    """Operate on a datasource.
    ---
    get:
      summary: Get a single datasource by datasource_id.
      parameters:
        - in: header
          name: Authorization
          schema:
            type: string
          required: true
          description: The authentication token obtained from a POST /session or POST /apps.
        - in: path
          name: datasource_id
          schema:
            type: string
          required: true
          description: The datasource id to get
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
      summary: Delete a single datasource by datasource_id.
      parameters:
        - in: header
          name: Authorization
          schema:
            type: string
          required: true
          description: The authentication token obtained from a POST /session or POST /apps.
        - in: path
          name: datasource_id
          schema:
            type: string
          required: true
          description: The datasource id to delete
      responses:
        200:
            description: OK
        401:
          content:
            application/json:
              schema: MessageSchema
    put:
      summary: Creates a new datasource.
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
                results = services.datasource_service.get(
                    token=token, datasource_id=datasource_id
                )
                if len(results) != 0:
                    return jsonify(results[0].to_dict())
                else:
                    return (
                        jsonify(
                            error_message(
                                f"Datasource {datasource_id} not found",
                                message_type="WARN",
                            )
                        ),
                        404,
                    )
            case controllers.DELETE:
                services.datasource_service.delete(
                    token=token, datasource_id=datasource_id
                )
                return jsonify(success=True)
            case controllers.PUT:
                result = services.datasource_service.update(
                    token=token, datasource=request.json, datasource_id=datasource_id
                )
                return jsonify(result.to_dict())
            case _:
                raise Exception("Should never be reached really")
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
