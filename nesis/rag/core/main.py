"""FastAPI app creation, logger configuration and main API routes."""

import llama_index

from nesis.rag.core.di import create_application_injector
from nesis.rag.core.launcher import create_app
import uvicorn
from injector import Injector
from nesis.rag.core.settings.settings import settings

# Add LlamaIndex simple observability
llama_index.core.set_global_handler("simple")

_settings = settings()
global_injector: Injector = create_application_injector(settings=_settings)
app = create_app(global_injector, settings=_settings)

# start a fastapi server with uvicorn


# from private_gpt.settings.settings import settings

# Set log_config=None to do not use the uvicorn logging configuration, and
# use ours instead. For reference, see below:
# https://github.com/tiangolo/fastapi/discussions/7457#discussioncomment-5141108
uvicorn.run(app, host="0.0.0.0", port=_settings.server.port, log_config=None)
