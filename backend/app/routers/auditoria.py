from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import auth, models
from app.database import get_db

router = APIRouter(prefix="/api/auditoria", tags=["Auditoria"])


@router.get("/")
def listar_logs_auditoria(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin),
    tabela: Optional[str] = Query(None, description="Filtrar por tabela afetada"),
    acao: Optional[str] = Query(None, description="Filtrar por acao"),
    usuario_id: Optional[int] = Query(None, description="Filtrar por usuario"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    query = db.query(models.LogAuditoria)

    if tabela:
        query = query.filter(models.LogAuditoria.tabela_afetada == tabela)
    if acao:
        query = query.filter(models.LogAuditoria.acao == acao)
    if usuario_id:
        query = query.filter(models.LogAuditoria.usuario_id == usuario_id)

    logs = query.order_by(models.LogAuditoria.data_hora.desc()).offset(offset).limit(limit).all()
    resultado = []

    for log in logs:
        usuario_nome = None
        usuario_codigo = None

        usuario_sistema = None
        if log.usuario_id:
            usuario_sistema = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.id == log.usuario_id).first()

        if usuario_sistema:
            usuario_nome = usuario_sistema.nome
            usuario_codigo = usuario_sistema.codigo
        elif log.usuario_id:
            usuario_legado = db.query(models.Usuario).filter(models.Usuario.id == log.usuario_id).first()
            if usuario_legado:
                usuario_nome = usuario_legado.nome

        resultado.append(
            {
                "id": log.id,
                "usuario_id": log.usuario_id,
                "usuario_nome": usuario_nome,
                "usuario_codigo": usuario_codigo,
                "acao": log.acao,
                "tabela_afetada": log.tabela_afetada,
                "registro_id": log.registro_id,
                "dados_anteriores": log.dados_anteriores,
                "dados_novos": log.dados_novos,
                "ip_origem": log.ip_origem,
                "data_hora": log.data_hora.isoformat() if log.data_hora else None,
            }
        )

    return resultado
