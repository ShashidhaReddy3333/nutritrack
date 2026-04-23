from starlette.requests import Request

from app.core.rate_limit import rate_limit_key
from app.core.security import create_access_token


def make_request(headers=None, client=("127.0.0.1", 12345)):
    encoded_headers = [
        (key.lower().encode("latin-1"), value.encode("latin-1"))
        for key, value in (headers or {}).items()
    ]
    return Request({"type": "http", "method": "GET", "path": "/", "headers": encoded_headers, "client": client})


def test_rate_limit_key_uses_forwarded_ip_from_trusted_proxy():
    request = make_request({"x-forwarded-for": "203.0.113.10, 10.0.0.5"})
    assert rate_limit_key(request) == "ip:203.0.113.10"


def test_rate_limit_key_prefers_authenticated_user_cookie():
    token = create_access_token("user-123")
    request = make_request({"cookie": f"nutritrack_access={token}"})
    assert rate_limit_key(request) == "user:user-123"
