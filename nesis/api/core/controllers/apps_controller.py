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
    token = get_bearer_token(request.headers.get("Authorization"))
    try:
        match request.method:
            case controllers.POST:
                result = services.app_service.create(token=token, app=request.json)
                return jsonify(result.to_dict())
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
