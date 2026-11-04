"""
Shared security utilities for MLflow server middleware.

This module contains common functions used by both Flask and FastAPI
security implementations.
"""

import fnmatch
from urllib.parse import urlparse

from mlflow.environment_variables import (
    MLFLOW_SERVER_ALLOWED_HOSTS,
    MLFLOW_SERVER_CORS_ALLOWED_ORIGINS,
)

# Security response messages
INVALID_HOST_MSG = "Invalid Host header - possible DNS rebinding attack detected"
CORS_BLOCKED_MSG = "Cross-origin request blocked"

# HTTP methods that modify state
STATE_CHANGING_METHODS = ["POST", "PUT", "DELETE", "PATCH"]

# Paths exempt from host validation
HEALTH_ENDPOINTS = ["/health", "/version"]

# API path prefix for MLflow endpoints
API_PATH_PREFIX = "/api/"

# Test-only endpoints that should not have CORS blocking
TEST_ENDPOINTS = ["/test", "/api/test"]

# Localhost addresses
LOCALHOST_VARIANTS = ["localhost", "127.0.0.1", "[::1]", "0.0.0.0"]
CORS_LOCALHOST_HOSTS = ["localhost", "127.0.0.1", "[::1]", "::1"]

# Private IP range start values for 172.16.0.0/12
PRIVATE_172_RANGE_START = 16
PRIVATE_172_RANGE_END = 32

# Regex patterns for localhost origins
LOCALHOST_ORIGIN_PATTERNS = [
    r"^http://localhost(:[0-9]+)?$",
    r"^http://127\.0\.0\.1(:[0-9]+)?$",
    r"^http://\[::1\](:[0-9]+)?$",
]


def _split_env_list(value: str | None) -> list[str] | None:
    """Split a comma-separated environment value, returning None when nothing is set."""
    if not value:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def get_allowed_hosts_from_env() -> list[str] | None:
    """Return the hosts from MLFLOW_SERVER_ALLOWED_HOSTS, or None if unset."""
    return _split_env_list(MLFLOW_SERVER_ALLOWED_HOSTS.get())


def get_allowed_origins_from_env() -> list[str] | None:
    """Return the origins from MLFLOW_SERVER_CORS_ALLOWED_ORIGINS, or None if unset."""
    return _split_env_list(MLFLOW_SERVER_CORS_ALLOWED_ORIGINS.get())


def get_default_allowed_hosts() -> list[str]:
    """
    Return the default Host header patterns: localhost (all ports), and the
    private IPv4 ranges 10.0.0.0/8, 172.16.0.0/12 and 192.168.0.0/16.
    """
    hosts: list[str] = []
    for variant in LOCALHOST_VARIANTS:
        hosts.append(variant)
        hosts.append(f"{variant}:*")
    hosts.append("10.*")
    hosts.append("192.168.*")
    for second_octet in range(PRIVATE_172_RANGE_START, PRIVATE_172_RANGE_END):
        hosts.append(f"172.{second_octet}.*")
    return hosts


def is_allowed_host_header(allowed_hosts: list[str], host: str) -> bool:
    """
    Check whether a Host header value matches one of the allowed host patterns.

    Patterns containing "*" use shell-style matching; other patterns must match exactly.
    A "*" entry in allowed_hosts allows every host. Empty or None hosts are rejected.
    """
    if not host:
        return False
    if "*" in allowed_hosts:
        return True
    for pattern in allowed_hosts:
        if "*" in pattern:
            if fnmatch.fnmatch(host, pattern):
                return True
        elif host == pattern:
            return True
    return False


def is_api_endpoint(path: str) -> bool:
    """Check whether a request path is an MLflow API endpoint (excluding test-only paths)."""
    if not path.startswith(API_PATH_PREFIX):
        return False
    for test_path in TEST_ENDPOINTS:
        if path == test_path or path.startswith(test_path + "/"):
            return False
    return True


def is_localhost_origin(origin: str) -> bool:
    """Check if an origin is from localhost."""
    if not origin:
        return False

    try:
        parsed = urlparse(origin)
        hostname = parsed.hostname
        return hostname in CORS_LOCALHOST_HOSTS
    except Exception:
        return False


def should_block_cors_request(origin: str, method: str, allowed_origins: list[str] | None) -> bool:
    """Determine if a CORS request should be blocked."""
    if not origin or method not in STATE_CHANGING_METHODS:
        return False

    if is_localhost_origin(origin):
        return False

    if allowed_origins:
        # If wildcard "*" is in the list, allow all origins
        if "*" in allowed_origins:
            return False
        if origin in allowed_origins:
            return False

    return True
