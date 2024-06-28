from flask import request, jsonify

from . import GET, POST, DELETE
from .api import app, error_message

import logging
import nesis.api.core.services as services
import nesis.api.core.services.util as util
from nesis.api.core.util.common import (
    get_bearer_token,
)


_LOG = logging.getLogger(__name__)


@app.route("/v1/modules/<module>/settings", methods=[POST, GET])
def operate_settings(module):
    token = get_bearer_token(request.headers.get("Authorization"))
    try:
        if request.method == POST:
            result = services.settings_service.create(
                token=token, setting=request.json, module=module
            )
            return jsonify(result.to_dict())
        else:
            results = services.settings_service.get(token=token, module=module)
            return jsonify({"items": [item.to_dict() for item in results]})
    except util.ServiceException as se:
        return jsonify(error_message(str(se))), 400
    except util.UnauthorizedAccess:
        return jsonify(error_message("Unauthorized access")), 401
    except util.PermissionException as ex:
        return jsonify(error_message(str(ex))), 403
    except:
        _LOG.exception("Error getting user")
        return jsonify(error_message("Server error")), 500


@app.route("/v1/modules/<module>/settings/<setting_id>", methods=[GET, DELETE])
def operate_setting(module, setting_id):
    token = get_bearer_token(request.headers.get("Authorization"))
    try:
        if request.method == GET:
            results = services.settings_service.get(
                token=token, module=module, setting_id=setting_id
            )
            if len(results) != 0:
                return jsonify(results[0].to_dict())
            else:
                return (
                    jsonify(
                        error_message(
                            f"Settings {setting_id} not found", message_type="WARN"
                        )
                    ),
                    404,
                )
        else:
            services.settings_service.delete(
                token=token, module=module, setting_id=setting_id
            )
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
