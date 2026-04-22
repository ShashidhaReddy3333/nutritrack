import ipaddress

from fastapi import Request
from slowapi import Limiter

from app.core.config import settings
from app.core.security import decode_token

ACCESS_COOKIE = "nutritrack_access"


def _trusted_proxy_networks() -> list[ipaddress._BaseNetwork]:
    networks: list[ipaddress._BaseNetwork] = []
    for cidr in settings.TRUSTED_PROXY_CIDRS:
        try:
            networks.append(ipaddress.ip_network(cidr, strict=False))
        except ValueError:
            continue
    return networks


TRUSTED_PROXY_NETWORKS = _trusted_proxy_networks()


def _is_trusted_proxy(host: str | None) -> bool:
    if not host:
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return any(address in network for network in TRUSTED_PROXY_NETWORKS)


def client_ip(request: Request) -> str:
    peer_host = request.client.host if request.client else None
    if _is_trusted_proxy(peer_host):
        forwarded_for = request.headers.get("x-forwarded-for", "")
        first_hop = forwarded_for.split(",", 1)[0].strip()
        if first_hop:
            return first_hop
    return peer_host or "unknown"


def rate_limit_key(request: Request) -> str:
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()

    user_id = decode_token(token) if token else None
    if user_id:
        return f"user:{user_id}"
    return f"ip:{client_ip(request)}"


limiter = Limiter(
    key_func=rate_limit_key,
    storage_uri=settings.RATE_LIMIT_STORAGE_URI,
)
