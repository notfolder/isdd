"""Configuration management for Claude Code integration with MLflow."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mlflow.environment_variables import (
    MLFLOW_EXPERIMENT_ID,
    MLFLOW_EXPERIMENT_NAME,
    MLFLOW_TRACKING_URI,
)

# Configuration field constants
HOOK_FIELD_HOOKS = "hooks"
HOOK_FIELD_COMMAND = "command"
ENVIRONMENT_FIELD = "environment"

# MLflow environment variable constants
MLFLOW_HOOK_IDENTIFIER = "mlflow.claude_code.hooks"
MLFLOW_TRACING_ENABLED = "MLFLOW_CLAUDE_TRACING_ENABLED"


@dataclass
class TracingStatus:
    """Dataclass for tracing status information."""

    enabled: bool
    tracking_uri: str | None = None
    experiment_id: str | None = None
    experiment_name: str | None = None
    reason: str | None = None




def get_env_var(var_name: str, default: str = "") -> str:
    """
    Get environment variable from OS or Claude settings as fallback.

    Looks up the OS environment first, then the "environment" section of
    ".claude/settings.json" in the current directory. Returns ``default`` when
    neither has the variable. Errors while reading the settings file are ignored.

    Args:
        var_name (str): The name of the environment variable to retrieve.
        default (str, optional): Value returned when the variable is found in neither
            location. Defaults to an empty string.

    Returns:
        str: The OS value if set, otherwise the settings value, otherwise ``default``.
    """
    os_value = os.environ.get(var_name)
    if os_value is not None:
        return os_value

    try:
        config = load_claude_config(Path(".claude") / "settings.json")
        settings_value = config.get(ENVIRONMENT_FIELD, {}).get(var_name)
        if settings_value is not None:
            return settings_value
    except Exception:
        pass

    return default


def get_tracing_status(settings_path: Path) -> TracingStatus:
    """
    Get current tracing status from Claude settings and environment configuration.

    Args:
        settings_path (Path): Path to the Claude settings.json file.

    Returns:
        TracingStatus: ``enabled`` is True only when MLFLOW_CLAUDE_TRACING_ENABLED is
            "true" in the settings environment section. When enabled, the tracking URI,
            experiment ID and experiment name are read from the same section. When
            disabled, ``reason`` explains why.
    """
    if not settings_path.exists():
        return TracingStatus(enabled=False, reason="No configuration found")

    config = load_claude_config(settings_path)
    env_vars = config.get(ENVIRONMENT_FIELD, {})

    if MLFLOW_TRACING_ENABLED not in env_vars:
        return TracingStatus(enabled=False, reason="No configuration found")

    if env_vars[MLFLOW_TRACING_ENABLED] != "true":
        return TracingStatus(
            enabled=False,
            reason=f"{MLFLOW_TRACING_ENABLED} is not set to 'true'",
        )

    return TracingStatus(
        enabled=True,
        tracking_uri=env_vars.get(MLFLOW_TRACKING_URI.name),
        experiment_id=env_vars.get(MLFLOW_EXPERIMENT_ID.name),
        experiment_name=env_vars.get(MLFLOW_EXPERIMENT_NAME.name),
    )


def load_claude_config(settings_path: Path) -> dict[str, Any]:
    """
    Load existing Claude configuration from settings file.

    Args:
        settings_path (Path): Path to the Claude settings.json file to load.

    Returns:
        dict[str, Any]: The parsed JSON value. Returns an empty dict when the file is
            missing, cannot be read, or is not valid JSON. No schema validation is done.
    """
    try:
        with open(settings_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_claude_config(settings_path: Path, config: dict[str, Any]) -> None:
    """
    Save Claude configuration to settings file.

    Creates missing parent directories, then overwrites the file with the config
    serialized as UTF-8 JSON with 2-space indentation.

    Args:
        settings_path (Path): Path to the Claude settings.json file to write.
        config (dict[str, Any]): Configuration to save.

    Raises:
        OSError: If directories cannot be created or the file cannot be written.
        TypeError: If ``config`` contains values that are not JSON serializable.
    """
    path = Path(settings_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def setup_environment_config(
    settings_path: Path,
    tracking_uri: str | None = None,
    experiment_id: str | None = None,
    experiment_name: str | None = None,
) -> None:
    """
    Set up MLflow environment variables in Claude settings configuration.

    Always sets MLFLOW_CLAUDE_TRACING_ENABLED to "true". A truthy ``tracking_uri``
    overwrites the stored tracking URI. A truthy ``experiment_id`` is stored and removes
    any stored experiment name. Otherwise a truthy ``experiment_name`` is stored. Other
    existing settings are preserved.

    Args:
        settings_path (Path): Path to the Claude settings.json file. Parent directories
            are created when missing.
        tracking_uri (str | None, optional): MLflow tracking URI. Defaults to None.
        experiment_id (str | None, optional): MLflow experiment ID. Defaults to None.
        experiment_name (str | None, optional): MLflow experiment name, used only when
            ``experiment_id`` is not truthy. Defaults to None.
    """
    config = load_claude_config(settings_path)

    env_vars = config.get(ENVIRONMENT_FIELD)
    if not isinstance(env_vars, dict):
        env_vars = {}
        config[ENVIRONMENT_FIELD] = env_vars

    env_vars[MLFLOW_TRACING_ENABLED] = "true"

    if tracking_uri:
        env_vars[MLFLOW_TRACKING_URI.name] = tracking_uri

    if experiment_id:
        env_vars[MLFLOW_EXPERIMENT_ID.name] = experiment_id
        env_vars.pop(MLFLOW_EXPERIMENT_NAME.name, None)
    elif experiment_name:
        env_vars[MLFLOW_EXPERIMENT_NAME.name] = experiment_name

    save_claude_config(settings_path, config)
