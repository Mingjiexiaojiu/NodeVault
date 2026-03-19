"""SSRF protection — validate URLs before making outbound requests."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from backend.core.config import settings

# Private / reserved IP networks that must be blocked by default
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local / cloud metadata
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fd00::/8"),
]


class SSRFError(Exception):
    """Raised when a URL targets a private / blocked address."""


def _parse_allowed_cidrs() -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    raw = settings.allowed_private_cidrs.strip()
    if not raw:
        return []
    cidrs: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for cidr in raw.split(","):
        cidr = cidr.strip()
        if cidr:
            cidrs.append(ipaddress.ip_network(cidr, strict=False))
    return cidrs


def validate_url(url: str) -> str:
    """Validate *url* is safe for server-side requests.

    Returns the resolved URL (unchanged). Raises ``SSRFError`` if the
    target resolves to a private/blocked IP address.
    """
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise SSRFError(f"Invalid URL (no hostname): {url}")

    # Resolve hostname → IP addresses
    try:
        infos = socket.getaddrinfo(hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise SSRFError(f"Cannot resolve hostname {hostname!r}: {exc}") from exc

    allowed = _parse_allowed_cidrs()

    for family, _type, _proto, _canonname, sockaddr in infos:
        ip = ipaddress.ip_address(sockaddr[0])
        for net in _BLOCKED_NETWORKS:
            if ip in net:
                # Check whitelist
                if any(ip in a for a in allowed):
                    continue
                raise SSRFError(
                    f"URL {url!r} resolves to private address {ip} "
                    f"which is blocked. Add to ALLOWED_PRIVATE_CIDRS to allow."
                )
    return url
