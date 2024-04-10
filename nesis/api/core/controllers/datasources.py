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
    except util.PermissionException:
        return jsonify(error_message("Forbidden action on resource")), 403
    except util.ValidationException:
        return jsonify(error_message("Unable to validate datasource connection")), 403
    except:
        _LOG.exception("Error getting user")
        return jsonify(error_message("Server error")), 500


@app.route(
    "/v1/datasources/<datasource_id>",
    methods=[controllers.GET, controllers.DELETE, controllers.PUT],
)
def operate_datasource(datasource_id):
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
    except util.PermissionException:
        return jsonify(error_message("Forbidden action on resource")), 403
    except:
        _LOG.exception("Error getting user")
        return jsonify(error_message("Server error")), 500
