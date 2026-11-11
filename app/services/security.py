import ipaddress
import socket
from typing import Tuple
from urllib.parse import urlparse
from fastapi import HTTPException


class SecurityService:
    """Provides URL safety verification, SSRF prevention, and request payload boundary checks."""

    ALLOWED_SCHEMES = {"http", "https"}

    BLOCKED_NETWORKS = [
        ipaddress.ip_network("0.0.0.0/8"),
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("169.254.0.0/16"),  # Link-local / Cloud Metadata
        ipaddress.ip_network("224.0.0.0/4"),     # Multicast
        ipaddress.ip_network("240.0.0.0/4"),     # Reserved
        ipaddress.ip_network("::1/128"),         # IPv6 Loopback
        ipaddress.ip_network("fc00::/7"),        # IPv6 Private
        ipaddress.ip_network("fe80::/10"),       # IPv6 Link-local
    ]

    @classmethod
    def validate_url_safety(cls, url: str) -> Tuple[bool, str]:
        """Validates that a URL is safe to fetch, preventing SSRF attacks on private networks."""
        try:
            parsed = urlparse(url)
        except Exception:
            return False, "Invalid URL format"

        if parsed.scheme.lower() not in cls.ALLOWED_SCHEMES:
            return False, f"Disallowed URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted."

        hostname = parsed.hostname
        if not hostname:
            return False, "URL hostname cannot be empty."

        # Check for literal IP addresses or resolve domain
        try:
            ip_objs = []
            try:
                # Direct IP literal check
                ip_objs.append(ipaddress.ip_address(hostname))
            except ValueError:
                # DNS Resolution
                addr_info = socket.getaddrinfo(hostname, None)
                for res in addr_info:
                    ip_str = res[4][0]
                    ip_objs.append(ipaddress.ip_address(ip_str))

            for ip in ip_objs:
                for blocked_net in cls.BLOCKED_NETWORKS:
                    if ip in blocked_net:
                        return False, f"Access to private/internal network IP range ({ip}) is strictly forbidden."

        except socket.gaierror:
            return False, f"Failed to resolve DNS for hostname '{hostname}'"
        except Exception as e:
            return False, f"Security verification error: {str(e)}"

        return True, "URL is safe"

    @classmethod
    def enforce_safe_url(cls, url: str):
        """Helper that raises HTTP 400 if URL safety validation fails."""
        is_safe, reason = cls.validate_url_safety(url)
        if not is_safe:
            raise HTTPException(status_code=400, detail=f"SSRF Security Restriction: {reason}")