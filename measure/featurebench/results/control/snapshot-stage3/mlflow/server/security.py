import logging
from http import HTTPStatus

from flask import Flask, Response, request
from flask_cors import CORS

from mlflow.environment_variables import (
    MLFLOW_SERVER_DISABLE_SECURITY_MIDDLEWARE,
    MLFLOW_SERVER_X_FRAME_OPTIONS,
)
from mlflow.server.security_utils import (
    CORS_BLOCKED_MSG,
    HEALTH_ENDPOINTS,
    INVALID_HOST_MSG,
    LOCALHOST_ORIGIN_PATTERNS,
    get_allowed_hosts_from_env,
    get_allowed_origins_from_env,
    get_default_allowed_hosts,
    is_allowed_host_header,
    is_api_endpoint,
    should_block_cors_request,
)
from mlflow.tracing.constant import TRACE_RENDERER_ASSET_PATH

_logger = logging.getLogger(__name__)


def get_allowed_hosts() -> list[str]:
    """
    Get the list of allowed hosts for the MLflow server.

    Environment-configured hosts take precedence; otherwise the defaults are returned.
    """
    return get_allowed_hosts_from_env() or get_default_allowed_hosts()


def get_allowed_origins() -> list[str]:
    """
    Get list of allowed CORS origins from environment or defaults.

    Returns an empty list when no origins are configured in the environment.
    """
    return get_allowed_origins_from_env() or []


def init_security_middleware(app: Flask) -> None:
    """
    Initialize security middleware for the Flask application.

    Configures Host header validation, Flask-CORS, blocking of disallowed cross-origin
    state-changing API requests, and the X-Content-Type-Options and X-Frame-Options
    response headers. Does nothing when MLFLOW_SERVER_DISABLE_SECURITY_MIDDLEWARE is
    exactly "true".

    Args:
        app (Flask): The Flask application instance to configure.
    """
    if MLFLOW_SERVER_DISABLE_SECURITY_MIDDLEWARE.get() == "true":
        return

    allowed_origins = get_allowed_origins()
    allowed_hosts = get_allowed_hosts()
    x_frame_options = MLFLOW_SERVER_X_FRAME_OPTIONS.get()

    if allowed_origins and "*" in allowed_origins:
        cors_origins = "*"
    else:
        cors_origins = LOCALHOST_ORIGIN_PATTERNS + allowed_origins

    CORS(
        app,
        origins=cors_origins,
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers="*",
        expose_headers="*",
    )

    @app.before_request
    def _validate_host_header():
        if request.path in HEALTH_ENDPOINTS:
            return None
        host = request.headers.get("Host", "")
        if not is_allowed_host_header(allowed_hosts, host):
            _logger.warning(f"Rejected request with invalid Host header: {host}")
            return Response(INVALID_HOST_MSG, status=HTTPStatus.FORBIDDEN, mimetype="text/plain")
        return None

    @app.before_request
    def _block_disallowed_cross_origin_requests():
        if not is_api_endpoint(request.path):
            return None
        origin = request.headers.get("Origin", "")
        if should_block_cors_request(origin, request.method, allowed_origins):
            _logger.warning(f"Blocked cross-origin request from {origin}")
            return Response(CORS_BLOCKED_MSG, status=HTTPStatus.FORBIDDEN, mimetype="text/plain")
        return None

    @app.after_request
    def _add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Skip X-Frame-Options for the notebook renderer so it can be embedded in notebooks
        is_notebook_renderer = request.path.startswith(TRACE_RENDERER_ASSET_PATH)
        if x_frame_options and x_frame_options.upper() != "NONE" and not is_notebook_renderer:
            response.headers["X-Frame-Options"] = x_frame_options.upper()

        if (
            request.method == "OPTIONS"
            and response.status_code == HTTPStatus.OK
            and is_api_endpoint(request.path)
        ):
            response.status_code = HTTPStatus.NO_CONTENT
        return response
