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

    Args:
        var_name (str): The name of the environment variable to retrieve
        default (str, optional): Default value to return if the variable is not found
            in either location. Defaults to empty string.

    Returns:
        str: The OS environment value if available, otherwise the value from Claude
            settings, or the default value if not found in either location.
    """
    if var_name in os.environ:
        return os.environ[var_name]

    try:
        settings = load_claude_config(Path(".claude") / "settings.json")
        env = settings.get(ENVIRONMENT_FIELD, {})
        return env.get(var_name, default)
    except Exception:
        return default


def get_tracing_status(settings_path: Path) -> TracingStatus:
    """
    Get current tracing status from Claude settings and environment configuration.

    Args:
        settings_path (Path): Path to the Claude settings.json file.

    Returns:
        TracingStatus: Tracing state with the MLflow tracking URI, experiment ID and
            experiment name read from the settings "environment" field, and a reason
            when tracing is disabled.
    """
    if not settings_path.exists():
        return TracingStatus(enabled=False, reason="No configuration found")

    config = load_claude_config(settings_path)
    env = config.get(ENVIRONMENT_FIELD, {})

    if env.get(MLFLOW_TRACING_ENABLED) != "true":
        return TracingStatus(
            enabled=False,
            reason=f"{MLFLOW_TRACING_ENABLED} is not set to 'true'",
        )

    return TracingStatus(
        enabled=True,
        tracking_uri=env.get(MLFLOW_TRACKING_URI.name),
        experiment_id=env.get(MLFLOW_EXPERIMENT_ID.name),
        experiment_name=env.get(MLFLOW_EXPERIMENT_NAME.name),
    )


def load_claude_config(settings_path: Path) -> dict[str, Any]:
    """
    Load existing Claude configuration from settings file.

    Args:
        settings_path (Path): Path to the Claude settings.json file to load.

    Returns:
        dict[str, Any]: Parsed JSON data from the settings file, or an empty dict if the
            file does not exist, cannot be read, or contains invalid JSON.
    """
    try:
        with open(settings_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save_claude_config(settings_path: Path, config: dict[str, Any]) -> None:
    """
    Save Claude configuration to settings file.

    Args:
        settings_path (Path): Path to the Claude settings.json file. Parent directories
            are created if they don't exist.
        config (dict[str, Any]): Configuration to save as JSON with 2-space indentation.

    Returns:
        None
    """
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def setup_environment_config(
    settings_path: Path,
    tracking_uri: str | None = None,
    experiment_id: str | None = None,
    experiment_name: str | None = None,
) -> None:
    """
    Set up MLflow environment variables in Claude settings configuration.

    Args:
        settings_path (Path): Path to the Claude settings.json file.
        tracking_uri (str | None, optional): MLflow tracking URI. A truthy value updates
            the setting; otherwise any existing tracking URI is left unchanged.
        experiment_id (str | None, optional): MLflow experiment ID. A truthy value takes
            precedence over experiment_name and removes any existing experiment name.
        experiment_name (str | None, optional): MLflow experiment name. Used only if
            experiment_id is not truthy.

    Returns:
        None
    """
    config = load_claude_config(settings_path)
    env = config.get(ENVIRONMENT_FIELD)
    if not isinstance(env, dict):
        env = {}
        config[ENVIRONMENT_FIELD] = env

    env[MLFLOW_TRACING_ENABLED] = "true"

    if tracking_uri:
        env[MLFLOW_TRACKING_URI.name] = tracking_uri

    if experiment_id:
        env[MLFLOW_EXPERIMENT_ID.name] = experiment_id
        env.pop(MLFLOW_EXPERIMENT_NAME.name, None)
    elif experiment_name:
        env[MLFLOW_EXPERIMENT_NAME.name] = experiment_name

    save_claude_config(settings_path, config)
