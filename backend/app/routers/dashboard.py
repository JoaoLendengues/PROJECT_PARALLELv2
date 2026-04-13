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
                'movimentacoes_hoje': movimentacoes_hoje

        }
    }


