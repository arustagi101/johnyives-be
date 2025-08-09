from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urlparse


def validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http/https URLs are allowed")
    if not parsed.netloc:
        raise ValueError("URL must include a host")

    hostname = parsed.hostname or ""

    # Disallow direct IPs to private/local ranges
    if _is_ip_address(hostname):
        if _is_private_ip(hostname):
            raise ValueError("Private IP addresses are not allowed")
        return

    # Resolve and check IPs for the hostname
    try:
        infos = socket.getaddrinfo(hostname, None)
        for info in infos:
            sockaddr = info[4]
            ip = sockaddr[0]
            if _is_private_ip(ip):
                raise ValueError("Resolved to a private IP; refusing to fetch")
    except socket.gaierror:
        raise ValueError("Hostname could not be resolved")


def _is_ip_address(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _is_private_ip(ip: str) -> bool:
    ip_obj = ipaddress.ip_address(ip)
    return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_link_local
