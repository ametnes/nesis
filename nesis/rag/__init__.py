"""rag."""

import os
import logging

# Set to 'DEBUG' to have extensive logging turned on, even for libraries
ROOT_LOG_LEVEL = os.environ.get("LOG_LEVEL") or "INFO"

PRETTY_LOG_FORMAT = (
    "%(asctime)s.%(msecs)03d [%(levelname)-8s] %(name)+25s - %(message)s"
)
logging.basicConfig(
    level=ROOT_LOG_LEVEL, format=PRETTY_LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S"
)
logging.captureWarnings(True)
