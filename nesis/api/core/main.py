#!/usr/bin/env python

import argparse
import json
import os
import sys

import yaml
from gevent.pywsgi import WSGIServer

working_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(working_dir)

from nesis.api.core.controllers import api as cloud_ctrl
from nesis.api.core.models import initialize_engine
from nesis.api.core.services import init_services as cloud_services
from nesis.api.core.util.http import HttpClient
import logging
import nesis.api.core.util as util

import nesis.api.core.config as settings

_LOG = logging.getLogger(__name__)


def run_cloud(app, args, services):
    config_file = args.config
    # secrets_file = args.secrets
    #
    if config_file:
        with open(config_file) as fh:
            if config_file.endswith(".json"):
                config = json.load(fh)
            else:
                config = yaml.load(fh, yaml.Loader)
    else:
        config = {}

    config = util.merge(config, settings.default)
    service_config = config.get("service") or {}

    # Initialize database
    try:
        _LOG.info("Initializing database engine...")
        initialize_engine(config)
    except:
        _LOG.exception(f"Error initializing application engine")
        sys.exit(1)

    # Initialize services
    http_client = HttpClient(config=config)

    try:
        _LOG.info("Initializing services...")
        services(config, http_client=http_client)
        _LOG.info("Done initializing services...")
    except:
        _LOG.exception(f"Error initializing services")
        sys.exit(1)

    # Start the application
    port = service_config.get("port", os.environ.get("NESIS_API_PORT")) or "6000"
    host = service_config.get("host") or "0.0.0.0"

    http_server = WSGIServer((host, int(port)), cloud_ctrl.app)

    _LOG.info("Starting server...")
    http_server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nesis API Service")
    parser.add_argument("--config", type=str, help="Configuration file", required=False)
    parser.add_argument("--port", type=str, help="Listen port", required=False)

    args = parser.parse_args()

    _LOG.info("Running the module")
    try:
        run_cloud(app=cloud_ctrl.app, services=cloud_services, args=args)
    except Exception as ex:
        _LOG.error(f"Error initializing module - {ex}", exc_info=True)
        sys.exit(1)
