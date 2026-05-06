import unicodedata
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.audit import model_to_dict, registrar_log_auditoria
from app.database import get_db

router = APIRouter(prefix="/api/demandas", tags=["Demandas"])

MANAGER_LEVELS = {"admin", "gerente"}
REQUESTER_LEVELS = {"solicitante"}
TI_CARGO_KEYWORDS = ("ti", "t.i", "tecnologia", "suporte", "informatica")


def _normalize_text(value) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text.strip().lower())
    return "".join(char for char in text if not unicodedata.combining(char))


def _normalize_access_level(value) -> str:
    aliases = {
        "administrador": "admin",
        "gerencia": "gerente",
        "manager": "gerente",
        "funcionario": "solicitante",
        "vendedor": "solicitante",
    }
    normalized = _normalize_text(value) or "usuario"
    return aliases.get(normalized, normalized)


def _is_ti_user(usuario: models.UsuarioSistema) -> bool:
    cargo = _normalize_text(getattr(usuario, "cargo", ""))
    return bool(cargo) and any(keyword in cargo for keyword in TI_CARGO_KEYWORDS)


def _is_requester(usuario: models.UsuarioSistema) -> bool:
    return _normalize_access_level(getattr(usuario, "nivel_acesso", None)) in REQUESTER_LEVELS


def _can_handle_demands(usuario: models.UsuarioSistema) -> bool:
    return _normalize_access_level(getattr(usuario, "nivel_acesso", None)) in MANAGER_LEVELS or _is_ti_user(usuario)


def _ensure_demanda_access(usuario: models.UsuarioSistema) -> None:
    if _is_requester(usuario) or _can_handle_demands(usuario):
        return
    raise HTTPException(status_code=403, detail="Acesso negado para demandas")


def _ensure_demanda_management(usuario: models.UsuarioSistema) -> None:
    if _can_handle_demands(usuario):
        return
    raise HTTPException(status_code=403, detail="Apenas gerencia, TI ou administradores podem gerir demandas")


def _get_accessible_demanda(db: Session, demanda_id: int, usuario: models.UsuarioSistema) -> models.Demanda:
    _ensure_demanda_access(usuario)
    query = db.query(models.Demanda).filter(models.Demanda.id == demanda_id)
    if _is_requester(usuario):
        query = query.filter(models.Demanda.criado_por == usuario.id)
    demanda = query.first()
    if not demanda:
        raise HTTPException(status_code=404, detail="Demanda nao encontrada")
    return demanda


def _destinatarios_nova_demanda(db: Session, demanda: models.Demanda) -> List[models.UsuarioSistema]:
    ativos = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.ativo == True).all()
    destinatarios = []
    vistos = set()

    for usuario in ativos:
        nivel = _normalize_access_level(usuario.nivel_acesso)
        mesmo_local = not demanda.empresa or not usuario.empresa or _normalize_text(usuario.empresa) == _normalize_text(demanda.empresa)

        deve_receber = (
            nivel == "admin"
            or (nivel == "gerente" and mesmo_local)
            or _is_ti_user(usuario)
        )

        if deve_receber and usuario.id not in vistos:
            vistos.add(usuario.id)
            destinatarios.append(usuario)

    return destinatarios


def _criar_notificacoes_demanda(db: Session, demanda: models.Demanda, origem: models.UsuarioSistema) -> None:
    titulo = "Nova demanda recebida"
    mensagem = f"{demanda.solicitante} abriu a demanda '{demanda.titulo}'."
    dados_extra = {
        "demanda_id": demanda.id,
        "empresa": demanda.empresa,
        "solicitante": demanda.solicitante,
        "status": demanda.status,
    }

    for usuario in _destinatarios_nova_demanda(db, demanda):
        if usuario.id == origem.id:
            continue
        db.add(
            models.Notificacao(
                usuario_id=usuario.id,
                tipo="demanda",
                titulo=titulo,
                mensagem=mensagem,
                prioridade=demanda.prioridade or "media",
                acao="show_demandas",
                acao_id=demanda.id,
                dados_extra=dados_extra,
            )
        )


def _notificar_solicitante(
    db: Session,
    demanda: models.Demanda,
    titulo: str,
    mensagem: str,
    prioridade: Optional[str] = None,
) -> None:
    if not demanda.criado_por:
        return

    db.add(
        models.Notificacao(
            usuario_id=demanda.criado_por,
            tipo="demanda",
            titulo=titulo,
            mensagem=mensagem,
            prioridade=prioridade or demanda.prioridade or "media",
            acao="show_demandas",
            acao_id=demanda.id,
            dados_extra={
                "demanda_id": demanda.id,
                "empresa": demanda.empresa,
                "solicitante": demanda.solicitante,
                "status": demanda.status,
                "responsavel": demanda.responsavel,
            },
        )
    )


