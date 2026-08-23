from app import create_app


class CorsLoginConfig:
    TESTING = True
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_NAME = "test_session"
    PERMANENT_SESSION_LIFETIME = 3600
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    CSRF_PROTECT = True
    FINGERPRINT_PROVIDER = "mock"
    ZKTECO_DEVICE_INDEX = 0
    ZKTECO_CAPTURE_TIMEOUT_SECONDS = 15
    ZKTECO_ENROLL_SAMPLES = 3
    ZKTECO_MATCH_THRESHOLD = 1


def test_login_preflight_allows_localhost_and_loopback_origins():
    app = create_app(CorsLoginConfig)
    client = app.test_client()

    for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
        response = client.open(
            "/api/auth/login",
            method="OPTIONS",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

        assert response.status_code == 200
        assert response.headers["Access-Control-Allow-Origin"] == origin
        assert response.headers["Access-Control-Allow-Credentials"] == "true"
        assert "POST" in response.headers["Access-Control-Allow-Methods"]
