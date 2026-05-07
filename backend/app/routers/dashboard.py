from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


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
def get_status_internet(empresa: str | None = None):
    """Retorna o status da rede local usando o firewall da unidade como alvo."""
    import os
    import socket
    import time
    import unicodedata
    from urllib.parse import urlparse

    firewall_targets = {
        "PINHEIRO TAGUATINGA": {
            "host": "10.1.1.100",
            "port": 8443,
            "label": "Firewall Netdeep - PINHEIRO TAGUATINGA",
        },
        "PINHEIRO SIA": {
            "host": "10.1.1.150",
            "port": 8443,
            "label": "Firewall Netdeep - PINHEIRO SIA",
        },
        "PINHEIRO INDUSTRIA": {
            "host": "85.113.93.6",
            "port": 8443,
            "label": "Firewall Netdeep - PINHEIRO INDUSTRIA",
        },
    }

    def normalize_company(value: str | None) -> str:
        text = str(value or "").strip().upper()
        if not text:
            return ""
        text = unicodedata.normalize("NFKD", text)
        return "".join(char for char in text if not unicodedata.combining(char))

    def get_local_target():
        normalized_company = normalize_company(empresa)
        configured_port = os.getenv("REDE_LOCAL_PORT") or os.getenv("LOCAL_NETWORK_PORT")

        if normalized_company in firewall_targets:
            target = dict(firewall_targets[normalized_company])
            if configured_port:
                target["port"] = int(configured_port)
            return target

        configured_host = os.getenv("REDE_LOCAL_HOST") or os.getenv("LOCAL_NETWORK_HOST")
        if configured_host:
            return {
                "host": configured_host,
                "port": int(configured_port or 8443),
                "label": "Firewall local configurado",
            }

        database_url = os.getenv("DATABASE_URL", "")
        parsed_database = urlparse(database_url)
        if parsed_database.hostname and parsed_database.hostname not in {"localhost", "127.0.0.1"}:
            return {
                "host": parsed_database.hostname,
                "port": int(configured_port or parsed_database.port or 8000),
                "label": "Servidor local da aplicacao",
            }

        return {
            "host": "10.1.1.150",
            "port": int(configured_port or 8443),
            "label": "Firewall Netdeep - PINHEIRO SIA",
        }

    try:
        target = get_local_target()
        host = target["host"]
        port = int(target["port"])
        label = target["label"]

        start_time = time.time()
        with socket.create_connection((host, port), timeout=3):
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
            "empresa_monitorada": empresa,
            "servidor": f"{label} ({host}:{port})",
        }

    except TimeoutError:
        return {
            "status": "offline",
            "latencia_ms": None,
            "qualidade": "offline",
            "cor": "#ef4444",
            "barras": 0,
            "icone": "offline",
            "empresa_monitorada": empresa,
            "servidor": "Firewall local (timeout)",
        }

    except Exception as exc:
        return {
            "status": "erro",
            "latencia_ms": None,
            "qualidade": "erro",
            "cor": "#ef4444",
            "barras": 0,
            "icone": "erro",
            "empresa_monitorada": empresa,
            "servidor": f"Erro: {str(exc)[:40]}",
        }
