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


@app.route("/v1/datasources", methods=[POST, GET])
def operate_datasources():
    token = get_bearer_token(request.headers.get("Authorization"))
    try:
        if request.method == POST:
            result = services.datasource_service.create(
                token=token, datasource=request.json
            )
            return jsonify(result.to_dict())
        else:
            results = services.datasource_service.get(token=token)
            return jsonify({"items": [item.to_dict() for item in results]})
    except util.ServiceException as se:
        return jsonify(error_message(str(se))), 400
    except util.UnauthorizedAccess:
        return jsonify(error_message("Unauthorized access")), 401
    except util.PermissionException:
        return jsonify(error_message("Forbidden resource")), 403
    except util.ValidationException:
        return jsonify(error_message("Unable to validate datasource connection")), 403
    except:
        _LOG.exception("Error getting user")
        return jsonify(error_message("Server error")), 500


@app.route("/v1/datasources/<datasource_id>", methods=[GET, DELETE])
def operate_datasource(datasource_id):
    token = get_bearer_token(request.headers.get("Authorization"))
    try:
        if request.method == GET:
            results = services.datasource_service.get(
                token=token, datasource_id=datasource_id
            )
            if len(results) != 0:
                return jsonify(results[0].to_dict())
            else:
                return (
                    jsonify(
                        error_message(
                            f"Datasource {datasource_id} not found", message_type="WARN"
                        )
                    ),
                    404,
                )
        else:
            services.datasource_service.delete(token=token, datasource_id=datasource_id)
            return jsonify(success=True)
    except util.ServiceException as se:
        return jsonify(error_message(str(se))), 400
    except util.UnauthorizedAccess:
        return jsonify(error_message("Unauthorized access")), 401
    except util.PermissionException:
        return jsonify(error_message("Forbidden resource")), 403
    except:
        _LOG.exception("Error getting user")
        return jsonify(error_message("Server error")), 500


@app.route("/v1/datasources/<datasource>/dataobjects/<dataobject>", methods=[GET])
def operate_dataobject(datasource, dataobject):
    token = get_bearer_token(request.headers.get("Authorization"))
    try:
        if request.method == GET:
            results = services.dataobject_service.get(
                token=token, datasource=datasource, dataobject=dataobject
            )
            return jsonify(results.to_dict())

    except util.ServiceException as se:
        return jsonify(error_message(str(se))), 400
    except util.UnauthorizedAccess:
        return jsonify(error_message("Unauthorized access")), 401
    except util.PermissionException:
        return jsonify(error_message("Forbidden resource")), 403
    except:
        _LOG.exception("Error getting user")
        return jsonify(error_message("Server error")), 500
