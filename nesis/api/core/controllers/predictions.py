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
                        token=token, module=module, payload=request.json
                    )
                case _:
                    raise util.ServiceException("Invalid module")
            return jsonify(result.to_dict())

    except util.ServiceException as se:
        return jsonify(error_message(str(se))), 400
    except util.UnauthorizedAccess:
        return jsonify(error_message("Unauthorized access")), 401
    except util.PermissionException:
        return jsonify(error_message("Forbidden action on resource")), 403
    except:
        _LOG.exception("Error getting user")
        return jsonify(error_message("Server error")), 500
