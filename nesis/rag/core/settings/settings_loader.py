import functools
import logging
import os
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic.v1.utils import deep_update, unique_list

from nesis.rag.core.constants import PROJECT_ROOT_PATH
from nesis.rag.core.settings.yaml import load_yaml_with_envvars

logger = logging.getLogger(__name__)


# if running in unittest, use the test profile
_test_profile = ["test"] if "tests.fixtures" in sys.modules else []

active_profiles: list[str] = unique_list(
    ["default"]
    + [
        item.strip()
        for item in os.environ.get("PGPT_PROFILES", "").split(",")
        if item.strip()
    ]
    + _test_profile
)


def merge_settings(settings: Iterable[dict[str, Any]]) -> dict[str, Any]:
    return functools.reduce(deep_update, settings, {})


def load_settings_from_profile(profile: str) -> dict[str, Any]:
    _settings_home = os.environ.get("OPTIMAL_SETTINGS_HOME") or PROJECT_ROOT_PATH
    profile_file_name = os.environ.get("OPTIMAL_SETTINGS_FILE")

    if profile_file_name is None:
        if profile == "default":
            profile_file_name = "settings.yaml"
        else:
            profile_file_name = f"settings-{profile}.yaml"

        path = Path(_settings_home) / profile_file_name
    else:
        path = Path(profile_file_name)

    with Path(path).open("r") as f:
        config = load_yaml_with_envvars(f)
    if not isinstance(config, dict):
        raise TypeError(f"Config file has no top-level mapping: {path}")
    return config


def load_active_settings() -> dict[str, Any]:
    """Load active profiles and merge them."""
    logger.info("Starting application with profiles=%s", active_profiles)
    loaded_profiles = [
        load_settings_from_profile(profile) for profile in active_profiles
    ]
    merged: dict[str, Any] = merge_settings(loaded_profiles)
    return merged