def _aplicar_data_conclusao(demanda: models.Demanda) -> None:
    if demanda.status == "concluido":
        demanda.data_conclusao = date.today()
    elif demanda.status != "concluido":
        demanda.data_conclusao = None


@router.get("/", response_model=List[schemas.DemandaResponse])
def listar_demandas(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    prioridade: Optional[str] = Query(None, description="Filtrar por prioridade"),
    urgencia: Optional[str] = Query(None, description="Filtrar por urgencia"),
    empresa: Optional[str] = Query(None, description="Filtrar por empresa"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Lista demandas visiveis para o usuario atual."""
    _ensure_demanda_access(current_user)

    query = db.query(models.Demanda)

    if _is_requester(current_user):
        query = query.filter(models.Demanda.criado_por == current_user.id)

    if status:
        query = query.filter(models.Demanda.status == status)

    if prioridade:
        query = query.filter(models.Demanda.prioridade == prioridade)

    if urgencia:
        query = query.filter(models.Demanda.urgencia == urgencia)

    if empresa:
        query = query.filter(models.Demanda.empresa == empresa)

    return (
        query.order_by(models.Demanda.data_abertura.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/{demanda_id}", response_model=schemas.DemandaResponse)
def obter_demanda(
    demanda_id: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
):
    """Obtem uma demanda especifica respeitando o perfil do usuario."""
    return _get_accessible_demanda(db, demanda_id, current_user)


@router.post("/", response_model=schemas.DemandaResponse, status_code=201)
def criar_demanda(
    demanda: schemas.DemandaCreate,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
    request: Request = None,
):
    """Cria uma nova demanda."""
    _ensure_demanda_access(current_user)

    dados = demanda.model_dump()

    if _is_requester(current_user):
        dados["solicitante"] = current_user.nome
        dados["empresa"] = current_user.empresa or dados.get("empresa")
        dados["status"] = "aberto"
        dados["responsavel"] = None

    nova_demanda = models.Demanda(**dados, criado_por=current_user.id)
    db.add(nova_demanda)
    db.flush()

    registrar_log_auditoria(
        db,
        current_user,
        acao="CREATE",
        tabela_afetada="demandas",
        registro_id=nova_demanda.id,
        dados_novos=model_to_dict(nova_demanda),
        request=request,
    )

    _criar_notificacoes_demanda(db, nova_demanda, current_user)
    db.commit()
    db.refresh(nova_demanda)
    return nova_demanda


@router.put("/{demanda_id}", response_model=schemas.DemandaResponse)
def atualizar_demanda(
    demanda_id: int,
    demanda: schemas.DemandaUpdate,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
    request: Request = None,
):
    """Atualiza uma demanda."""
    _ensure_demanda_management(current_user)
    demanda_existente = _get_accessible_demanda(db, demanda_id, current_user)
    dados_anteriores = model_to_dict(demanda_existente)

    update_data = demanda.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(demanda_existente, field, value)

    _aplicar_data_conclusao(demanda_existente)

    registrar_log_auditoria(
        db,
        current_user,
        acao="UPDATE",
        tabela_afetada="demandas",
        registro_id=demanda_existente.id,
        dados_anteriores=dados_anteriores,
        dados_novos=model_to_dict(demanda_existente),
        request=request,
    )

    db.commit()
    db.refresh(demanda_existente)
    return demanda_existente


@router.put("/{demanda_id}/assumir")
def assumir_demanda(
    demanda_id: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
    request: Request = None,
):
    """Atribui a demanda ao usuario atual."""
    _ensure_demanda_management(current_user)
    demanda = _get_accessible_demanda(db, demanda_id, current_user)

    if demanda.status in {"concluido", "cancelado"}:
        raise HTTPException(status_code=400, detail="Nao e possivel assumir uma demanda encerrada")

    responsavel_atual = (demanda.responsavel or "").strip()
    if responsavel_atual and _normalize_text(responsavel_atual) != _normalize_text(current_user.nome):
        raise HTTPException(status_code=409, detail="Esta demanda ja foi assumida por outro usuario")

    dados_anteriores = model_to_dict(demanda)
    demanda.responsavel = current_user.nome
    if demanda.status == "aberto":
        demanda.status = "andamento"

    registrar_log_auditoria(
        db,
        current_user,
        acao="ASSIGN",
        tabela_afetada="demandas",
        registro_id=demanda.id,
        dados_anteriores=dados_anteriores,
        dados_novos=model_to_dict(demanda),
        request=request,
    )

    if demanda.criado_por and demanda.criado_por != current_user.id:
        _notificar_solicitante(
            db,
            demanda,
            titulo="Sua demanda foi assumida",
            mensagem=f"{current_user.nome} assumiu a demanda '{demanda.titulo}'.",
            prioridade="media",
        )

    db.commit()
    return {"message": "Demanda assumida com sucesso"}


@router.put("/{demanda_id}/concluir")
def concluir_demanda(
    demanda_id: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
    request: Request = None,
):
    """Conclui uma demanda."""
    _ensure_demanda_management(current_user)
    demanda = _get_accessible_demanda(db, demanda_id, current_user)
    dados_anteriores = model_to_dict(demanda)

    demanda.status = "concluido"
    demanda.data_conclusao = date.today()
    if not demanda.responsavel:
        demanda.responsavel = current_user.nome

    registrar_log_auditoria(
        db,
        current_user,
        acao="COMPLETE",
        tabela_afetada="demandas",
        registro_id=demanda.id,
        dados_anteriores=dados_anteriores,
        dados_novos=model_to_dict(demanda),
        request=request,
    )

    if demanda.criado_por and demanda.criado_por != current_user.id:
        _notificar_solicitante(
            db,
            demanda,
            titulo="Sua demanda foi concluida",
            mensagem=f"A demanda '{demanda.titulo}' foi concluida por {current_user.nome}.",
            prioridade="baixa",
        )

    db.commit()
    return {"message": "Demanda concluida com sucesso"}


@router.put("/{demanda_id}/cancelar")
def cancelar_demanda(
    demanda_id: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
    request: Request = None,
):
    """Cancela uma demanda."""
    _ensure_demanda_management(current_user)
    demanda = _get_accessible_demanda(db, demanda_id, current_user)
    dados_anteriores = model_to_dict(demanda)

    demanda.status = "cancelado"
    demanda.data_conclusao = None

    registrar_log_auditoria(
        db,
        current_user,
        acao="CANCEL",
        tabela_afetada="demandas",
        registro_id=demanda.id,
        dados_anteriores=dados_anteriores,
        dados_novos=model_to_dict(demanda),
        request=request,
    )

    if demanda.criado_por and demanda.criado_por != current_user.id:
        _notificar_solicitante(
            db,
            demanda,
            titulo="Sua demanda foi cancelada",
            mensagem=f"A demanda '{demanda.titulo}' foi cancelada por {current_user.nome}.",
            prioridade="media",
        )

    db.commit()
    return {"message": "Demanda cancelada com sucesso"}


@router.delete("/{demanda_id}")
def deletar_demanda(
    demanda_id: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
    request: Request = None,
):
    """Remove uma demanda."""
    if _normalize_access_level(current_user.nivel_acesso) != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem deletar demandas")

    demanda = _get_accessible_demanda(db, demanda_id, current_user)
    dados_anteriores = model_to_dict(demanda)

    registrar_log_auditoria(
        db,
        current_user,
        acao="DELETE",
        tabela_afetada="demandas",
        registro_id=demanda.id,
        dados_anteriores=dados_anteriores,
        request=request,
    )

    db.delete(demanda)
    db.commit()
    return {"message": "Demanda deletada com sucesso"}


@router.get("/status/lista")
def listar_status():
    """Lista todos os status de demanda."""
    return {
        "status": [
            {"value": "aberto", "label": "Aberto", "color": "#f4a261"},
            {"value": "andamento", "label": "Em Andamento", "color": "#2a9d8f"},
            {"value": "concluido", "label": "Concluido", "color": "#2c7da0"},
            {"value": "cancelado", "label": "Cancelado", "color": "#e76f51"},
        ]
    }


@router.get("/prioridades/lista")
def listar_prioridades():
    """Lista todas as prioridades."""
    return {
        "prioridades": [
            {"value": "alta", "label": "Alta", "color": "#e76f51"},
            {"value": "media", "label": "Media", "color": "#f4a261"},
            {"value": "baixa", "label": "Baixa", "color": "#2a9d8f"},
        ]
    }


@router.get("/urgencias/lista")
def listar_urgencias():
    """Lista todas as urgencias."""
    return {
        "urgencias": [
            {"value": "alta", "label": "Alta", "color": "#e76f51"},
            {"value": "media", "label": "Media", "color": "#f4a261"},
            {"value": "baixa", "label": "Baixa", "color": "#2a9d8f"},
        ]
    }
