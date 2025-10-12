"""
Logging middleware for FastAPI application.

Provides request/response logging with timing information and correlation IDs.
"""

import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses.

    Logs:
    - Request method, path, and client IP
    - Request processing time
    - Response status code
    - Request correlation ID for tracing
    """

    def __init__(self, app: ASGIApp):
        """
        Initialize logging middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response
        """
        # Generate request ID for correlation
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Extract request details
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        # Start timing
        start_time = time.time()

        # Log incoming request
        logger.info(
            f"Incoming request: {method} {path}",
            extra={
                "request_id": request_id,
                "method": method,
                "endpoint": path,
                "client_ip": client_ip,
                "query_params": str(request.query_params) if request.query_params else None,
            }
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate processing time
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            logger.info(
                f"Request completed: {method} {path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "endpoint": path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                }
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate processing time
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            logger.error(
                f"Request failed: {method} {path} - {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "endpoint": path,
                    "duration_ms": round(duration_ms, 2),
                },
                exc_info=True
            )

            # Re-raise exception to be handled by FastAPI
            raise


def log_request_body(request: Request, body: dict) -> None:
    """
    Log request body with sanitization.

    Args:
        request: HTTP request
        body: Request body as dictionary
    """
    request_id = getattr(request.state, "request_id", "unknown")

    # Sanitize sensitive information
    sanitized_body = _sanitize_data(body)

    logger.debug(
        f"Request body: {sanitized_body}",
        extra={
            "request_id": request_id,
            "endpoint": request.url.path,
        }
    )


def log_response_body(request: Request, body: dict, status_code: int) -> None:
    """
    Log response body.

    Args:
        request: HTTP request
        body: Response body as dictionary
        status_code: HTTP status code
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.debug(
        f"Response body: {body}",
        extra={
            "request_id": request_id,
            "endpoint": request.url.path,
            "status_code": status_code,
        }
    )


def _sanitize_data(data: dict) -> dict:
    """
    Sanitize sensitive information from data.

    Removes or masks fields that might contain sensitive information.

    Args:
        data: Dictionary to sanitize

    Returns:
        Sanitized dictionary
    """
    if not isinstance(data, dict):
        return data

    sensitive_fields = {"password", "token", "api_key", "secret", "authorization"}
    sanitized = {}

    for key, value in data.items():
        if key.lower() in sensitive_fields:
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_data(value)
        elif isinstance(value, list):
            sanitized[key] = [
                _sanitize_data(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized
