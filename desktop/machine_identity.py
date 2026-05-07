import os
import socket
import uuid
from urllib.parse import urlparse


def _format_mac(node_value: int) -> str:
    hex_value = f"{node_value:012X}"
    return ":".join(hex_value[index:index + 2] for index in range(0, 12, 2))


def get_machine_hostname() -> str:
    return (
        os.getenv("COMPUTERNAME")
        or os.getenv("HOSTNAME")
        or socket.gethostname()
        or ""
    ).strip()


def get_machine_mac_address() -> str:
    try:
        return _format_mac(uuid.getnode())
    except Exception:
        return ""


def _host_from_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        return (parsed.hostname or "").strip()
    except Exception:
        return ""


def _probe_local_ip(target_host: str) -> str:
    if not target_host:
        return ""

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect((target_host, 80))
            return str(sock.getsockname()[0] or "").strip()
    except Exception:
        return ""


def get_machine_ip_address(preferred_url: str = "") -> str:
    target_host = _host_from_url(preferred_url)
    candidates = []

    if target_host:
        candidates.append(_probe_local_ip(target_host))

    try:
        hostname = socket.gethostname()
        _, _, host_ips = socket.gethostbyname_ex(hostname)
        for ip_address in host_ips:
            if ip_address and not ip_address.startswith("127."):
                candidates.append(ip_address.strip())
    except Exception:
        pass

    candidates.append(_probe_local_ip("8.8.8.8"))

    for candidate in candidates:
        if candidate and not candidate.startswith("127."):
            return candidate

    return ""


def get_machine_identity(preferred_url: str = "") -> dict:
    return {
        "hostname": get_machine_hostname(),
        "ip_address": get_machine_ip_address(preferred_url),
        "mac_address": get_machine_mac_address(),
    }
