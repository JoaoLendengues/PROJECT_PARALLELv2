from datetime import date
from typing import List, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app import models, schemas
from app.audit import get_request_user, model_to_dict, registrar_log_auditoria
from app.database import get_db

router = APIRouter(prefix="/api/pedidos", tags=["Pedidos"])


def _pedido_to_response(db: Session, pedido: models.Pedido, material_nome_fallback: Optional[str] = None) -> dict:
    material_nome = material_nome_fallback

    if pedido.material_id:
        material = db.query(models.Material).filter(models.Material.id == pedido.material_id).first()
        if material:
            material_nome = material.nome

    data = {column.key: getattr(pedido, column.key) for column in pedido.__table__.columns}
    data["material_nome"] = material_nome
    return data


def _normalizar_link_compra(link_compra: Optional[str]) -> Optional[str]:
    if link_compra is None:
        return None

    valor = str(link_compra).strip()
    if not valor:
        return None

    if "://" not in valor:
        valor = f"https://{valor}"

    parsed = urlparse(valor)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=400, detail="Link de compra invalido")

    return parsed.geturl()


@router.get("/", response_model=List[schemas.PedidoResponse])
def listar_pedidos(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    solicitante: Optional[str] = Query(None, description="Filtrar por solicitante"),
    empresa: Optional[str] = Query(None, description="Filtrar por empresa"),
    departamento: Optional[str] = Query(None, description="Filtrar por departamento"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    query = db.query(models.Pedido)

    if status:
        query = query.filter(models.Pedido.status == status)

    if solicitante:
        query = query.filter(models.Pedido.solicitante.ilike(f"%{solicitante}%"))

    if empresa:
        query = query.filter(models.Pedido.empresa == empresa)

    if departamento:
        query = query.filter(models.Pedido.departamento == departamento)

    pedidos = query.order_by(models.Pedido.data_solicitacao.desc()).offset(offset).limit(limit).all()
    return [_pedido_to_response(db, pedido) for pedido in pedidos]


@router.get("/{pedido_id}", response_model=schemas.PedidoResponse)
def obter_pedido(pedido_id: int, db: Session = Depends(get_db)):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    return _pedido_to_response(db, pedido)


@router.post("/", response_model=schemas.PedidoResponse, status_code=201)
def criar_pedido(
    pedido: schemas.PedidoCreate,
    request: Request,
    db: Session = Depends(get_db),
    usuario_id: int = Query(1, description="ID do usuario legado vinculado ao pedido"),
):
    usuario_auditoria = get_request_user(request, db)
    material_id = pedido.material_id
    link_compra = _normalizar_link_compra(pedido.link_compra)

    if not material_id and pedido.material_nome:
        material_existente = db.query(models.Material).filter(
            models.Material.nome == pedido.material_nome,
            models.Material.empresa == pedido.empresa,
        ).first()

        if material_existente:
            material_id = material_existente.id
        else:
            novo_material = models.Material(
                nome=pedido.material_nome,
                descricao="Material solicitado em pedido",
                quantidade=0,
                categoria="Nao categorizado",
                empresa=pedido.empresa,
                status="ativo",
            )
            db.add(novo_material)
            db.flush()
            material_id = novo_material.id

    if not material_id:
        raise HTTPException(status_code=400, detail="Material nao identificado")

    material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material nao encontrado")

    novo_pedido = models.Pedido(
        material_id=material_id,
        quantidade=pedido.quantidade,
        solicitante=pedido.solicitante,
        empresa=pedido.empresa,
        departamento=pedido.departamento,
        status=pedido.status,
        observacao=pedido.observacao,
        link_compra=link_compra,
        usuario_id=usuario_id,
    )
    db.add(novo_pedido)
    db.flush()

    registrar_log_auditoria(
        db,
        usuario=usuario_auditoria,
        acao="CREATE",
        tabela_afetada="pedidos",
        registro_id=novo_pedido.id,
        dados_novos=model_to_dict(novo_pedido),
        request=request,
    )

    db.commit()
    db.refresh(novo_pedido)
    return _pedido_to_response(db, novo_pedido, material_nome_fallback=material.nome if material else pedido.material_nome)


@router.put("/{pedido_id}", response_model=schemas.PedidoResponse)
def atualizar_pedido(
    pedido_id: int,
    pedido: schemas.PedidoUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    pedido_existente = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido_existente:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    usuario_auditoria = get_request_user(request, db)
    dados_anteriores = model_to_dict(pedido_existente)
    update_data = pedido.model_dump(exclude_unset=True)

    if "link_compra" in update_data:
        update_data["link_compra"] = _normalizar_link_compra(update_data["link_compra"])

    for field, value in update_data.items():
        setattr(pedido_existente, field, value)

    registrar_log_auditoria(
        db,
        usuario=usuario_auditoria,
        acao="UPDATE",
        tabela_afetada="pedidos",
        registro_id=pedido_existente.id,
        dados_anteriores=dados_anteriores,
        dados_novos=model_to_dict(pedido_existente),
        request=request,
    )

    db.commit()
    db.refresh(pedido_existente)
    return _pedido_to_response(db, pedido_existente)


@router.put("/{pedido_id}/aprovar")
def aprovar_pedido(
    pedido_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    if pedido.status != "pendente":
        raise HTTPException(status_code=400, detail="Apenas pedidos pendentes podem ser aprovados")

    usuario_auditoria = get_request_user(request, db)
    dados_anteriores = model_to_dict(pedido)
    pedido.status = "aprovado"

    registrar_log_auditoria(
        db,
        usuario=usuario_auditoria,
        acao="APPROVE",
        tabela_afetada="pedidos",
        registro_id=pedido.id,
        dados_anteriores=dados_anteriores,
        dados_novos=model_to_dict(pedido),
        request=request,
    )

    db.commit()
    return {"message": "Pedido aprovado com sucesso", "pedido_id": pedido_id}


@router.put("/{pedido_id}/concluir")
def concluir_pedido(
    pedido_id: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario_id: int = Query(1, description="ID do usuario legado vinculado a movimentacao"),
):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    if pedido.status != "aprovado":
        raise HTTPException(
            status_code=400,
            detail=f"Apenas pedidos aprovados podem ser concluidos. Status atual: {pedido.status}",
        )

    material = db.query(models.Material).filter(models.Material.id == pedido.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material nao encontrado")

    usuario_auditoria = get_request_user(request, db)
    dados_anteriores = model_to_dict(pedido)

    material.quantidade += pedido.quantidade
    pedido.status = "concluido"
    pedido.data_conclusao = date.today()

    movimentacao = models.Movimentacao(
        material_id=pedido.material_id,
        tipo="entrada",
        quantidade=pedido.quantidade,
        usuario_id=usuario_id,
        empresa=pedido.empresa,
        destinatario=pedido.solicitante,
        observacao=f"Pedido de compra #{pedido_id} concluido - {pedido.observacao or ''}",
    )
    db.add(movimentacao)

    registrar_log_auditoria(
        db,
        usuario=usuario_auditoria,
        acao="COMPLETE",
        tabela_afetada="pedidos",
        registro_id=pedido.id,
        dados_anteriores=dados_anteriores,
        dados_novos=model_to_dict(pedido),
        request=request,
    )

    db.commit()

    return {
        "message": "Pedido de compra concluido com sucesso! Estoque atualizado.",
        "pedido_id": pedido_id,
        "material": material.nome,
        "quantidade_adicionada": pedido.quantidade,
        "novo_estoque": material.quantidade,
    }


@router.put("/{pedido_id}/cancelar")
def cancelar_pedido(
    pedido_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    if pedido.status not in ["pendente", "aprovado"]:
        raise HTTPException(status_code=400, detail="Apenas pedidos pendentes ou aprovados podem ser cancelados")

    usuario_auditoria = get_request_user(request, db)
    dados_anteriores = model_to_dict(pedido)
    pedido.status = "cancelado"

    registrar_log_auditoria(
        db,
        usuario=usuario_auditoria,
        acao="CANCEL",
        tabela_afetada="pedidos",
        registro_id=pedido.id,
        dados_anteriores=dados_anteriores,
        dados_novos=model_to_dict(pedido),
        request=request,
    )

    db.commit()
    return {"message": "Pedido cancelado com sucesso", "pedido_id": pedido_id}


@router.delete("/{pedido_id}")
def deletar_pedido(
    pedido_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    usuario_auditoria = get_request_user(request, db)
    dados_anteriores = model_to_dict(pedido)

    registrar_log_auditoria(
        db,
        usuario=usuario_auditoria,
        acao="DELETE",
        tabela_afetada="pedidos",
        registro_id=pedido.id,
        dados_anteriores=dados_anteriores,
        request=request,
    )

    db.delete(pedido)
    db.commit()
    return {"message": "Pedido deletado com sucesso"}


@router.get("/status/lista")
def listar_status():
    return {
        "status": [
            {"value": "pendente", "label": "Pendente", "color": "#f4a261"},
            {"value": "aprovado", "label": "Aprovado", "color": "#2a9d8f"},
            {"value": "concluido", "label": "Concluido", "color": "#2c7da0"},
            {"value": "cancelado", "label": "Cancelado", "color": "#e76f51"},
        ]
    }
