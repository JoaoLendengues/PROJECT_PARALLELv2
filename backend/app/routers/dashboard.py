from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.network_topology import get_topology_catalog, get_unit_topology, normalize_company

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


def _resolve_local_target(empresa: Optional[str]) -> dict:
    import os
    from urllib.parse import urlparse

    normalized_company = normalize_company(empresa)
    configured_port = os.getenv("REDE_LOCAL_PORT") or os.getenv("LOCAL_NETWORK_PORT")
    topology = get_unit_topology(normalized_company)

    if topology.get("firewall"):
        target = dict(topology["firewall"])
        if configured_port:
            target["port"] = int(configured_port)
        target["empresa"] = normalized_company
        return target

    configured_host = os.getenv("REDE_LOCAL_HOST") or os.getenv("LOCAL_NETWORK_HOST")
    if configured_host:
        return {
            "empresa": normalized_company or "LOCAL",
            "host": configured_host,
            "port": int(configured_port or 8443),
            "label": "Firewall local configurado",
        }

    database_url = os.getenv("DATABASE_URL", "")
    parsed_database = urlparse(database_url)
    if parsed_database.hostname and parsed_database.hostname not in {"localhost", "127.0.0.1"}:
        return {
            "empresa": normalized_company or "LOCAL",
            "host": parsed_database.hostname,
            "port": int(configured_port or parsed_database.port or 8000),
            "label": "Servidor local da aplicacao",
        }

    fallback = dict(get_topology_catalog()["PINHEIRO SIA"]["firewall"])
    fallback["empresa"] = normalized_company or "PINHEIRO SIA"
    return fallback


def _probe_tcp_target(host: str, port: int, label: str, empresa_monitorada: Optional[str] = None) -> dict:
    import socket
    import time

    try:
        start_time = time.time()
        with socket.create_connection((host, int(port)), timeout=3):
            pass
        end_time = time.time()

        latency_ms = int((end_time - start_time) * 1000)
        if latency_ms < 40:
            qualidade = "excelente"
            cor = "#10b981"
            barras = 4
            icone = "online"
        elif latency_ms < 90:
            qualidade = "bom"
            cor = "#3b82f6"
            barras = 3
            icone = "bom"
        elif latency_ms < 180:
            qualidade = "regular"
            cor = "#f59e0b"
            barras = 2
            icone = "regular"
        else:
            qualidade = "ruim"
            cor = "#ef4444"
            barras = 1
            icone = "ruim"

        return {
            "status": "online",
            "latencia_ms": latency_ms,
            "qualidade": qualidade,
            "cor": cor,
            "barras": barras,
            "icone": icone,
            "empresa_monitorada": empresa_monitorada,
            "servidor": f"{label} ({host}:{port})",
            "detalhe": f"Resposta em {latency_ms} ms",
            "host": host,
            "port": int(port),
            "label": label,
        }
    except TimeoutError:
        return {
            "status": "offline",
            "latencia_ms": None,
            "qualidade": "offline",
            "cor": "#ef4444",
            "barras": 0,
            "icone": "offline",
            "empresa_monitorada": empresa_monitorada,
            "servidor": f"{label} ({host}:{port})",
            "detalhe": "Sem resposta no tempo esperado",
            "host": host,
            "port": int(port),
            "label": label,
        }
    except Exception as exc:
        return {
            "status": "erro",
            "latencia_ms": None,
            "qualidade": "erro",
            "cor": "#ef4444",
            "barras": 0,
            "icone": "erro",
            "empresa_monitorada": empresa_monitorada,
            "servidor": f"{label} ({host}:{port})",
            "detalhe": str(exc)[:80],
            "host": host,
            "port": int(port),
            "label": label,
        }


@router.get("/resumo")
def get_dashboard_resumo(db: Session = Depends(get_db)):
    """Retorna resumo para o dashboard."""
    total_materiais = db.query(models.Material).filter(models.Material.status == "ativo").count()
    maquinas_ativas = db.query(models.Maquina).filter(models.Maquina.status == "ativo").count()
    manutencoes_pendentes = db.query(models.Manutencao).filter(models.Manutencao.status == "pendente").count()
    pedidos_pendentes = db.query(models.Pedido).filter(models.Pedido.status == "pendente").count()
    movimentacoes_hoje = db.query(models.Movimentacao).filter(models.Movimentacao.data_hora >= date.today()).count()
    demandas_abertas = db.query(models.Demanda).filter(models.Demanda.status == "aberto").count()

    return {
        "resumo": {
            "total_materiais": total_materiais,
            "itens_baixo_estoque": 0,
            "maquinas_ativas": maquinas_ativas,
            "manutencoes_pendentes": manutencoes_pendentes,
            "pedidos_pendentes": pedidos_pendentes,
            "movimentacoes_hoje": movimentacoes_hoje,
            "demandas_abertas": demandas_abertas,
        }
    }


@router.get("/status-internet")
def get_status_internet(empresa: Optional[str] = None):
    """Retorna o status da rede local usando o firewall da unidade como alvo."""
    target = _resolve_local_target(empresa)
    return _probe_tcp_target(
        host=target["host"],
        port=target["port"],
        label=target["label"],
        empresa_monitorada=empresa,
    )


@router.get("/status-lan-to-lan")
def get_status_lan_to_lan(empresa: Optional[str] = None):
    """Retorna a conectividade da unidade atual para os firewalls das outras unidades."""
    origem = _resolve_local_target(empresa)
    empresa_origem = normalize_company(empresa)
    topology_catalog = get_topology_catalog()

    destinos = []
    for empresa_destino, unit in topology_catalog.items():
        if empresa_origem and empresa_destino == empresa_origem:
            continue
        if unit.get("firewall"):
            destinos.append((empresa_destino, dict(unit["firewall"])))

    if not destinos and empresa_origem in topology_catalog and topology_catalog[empresa_origem].get("firewall"):
        destinos = [(empresa_origem, dict(topology_catalog[empresa_origem]["firewall"]))]

    def monitorar_destino(item):
        empresa_destino, target = item
        resultado = _probe_tcp_target(
            host=target["host"],
            port=target["port"],
            label=target["label"],
            empresa_monitorada=empresa,
        )
        resultado["empresa"] = empresa_destino
        return resultado

    if destinos:
        with ThreadPoolExecutor(max_workers=min(3, len(destinos))) as executor:
            links = list(executor.map(monitorar_destino, destinos))
    else:
        links = []

    resumo = {
        "online": sum(1 for link in links if link.get("status") == "online"),
        "offline": sum(1 for link in links if link.get("status") == "offline"),
        "erro": sum(1 for link in links if link.get("status") == "erro"),
        "total": len(links),
    }

    return {
        "empresa_origem": empresa_origem or origem.get("empresa"),
        "origem": origem,
        "links": links,
        "resumo": resumo,
    }


@router.get("/topologia-links")
def get_topologia_links(empresa: Optional[str] = None):
    """Retorna o cadastro de firewalls e links dedicados por unidade."""
    empresa_origem = normalize_company(empresa)
    catalog = list(get_topology_catalog().values())
    unidade_atual = get_unit_topology(empresa_origem)

    return {
        "empresa_origem": empresa_origem or unidade_atual.get("empresa"),
        "unidade_atual": unidade_atual,
        "unidades": catalog,
    }
