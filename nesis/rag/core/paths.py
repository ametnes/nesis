from pathlib import Path

from nesis.rag.core.constants import PROJECT_ROOT_PATH
from nesis.rag.core.settings.settings import settings


def _absolute_or_from_project_root(path: str) -> Path:
    if path.startswith("/"):
        return Path(path)
    return PROJECT_ROOT_PATH / path


models_path: Path = _absolute_or_from_project_root(settings().data.models_folder)
models_cache_path: Path = models_path / "cache"
docs_path: Path = PROJECT_ROOT_PATH / "docs"
local_data_path: Path = _absolute_or_from_project_root(
    settings().data.local_data_folder
)
