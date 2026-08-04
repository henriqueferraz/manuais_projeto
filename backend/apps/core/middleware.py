"""Middleware de correlação request_id."""

from __future__ import annotations

import uuid

import structlog
from django.utils.deprecation import MiddlewareMixin


class RequestIdMiddleware(MiddlewareMixin):
    """Garante X-Request-ID e bind no contexto structlog."""

    HEADER = "HTTP_X_REQUEST_ID"

    def process_request(self, request):
        request_id = request.META.get(self.HEADER) or str(uuid.uuid4())
        request.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

    def process_response(self, request, response):
        request_id = getattr(request, "request_id", None)
        if request_id:
            response["X-Request-ID"] = request_id
        return response
