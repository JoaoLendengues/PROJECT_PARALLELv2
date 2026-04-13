from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from datetime import datetime, date

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/resumo")
def get_dashboard_resumo(db: Session = Depends(get_db)):
    """Retorna resumo para o dashboard"""
    
    # Contar materiais ativos
    total_materiais = db.query(models.Material).filter(
        models.Material.status == 'ativo'
    ).count()

    # Contar máquinas ativas
    maquinas_ativas = db.query(models.Maquina).filter(
        models.Maquina.status == 'ativo'
    ).count()

    # Contar manutenções pendentes
    manutencoes_pendentes = db.query(models.Manutencao).filter(
        models.Manutencao.status == 'pendente'
    ).count()

    # Contar pedidos pendentes
    pedidos_pendentes = db.query(models.Pedido).filter(
        models.Pedido.status == 'pendente'
    ).count()

    # Contar movimentações de hoje
    movimentacoes_hoje = db.query(models.Movimentacao).filter(
        models.Movimentacao.data_hora >= date.today()
    ).count()

    # Contar demandas abertas
    demandas_abertas = db.query(models.Demanda).filter(
        models.Demanda.status == 'aberto'
    ).count()



    # Contar items com estoque baixo
    itens_baixo_estoque = 0
    

    return {
        'resumo': {
                'total_materiais': total_materiais,
                'itens_baixo_estoque': itens_baixo_estoque,
                'maquinas_ativas': maquinas_ativas,
                'manutencoes_pendentes': manutencoes_pendentes,
                'pedidos_pendentes': pedidos_pendentes,
                'movimentacoes_hoje': movimentacoes_hoje,
                'demandas_abertas': demandas_abertas
        }
    }

@router.get('/status-internet')
def get_status_internet():
    """Retorna o status da internet (latência e qualidade)"""
    import os
    import time
    import requests

    # Usar variável de ambiente ou valor padrão
    SERVIDOR_DNS = os.getenv("SERVIDOR_DNS", "10.1.1.10")
    url = f"https://{SERVIDOR_DNS}"
    
    try:
        # Medir latência para o servidor DNS configurado
        start_time = time.time()
        response = requests.get(url, timeout=5, verify=False)
        end_time = time.time()

        latency_ms = int((end_time - start_time) * 1000)

        # Determinar qualidade da internet baseada na latência
        if latency_ms < 50:
            qualidade = 'excelente'
            cor = '#10b981'  # Verde
            barras = 4
            icone = '🟢'
        elif latency_ms < 100:
            qualidade = 'bom'
            cor = '#3b82f6'  # Azul
            barras = 3
            icone = '📶'
        elif latency_ms < 200:
            qualidade = 'regular'
            cor = '#f59e0b'  # Laranja
            barras = 2
            icone = '⚠️'
        else:
            qualidade = 'ruim'
            cor = '#ef4444'
            barras = 1
            icone = '🔴'

        return {
            'status': 'online',
            'latencia_ms': latency_ms,
            'qualidade': qualidade,
            'cor': cor,
            'barras': barras,
            'icone': icone,
            'servidor': f'DNS {SERVIDOR_DNS}'
        }
    
    except requests.exceptions.Timeout:
        return {
            "status": "offline",
            "latencia_ms": None,
            "qualidade": "offline",
            "cor": "#ef4444",
            "barras": 0,
            "icone": "🔴",
            "servidor": f"DNS {SERVIDOR_DNS} (Timeout)"
        }
    
    except Exception as e:
        return {
            'status': 'erro',
            'latencia_ms': None,
            'qualidade': 'erro',
            'cor': '#ef4444',
            'barras': 0,
            'icone': '❌',
            'servidor': f"Erro: {str(e)[:40]}"
        }
