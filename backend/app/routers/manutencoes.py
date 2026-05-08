from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models, schemas
from app.audit import get_request_user, model_to_dict, registrar_log_auditoria
from app.database import get_db

router = APIRouter(prefix="/api/manutencoes", tags=["Manutencoes"])


def _manutencao_to_response(db: Session, manutencao: models.Manutencao) -> dict:
    maquina = db.query(models.Maquina).filter(models.Maquina.id == manutencao.maquina_id).first()
    return {
        **{key: getattr(manutencao, key) for key in manutencao.__dict__.keys() if not key.startswith("_")},
        "maquina_nome": maquina.nome if maquina else None,
    }


@router.get("/", response_model=List[schemas.ManutencaoResponse])
def listar_manutencoes(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    maquina_id: Optional[int] = Query(None, description="Filtrar por maquina"),
    empresa: Optional[str] = Query(None, description="Filtrar por empresa"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    query = db.query(models.Manutencao)

    if status:
        query = query.filter(models.Manutencao.status == status)

    if maquina_id:
        query = query.filter(models.Manutencao.maquina_id == maquina_id)

    if empresa:
        query = query.join(models.Maquina, models.Manutencao.maquina_id == models.Maquina.id).filter(
            models.Maquina.empresa == empresa
        )

    if tipo:
        query = query.filter(models.Manutencao.tipo == tipo)

    manutencoes = query.order_by(models.Manutencao.data_inicio.desc()).offset(offset).limit(limit).all()
    return [_manutencao_to_response(db, manutencao) for manutencao in manutencoes]


@router.get("/{manutencao_id}", response_model=schemas.ManutencaoResponse)
def obter_manutencao(manutencao_id: int, db: Session = Depends(get_db)):
    manutencao = db.query(models.Manutencao).filter(models.Manutencao.id == manutencao_id).first()

    if not manutencao:
        raise HTTPException(status_code=404, detail="Manutencao nao encontrada")

    return _manutencao_to_response(db, manutencao)


@router.post("/", response_model=schemas.ManutencaoResponse, status_code=201)
def criar_manutencao(
    manutencao: schemas.ManutencaoCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    maquina = db.query(models.Maquina).filter(models.Maquina.id == manutencao.maquina_id).first()
    if not maquina:
        raise HTTPException(status_code=404, detail="Maquina nao encontrada")

    usuario_auditoria = get_request_user(request, db)
    nova_manutencao = models.Manutencao(**manutencao.model_dump())
    db.add(nova_manutencao)
    db.flush()

    db.execute(
        text("UPDATE maquinas SET status = :status WHERE id = :id"),
        {"status": "manutencao", "id": manutencao.maquina_id},
    )

    dados_novos = model_to_dict(nova_manutencao)
    dados_novos["maquina_status_atualizado_para"] = "manutencao"
    dados_novos["maquina_id"] = maquina.id
    dados_novos["maquina_nome"] = maquina.nome
    registrar_log_auditoria(
        db,
        usuario=usuario_auditoria,
        acao="CREATE",
        tabela_afetada="manutencoes",
        registro_id=nova_manutencao.id,
        dados_novos=dados_novos,
        request=request,
    )

    db.commit()
    db.refresh(nova_manutencao)
    return _manutencao_to_response(db, nova_manutencao)


@router.put("/{manutencao_id}", response_model=schemas.ManutencaoResponse)
def atualizar_manutencao(
    manutencao_id: int,
    manutencao: schemas.ManutencaoUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    manutencao_existente = db.query(models.Manutencao).filter(models.Manutencao.id == manutencao_id).first()

    if not manutencao_existente:
        raise HTTPException(status_code=404, detail="Manutencao nao encontrada")

    usuario_auditoria = get_request_user(request, db)
    dados_anteriores = model_to_dict(manutencao_existente)
    update_data = manutencao.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(manutencao_existente, field, value)

    registrar_log_auditoria(
        db,
        usuario=usuario_auditoria,
        acao="UPDATE",
        tabela_afetada="manutencoes",
        registro_id=manutencao_existente.id,
        dados_anteriores=dados_anteriores,
        dados_novos=model_to_dict(manutencao_existente),
        request=request,
    )

    db.commit()
    db.refresh(manutencao_existente)
    return _manutencao_to_response(db, manutencao_existente)


@router.put("/{manutencao_id}/concluir")
def concluir_manutencao(
    manutencao_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    manutencao = db.query(models.Manutencao).filter(models.Manutencao.id == manutencao_id).first()

    if not manutencao:
        raise HTTPException(status_code=404, detail="Manutencao nao encontrada")

    if manutencao.status == "concluida":
        raise HTTPException(status_code=400, detail="Manutencao ja esta concluida")

    usuario_auditoria = get_request_user(request, db)
    dados_anteriores = model_to_dict(manutencao)

    manutencao.status = "concluida"
    manutencao.data_fim = date.today()

    maquina = db.query(models.Maquina).filter(models.Maquina.id == manutencao.maquina_id).first()
    if maquina:
        maquina.status = "ativo"

    dados_novos = model_to_dict(manutencao)
    if maquina:
        dados_novos["maquina_status_atualizado_para"] = maquina.status
        dados_novos["maquina_id"] = maquina.id
        dados_novos["maquina_nome"] = maquina.nome

    registrar_log_auditoria(
        db,
        usuario=usuario_auditoria,
        acao="COMPLETE",
        tabela_afetada="manutencoes",
        registro_id=manutencao.id,
        dados_anteriores=dados_anteriores,
        dados_novos=dados_novos,
        request=request,
    )

    db.commit()

    return {"message": "Manutencao concluida com sucesso", "manutencao_id": manutencao_id}


@router.delete("/{manutencao_id}")
def deletar_manutencao(
    manutencao_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    manutencao = db.query(models.Manutencao).filter(models.Manutencao.id == manutencao_id).first()

    if not manutencao:
        raise HTTPException(status_code=404, detail="Manutencao nao encontrada")

    usuario_auditoria = get_request_user(request, db)
    dados_anteriores = model_to_dict(manutencao)

    registrar_log_auditoria(
        db,
        usuario=usuario_auditoria,
        acao="DELETE",
        tabela_afetada="manutencoes",
        registro_id=manutencao.id,
        dados_anteriores=dados_anteriores,
        request=request,
    )

    db.delete(manutencao)
    db.commit()

    return {"message": "Manutencao deletada com sucesso"}


@router.get("/tipos/lista")
def listar_tipos():
    return {"tipos": ["preventiva", "corretiva", "emergencial"]}


@router.get("/status/lista")
def listar_status():
    return {"status": ["pendente", "andamento", "concluida", "cancelada"]}
