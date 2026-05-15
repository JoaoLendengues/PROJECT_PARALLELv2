from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.audit import get_request_user, model_to_dict, registrar_log_auditoria
from app.database import get_db

router = APIRouter(prefix="/api/movimentacoes", tags=["Movimentacoes"])


def _movimentacao_to_response(db: Session, movimentacao: models.Movimentacao):
    material = db.query(models.Material).filter(models.Material.id == movimentacao.material_id).first()
    usuario = None
    if movimentacao.usuario_id:
        usuario = db.query(models.Usuario).filter(models.Usuario.id == movimentacao.usuario_id).first()

    return {
        **{key: getattr(movimentacao, key) for key in movimentacao.__dict__.keys() if not key.startswith("_")},
        "material_nome": material.nome if material else None,
        "usuario_nome": usuario.nome if usuario else None,
    }


@router.get("/", response_model=List[schemas.MovimentacaoReponse])
def listar_movimentacoes(
    db: Session = Depends(get_db),
    material_id: Optional[int] = Query(None, description="Filtrar por material"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo (entrada/saida)"),
    empresa: Optional[str] = Query(None, description="Filtrar por empresa"),
    data_inicio: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    data_fim: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Lista todas as movimentacoes com filtros opcionais."""
    query = db.query(models.Movimentacao)

    if material_id:
        query = query.filter(models.Movimentacao.material_id == material_id)

    if tipo:
        query = query.filter(models.Movimentacao.tipo == tipo)

    if empresa:
        query = query.filter(models.Movimentacao.empresa == empresa)

    if data_inicio:
        query = query.filter(models.Movimentacao.data_hora >= data_inicio)

    if data_fim:
        query = query.filter(models.Movimentacao.data_hora <= f"{data_fim} 23:59:59")

    movimentacoes = (
        query.order_by(models.Movimentacao.data_hora.desc()).offset(offset).limit(limit).all()
    )
    return [_movimentacao_to_response(db, mov) for mov in movimentacoes]


@router.get("/{movimentacao_id}", response_model=schemas.MovimentacaoReponse)
def obter_movimentacao(movimentacao_id: int, db: Session = Depends(get_db)):
    """Obtem uma movimentacao especifica pelo ID."""
    movimentacao = (
        db.query(models.Movimentacao).filter(models.Movimentacao.id == movimentacao_id).first()
    )

    if not movimentacao:
        raise HTTPException(status_code=404, detail="Movimentacao nao encontrada")

    return _movimentacao_to_response(db, movimentacao)


@router.post("/", response_model=schemas.MovimentacaoReponse, status_code=201)
def criar_movimentacao(
    movimentacao: schemas.MovimentacaoCreate,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
    request: Request = None,
    usuario_id: int = Query(1, description="ID do usuario legado"),
):
    """Registra uma movimentacao de entrada ou saida."""
    material = db.query(models.Material).filter(models.Material.id == movimentacao.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material nao encontrado")

    if movimentacao.tipo not in ["entrada", "saida"]:
        raise HTTPException(status_code=400, detail='Tipo invalido. Use "entrada" ou "saida"')

    if movimentacao.tipo == "saida" and material.quantidade < movimentacao.quantidade:
        raise HTTPException(
            status_code=400,
            detail=f"Estoque insuficiente. Disponivel: {material.quantidade}",
        )

    dados_movimentacao = movimentacao.model_dump()
    dados_movimentacao["usuario_id"] = usuario_id
    dados_movimentacao["ip_origem"] = dados_movimentacao.get("ip_origem") or "127.0.0.1"

    estoque_antes = material.quantidade
    nova_movimentacao = models.Movimentacao(**dados_movimentacao)
    db.add(nova_movimentacao)

    if movimentacao.tipo == "entrada":
        material.quantidade += movimentacao.quantidade
    else:
        material.quantidade -= movimentacao.quantidade

    db.commit()
    db.refresh(nova_movimentacao)

    try:
        registrar_log_auditoria(
            db,
            usuario=current_user,
            acao="CREATE",
            tabela_afetada="movimentacoes",
            registro_id=nova_movimentacao.id,
            dados_novos={
                **model_to_dict(nova_movimentacao),
                "material_nome": material.nome,
                "estoque_antes": estoque_antes,
                "estoque_depois": material.quantidade,
                "confirmacao_senha": True,
            },
            request=request,
            ip_origem=dados_movimentacao["ip_origem"],
        )
        db.commit()
    except Exception as log_error:
        print(f"Erro ao registrar log de movimentacao: {log_error}")

    return _movimentacao_to_response(db, nova_movimentacao)


@router.put("/{movimentacao_id}", response_model=schemas.MovimentacaoReponse)
def atualizar_movimentacao(
    movimentacao_id: int,
    movimentacao: schemas.MovimentacaoUpdate,
    db: Session = Depends(get_db),
    request: Request = None,
):
    """Atualiza uma movimentacao existente sem mexer no estoque."""
    movimentacao_existente = (
        db.query(models.Movimentacao).filter(models.Movimentacao.id == movimentacao_id).first()
    )

    if not movimentacao_existente:
        raise HTTPException(status_code=404, detail="Movimentacao nao encontrada")

    usuario_auditoria = get_request_user(request, db)
    dados_anteriores = model_to_dict(movimentacao_existente)
    update_data = movimentacao.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(movimentacao_existente, field, value)

    db.commit()
    db.refresh(movimentacao_existente)
    try:
        registrar_log_auditoria(
            db,
            usuario=usuario_auditoria,
            acao="UPDATE",
            tabela_afetada="movimentacoes",
            registro_id=movimentacao_existente.id,
            dados_anteriores=dados_anteriores,
            dados_novos=model_to_dict(movimentacao_existente),
            request=request,
        )
        db.commit()
    except Exception as log_error:
        print(f"Erro ao registrar log de auditoria da movimentacao: {log_error}")
    return _movimentacao_to_response(db, movimentacao_existente)


@router.delete("/{movimentacao_id}")
def deletar_movimentacao(
    movimentacao_id: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin),
    request: Request = None,
):
    """Remove uma movimentacao sem reverter estoque. Apenas administradores."""
    movimentacao = (
        db.query(models.Movimentacao).filter(models.Movimentacao.id == movimentacao_id).first()
    )

    if not movimentacao:
        raise HTTPException(status_code=404, detail="Movimentacao nao encontrada")

    try:
        registrar_log_auditoria(
            db,
            usuario=current_user,
            acao="DELETE",
            tabela_afetada="movimentacoes",
            registro_id=movimentacao_id,
            dados_anteriores=model_to_dict(movimentacao),
            request=request,
        )
    except Exception as log_error:
        print(f"Erro ao criar log de auditoria: {log_error}")

    db.delete(movimentacao)
    db.commit()
    return {"message": "Movimentacao deletada com sucesso"}


@router.get("/resumo/por-periodo")
def resumo_por_periodo(
    db: Session = Depends(get_db),
    data_inicio: str = Query(..., description="Data inicial (YYYY-MM-DD)"),
    data_fim: str = Query(..., description="Data final (YYYY-MM-DD)"),
    empresa: Optional[str] = Query(None, description="Filtrar por empresa"),
):
    """Retorna resumo de movimentacoes por periodo."""
    query = db.query(models.Movimentacao).filter(
        models.Movimentacao.data_hora >= data_inicio,
        models.Movimentacao.data_hora <= f"{data_fim} 23:59:59",
    )

    if empresa:
        query = query.filter(models.Movimentacao.empresa == empresa)

    movimentacoes = query.all()
    total_entradas = sum(m.quantidade for m in movimentacoes if m.tipo == "entrada")
    total_saidas = sum(m.quantidade for m in movimentacoes if m.tipo == "saida")

    return {
        "periodo": {"inicio": data_inicio, "fim": data_fim},
        "total_movimentacoes": len(movimentacoes),
        "total_entradas": total_entradas,
        "total_saidas": total_saidas,
        "saldo": total_entradas - total_saidas,
        "movimentacoes": [
            {
                "id": m.id,
                "material_id": m.material_id,
                "tipo": m.tipo,
                "quantidade": m.quantidade,
                "empresa": m.empresa,
                "data_hora": m.data_hora.isoformat(),
            }
            for m in movimentacoes
        ],
    }
