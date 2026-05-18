import os
import unicodedata
from typing import Dict, Optional


def normalize_company(value: Optional[str]) -> str:
    text = str(value or "").strip().upper()
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    return "".join(char for char in text if not unicodedata.combining(char))


UNIT_TOPOLOGY = {
    "PINHEIRO TAGUATINGA": {
        "firewall": {
            "host": "10.1.1.100",
            "port": 8443,
            "label": "Firewall Netdeep - PINHEIRO TAGUATINGA",
        },
        "links_dedicados": [
            {
                "id": "principal",
                "nome": "Link dedicado principal",
                "label": "Link dedicado principal - PINHEIRO TAGUATINGA",
                "host_env": "LINK_TAGUATINGA_PRINCIPAL_HOST",
                "port_env": "LINK_TAGUATINGA_PRINCIPAL_PORT",
            },
            {
                "id": "backup",
                "nome": "Link dedicado backup",
                "label": "Link dedicado backup - PINHEIRO TAGUATINGA",
                "host_env": "LINK_TAGUATINGA_BACKUP_HOST",
                "port_env": "LINK_TAGUATINGA_BACKUP_PORT",
            },
        ],
    },
    "PINHEIRO SIA": {
        "firewall": {
            "host": "10.1.1.150",
            "port": 8443,
            "label": "Firewall Netdeep - PINHEIRO SIA",
        },
        "links_dedicados": [
            {
                "id": "principal",
                "nome": "Link dedicado principal",
                "label": "Link dedicado principal - PINHEIRO SIA",
                "host_env": "LINK_SIA_PRINCIPAL_HOST",
                "port_env": "LINK_SIA_PRINCIPAL_PORT",
            },
            {
                "id": "backup",
                "nome": "Link dedicado backup",
                "label": "Link dedicado backup - PINHEIRO SIA",
                "host_env": "LINK_SIA_BACKUP_HOST",
                "port_env": "LINK_SIA_BACKUP_PORT",
            },
        ],
    },
    "PINHEIRO INDUSTRIA": {
        "firewall": {
            "host": "85.113.93.6",
            "port": 8443,
            "label": "Firewall Netdeep - PINHEIRO INDUSTRIA",
        },
        "links_dedicados": [
            {
                "id": "principal",
                "nome": "Link dedicado principal",
                "label": "Link dedicado principal - PINHEIRO INDUSTRIA",
                "host_env": "LINK_INDUSTRIA_PRINCIPAL_HOST",
                "port_env": "LINK_INDUSTRIA_PRINCIPAL_PORT",
            },
            {
                "id": "backup",
                "nome": "Link dedicado backup",
                "label": "Link dedicado backup - PINHEIRO INDUSTRIA",
                "host_env": "LINK_INDUSTRIA_BACKUP_HOST",
                "port_env": "LINK_INDUSTRIA_BACKUP_PORT",
            },
        ],
    },
}


def _resolve_link_entry(entry: Dict) -> Dict:
    host = (os.getenv(entry["host_env"], "") or "").strip()
    raw_port = (os.getenv(entry["port_env"], "") or "").strip()
    try:
        port = int(raw_port) if raw_port else 443
    except ValueError:
        port = 443

    return {
        "id": entry["id"],
        "nome": entry["nome"],
        "label": entry["label"],
        "host": host or None,
        "port": port,
        "configurado": bool(host),
        "host_env": entry["host_env"],
        "port_env": entry["port_env"],
    }


def get_topology_catalog() -> Dict[str, Dict]:
    catalog = {}
    for company, unit in UNIT_TOPOLOGY.items():
        catalog[company] = {
            "empresa": company,
            "firewall": dict(unit["firewall"]),
            "links_dedicados": [_resolve_link_entry(entry) for entry in unit.get("links_dedicados", [])],
        }
    return catalog


def get_unit_topology(company: Optional[str]) -> Dict:
    normalized = normalize_company(company)
    catalog = get_topology_catalog()
    if normalized in catalog:
        return catalog[normalized]
    return {
        "empresa": normalized or "LOCAL",
        "firewall": None,
        "links_dedicados": [],
    }
