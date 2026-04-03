from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/resumo")
def get_dashboard_resumo(db: Session = Depends(get_db)):
    """Retorna resumo para o dashboard"""
    
    total_materiais = db.query(models.Material).filter(models.Material.status == "ativo").count()
    maquinas_ativas = db.query(models.Maquina).filter(models.Maquina.status == "ativo").count()
    manutencoes_pendentes = db.query(models.Manutencao).filter(models.Manutencao.status == "pendente").count()
    pedidos_pendentes = db.query(models.Pedido).filter(models.Pedido.status == "pendente").count()
    
    return {
        "resumo": {
            "total_materiais": total_materiais,
            "itens_baixo_estoque": 0,
            "maquinas_ativas": maquinas_ativas,
            "manutencoes_pendentes": manutencoes_pendentes,
            "pedidos_pendentes": pedidos_pendentes,
            "movimentacoes_hoje": 0
        }
    }
