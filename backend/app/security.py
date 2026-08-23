import secrets
from hmac import compare_digest

from flask import jsonify, request, session

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
CSRF_HEADER = "X-CSRF-Token"


def generate_csrf_token():
    token = secrets.token_urlsafe(32)
    session["csrf_token"] = token
    return token


def current_csrf_token():
    return session.get("csrf_token")


def register_security(app):
    @app.before_request
    def protect_against_csrf():
        if not should_validate_csrf(app):
            return None

        session_token = current_csrf_token()
        request_token = request.headers.get(CSRF_HEADER) or request.headers.get("X-CSRFToken")
        if not session_token or not request_token or not compare_digest(session_token, request_token):
            return (
                jsonify(
                    {
                        "success": False,
                        "code": "CSRF_INVALIDO",
                        "message": "Token CSRF invalido o ausente.",
                    }
                ),
                403,
            )
        return None

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Cache-Control", "no-store")
        return response


def should_validate_csrf(app):
    if not app.config.get("CSRF_PROTECT", not app.config.get("TESTING", False)):
        return False
    if request.method not in UNSAFE_METHODS:
        return False
    if not session.get("admin_id"):
        return False

    path = request.path
    return (
        path.startswith("/api/admin/")
        or path.startswith("/api/biometria/trabajadores/")
        or path == "/api/auth/logout"
    )
