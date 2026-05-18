from datetime import datetime
import unicodedata
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.database import get_db

router = APIRouter(prefix="/api/notificacoes", tags=["Notificacoes"])

MANAGER_LEVELS = {"admin", "gerente"}
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


def _can_receive_admin_alerts(usuario: models.UsuarioSistema) -> bool:
    nivel = _normalize_access_level(getattr(usuario, "nivel_acesso", None))
    return nivel in MANAGER_LEVELS or _is_ti_user(usuario)


def _same_company(usuario: models.UsuarioSistema, empresa: Optional[str]) -> bool:
    if not empresa or not getattr(usuario, "empresa", None):
        return True
    return _normalize_text(usuario.empresa) == _normalize_text(empresa)


def _can_receive_company_alert(usuario: models.UsuarioSistema, empresa: Optional[str]) -> bool:
    nivel = _normalize_access_level(getattr(usuario, "nivel_acesso", None))
    if nivel == "admin" or _is_ti_user(usuario):
        return True
    return _same_company(usuario, empresa)


def _is_active_demanda_status(value) -> bool:
    normalized = _normalize_text(value)
    return normalized in {"aberto", "andamento", "em andamento", "em_andamento"}


def _is_active_material_status(value) -> bool:
    normalized = _normalize_text(value)
    return normalized in {"ativo", "ativa", ""}


def _is_pending_manutencao_status(value) -> bool:
    normalized = _normalize_text(value)
    return normalized in {"pendente", "andamento", "em andamento", "em_andamento"}


def _is_pending_pedido_status(value) -> bool:
    normalized = _normalize_text(value)
    return normalized in {"pendente", "pedente", "aguardando"}


def _normalize_priority_bucket(prioridade, urgencia) -> str:
    prioridade_norm = _normalize_text(prioridade)
    urgencia_norm = _normalize_text(urgencia)
    if "alta" in {prioridade_norm, urgencia_norm}:
        return "alta"
    if "media" in {prioridade_norm, urgencia_norm}:
        return "media"
    return "baixa"


def _config_value(db: Session, chave: str, default):
    config = db.query(models.Configuracao).filter(models.Configuracao.chave == chave).first()
    if not config or config.valor is None:
        return default

    valor = str(config.valor).strip()
    if isinstance(default, bool):
        return valor.lower() == "true"
    if isinstance(default, int):
        try:
            return int(valor)
        except ValueError:
            return default
    return valor


def _notificacao_existente(db: Session, usuario_id: int, tipo: str, acao_id: int) -> bool:
    return (
        db.query(models.Notificacao.id)
        .filter(
            models.Notificacao.usuario_id == usuario_id,
            models.Notificacao.tipo == tipo,
            models.Notificacao.acao_id == acao_id,
            models.Notificacao.status == "nao_lida",
        )
        .first()
        is not None
    )


def _alerta_suprimido(db: Session, usuario_id: int, tipo: str, acao_id: int) -> bool:
    return (
        db.query(models.NotificacaoSuprimida.id)
        .filter(
            models.NotificacaoSuprimida.usuario_id == usuario_id,
            models.NotificacaoSuprimida.tipo == tipo,
            models.NotificacaoSuprimida.acao_id == acao_id,
        )
        .first()
        is not None
    )


def _registrar_supressao_alerta(db: Session, usuario_id: int, tipo: str, acao_id: int) -> None:
    if _alerta_suprimido(db, usuario_id, tipo, acao_id):
        return

    db.add(
        models.NotificacaoSuprimida(
            usuario_id=usuario_id,
            tipo=tipo,
            acao_id=acao_id,
        )
    )


def _limpar_supressoes_inativas(db: Session, usuario_id: int, tipo: str, active_ids: set[int]) -> None:
    query = db.query(models.NotificacaoSuprimida).filter(
        models.NotificacaoSuprimida.usuario_id == usuario_id,
        models.NotificacaoSuprimida.tipo == tipo,
    )
    if active_ids:
        query = query.filter(models.NotificacaoSuprimida.acao_id.notin_(active_ids))
    suppressed = query.all()
    for entry in suppressed:
        db.delete(entry)


def _criar_notificacao(
    db: Session,
    usuario: models.UsuarioSistema,
    tipo: str,
    titulo: str,
    mensagem: str,
    prioridade: str,
    acao: str,
    acao_id: int,
    dados_extra: Optional[dict] = None,
) -> Optional[models.Notificacao]:
    if _notificacao_existente(db, usuario.id, tipo, acao_id):
        return None
    if _alerta_suprimido(db, usuario.id, tipo, acao_id):
        return None

    notificacao = models.Notificacao(
        usuario_id=usuario.id,
        tipo=tipo,
        titulo=titulo,
        mensagem=mensagem,
        prioridade=prioridade,
        acao=acao,
        acao_id=acao_id,
        dados_extra=dados_extra,
    )
    db.add(notificacao)
    db.flush()
    return notificacao


@router.get("/", response_model=List[schemas.NotificacaoResponse])
def listar_notificacoes(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
    status: Optional[str] = Query(None, description="Filtrar por status (nao_lida, lida, ignorada)"),
    prioridade: Optional[str] = Query(None, description="Filtrar por prioridade (alta, media, baixa)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Lista notificacoes do usuario atual."""
    query = db.query(models.Notificacao).filter(models.Notificacao.usuario_id == current_user.id)

    if status:
        query = query.filter(models.Notificacao.status == status)

    if prioridade:
        query = query.filter(models.Notificacao.prioridade == prioridade)

    return query.order_by(models.Notificacao.criado_em.desc()).offset(offset).limit(limit).all()


@router.get("/nao-lidas/count")
def contar_nao_lidas(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
):
    """Retorna a quantidade de notificacoes nao lidas."""
    count = (
        db.query(models.Notificacao)
        .filter(
            models.Notificacao.usuario_id == current_user.id,
            models.Notificacao.status == "nao_lida",
        )
        .count()
    )
    return {"count": count}


@router.post("/")
def criar_notificacao(
    notificacao: schemas.NotificacaoCreate,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
):
    """Cria uma nova notificacao para o usuario autenticado."""
    nova_notificacao = models.Notificacao(**notificacao.model_dump(), usuario_id=current_user.id)
    db.add(nova_notificacao)
    db.commit()
    db.refresh(nova_notificacao)
    return {"message": "Notificacao criada com sucesso", "id": nova_notificacao.id}


@router.post("/sincronizar-alertas")
def sincronizar_alertas(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
):
    """Materializa alertas administrativos pendentes para o usuario atual."""
    if not getattr(current_user, "ativo", True) or not _can_receive_admin_alerts(current_user):
        return {"created": 0, "details": {}}

    created = 0
    details = {
        "estoque_critico": 0,
        "estoque_baixo": 0,
        "manutencao": 0,
        "pedido": 0,
        "demanda": 0,
    }
    created_notifications = []

    notif_estoque_critico = _config_value(db, "notif_estoque_critico", True)
    notif_estoque_baixo = _config_value(db, "notif_estoque_baixo", True)
    notif_manutencao = _config_value(db, "notif_manutencao", True)
    notif_pedidos = _config_value(db, "notif_pedidos", True)
    notif_demandas = _config_value(db, "notif_demandas", True)
    alerta_estoque_critico = _config_value(db, "alerta_estoque_critico", 2)
    alerta_estoque = _config_value(db, "alerta_estoque", 5)

    if notif_estoque_critico or notif_estoque_baixo:
        materiais = db.query(models.Material).all()
        estoque_critico_ativos = set()
        estoque_baixo_ativos = set()
        for material in materiais:
            if not _is_active_material_status(material.status):
                continue
            if not _can_receive_company_alert(current_user, material.empresa):
                continue

            quantidade = int(material.quantidade or 0)

            if notif_estoque_critico and quantidade <= alerta_estoque_critico:
                estoque_critico_ativos.add(int(material.id))
                mensagem = (
                    f"{material.nome}\n"
                    f"Apenas {quantidade} unidades restantes!\n"
                    f"Limite critico: {alerta_estoque_critico} unidades"
                )
                if quantidade <= 0:
                    mensagem = (
                        f"{material.nome}\n"
                        "Sem estoque disponivel!\n"
                        f"Limite critico: {alerta_estoque_critico} unidades"
                    )
                notificacao = _criar_notificacao(
                    db,
                    current_user,
                    tipo="estoque_critico",
                    titulo="ESTOQUE CRITICO!",
                    mensagem=mensagem,
                    prioridade="alta",
                    acao="show_materiais",
                    acao_id=material.id,
                    dados_extra={"quantidade": quantidade, "limite": alerta_estoque_critico},
                )
                if notificacao:
                    created += 1
                    details["estoque_critico"] += 1
                    created_notifications.append(notificacao)
                continue

            if notif_estoque_baixo and quantidade <= alerta_estoque:
                estoque_baixo_ativos.add(int(material.id))
                notificacao = _criar_notificacao(
                    db,
                    current_user,
                    tipo="estoque_baixo",
                    titulo="ESTOQUE BAIXO",
                    mensagem=(
                        f"{material.nome}\n"
                        f"Estoque: {quantidade} unidades\n"
                        f"Limite de alerta: {alerta_estoque} unidades"
                    ),
                    prioridade="media",
                    acao="show_materiais",
                    acao_id=material.id,
                    dados_extra={"quantidade": quantidade, "limite": alerta_estoque},
                )
                if notificacao:
                    created += 1
                    details["estoque_baixo"] += 1
                    created_notifications.append(notificacao)
        _limpar_supressoes_inativas(db, current_user.id, "estoque_critico", estoque_critico_ativos)
        _limpar_supressoes_inativas(db, current_user.id, "estoque_baixo", estoque_baixo_ativos)

    if notif_manutencao:
        manutencoes = (
            db.query(models.Manutencao, models.Maquina)
            .join(models.Maquina, models.Manutencao.maquina_id == models.Maquina.id)
            .all()
        )
        manutencoes_ativas = set()
        for manutencao, maquina in manutencoes:
            if not _is_pending_manutencao_status(manutencao.status):
                continue
            if not _can_receive_company_alert(current_user, maquina.empresa):
                continue
            manutencoes_ativas.add(int(manutencao.id))

            dias_pendente = 0
            if manutencao.data_inicio:
                try:
                    dias_pendente = (datetime.now().date() - manutencao.data_inicio).days
                except Exception:
                    dias_pendente = 0

            mensagem = f"{maquina.nome}\n"
            if dias_pendente > 0:
                mensagem += f"Pendente ha {dias_pendente} dia(s)\n"
            mensagem += f"Descricao: {(manutencao.descricao or '')[:50]}"

            notificacao = _criar_notificacao(
                db,
                current_user,
                tipo="manutencao",
                titulo="MANUTENCAO PENDENTE!",
                mensagem=mensagem,
                prioridade="alta" if dias_pendente > 7 else "media",
                acao="show_manutencoes",
                acao_id=manutencao.id,
                dados_extra={"dias_pendente": dias_pendente, "empresa": maquina.empresa},
            )
            if notificacao:
                created += 1
                details["manutencao"] += 1
                created_notifications.append(notificacao)
        _limpar_supressoes_inativas(db, current_user.id, "manutencao", manutencoes_ativas)

    if notif_pedidos:
        pedidos = db.query(models.Pedido).all()
        pedidos_ativos = set()
        for pedido in pedidos:
            if not _is_pending_pedido_status(pedido.status):
                continue
            if not _can_receive_company_alert(current_user, pedido.empresa):
                continue
            pedidos_ativos.add(int(pedido.id))

            dias_atraso = 0
            if pedido.data_solicitacao:
                try:
                    dias_atraso = (datetime.now().date() - pedido.data_solicitacao).days
                except Exception:
                    dias_atraso = 0

            material_nome = "Material"
            if pedido.material_id:
                material = db.query(models.Material).filter(models.Material.id == pedido.material_id).first()
                if material:
                    material_nome = material.nome

            mensagem = f"{material_nome}\nQuantidade: {pedido.quantidade}\nSolicitante: {pedido.solicitante}"
            if dias_atraso > 0:
                mensagem += f"\nAguardando ha {dias_atraso} dia(s)"

            notificacao = _criar_notificacao(
                db,
                current_user,
                tipo="pedido",
                titulo="PEDIDO PENDENTE!",
                mensagem=mensagem,
                prioridade="alta" if dias_atraso > 3 else "media",
                acao="show_pedidos",
                acao_id=pedido.id,
                dados_extra={"dias_atraso": dias_atraso, "empresa": pedido.empresa},
            )
            if notificacao:
                created += 1
                details["pedido"] += 1
                created_notifications.append(notificacao)
        _limpar_supressoes_inativas(db, current_user.id, "pedido", pedidos_ativos)

    if notif_demandas:
        demandas = db.query(models.Demanda).all()
        demandas_ativas = set()
        for demanda in demandas:
            if not _is_active_demanda_status(demanda.status):
                continue
            if not _can_receive_company_alert(current_user, demanda.empresa):
                continue
            demandas_ativas.add(int(demanda.id))

            prioridade_notif = _normalize_priority_bucket(demanda.prioridade, demanda.urgencia)
            mensagem = (
                f"Protocolo: #{demanda.id}\n"
                f"Titulo: {(demanda.titulo or '')[:50]}\n"
                f"Solicitante: {demanda.solicitante}"
            )
            if demanda.urgencia:
                mensagem += f"\nUrgencia: {demanda.urgencia}"
            if demanda.status:
                mensagem += f"\nStatus: {demanda.status}"

            notificacao = _criar_notificacao(
                db,
                current_user,
                tipo="demanda",
                titulo=f"DEMANDA {prioridade_notif.upper()} PENDENTE!",
                mensagem=mensagem,
                prioridade=prioridade_notif,
                acao="show_demandas",
                acao_id=demanda.id,
                dados_extra={
                    "empresa": demanda.empresa,
                    "prioridade": demanda.prioridade,
                    "urgencia": demanda.urgencia,
                    "status": demanda.status,
                },
            )
            if notificacao:
                created += 1
                details["demanda"] += 1
                created_notifications.append(notificacao)
        _limpar_supressoes_inativas(db, current_user.id, "demanda", demandas_ativas)

    if created:
        db.commit()
    else:
        db.rollback()

    serialized_notifications = [
        {
            "id": notif.id,
            "usuario_id": notif.usuario_id,
            "tipo": notif.tipo,
            "titulo": notif.titulo,
            "mensagem": notif.mensagem,
            "prioridade": notif.prioridade,
            "status": notif.status,
            "acao": notif.acao,
            "acao_id": notif.acao_id,
            "dados_extra": notif.dados_extra,
            "criado_em": notif.criado_em.isoformat() if notif.criado_em else datetime.now().isoformat(),
            "lida_em": notif.lida_em.isoformat() if notif.lida_em else None,
        }
        for notif in created_notifications
    ]

    return {"created": created, "details": details, "notifications": serialized_notifications}


@router.put("/{notificacao_id}/marcar-lida")
def marcar_como_lida(
    notificacao_id: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
):
    """Marca uma notificacao como lida."""
    notificacao = (
        db.query(models.Notificacao)
        .filter(
            models.Notificacao.id == notificacao_id,
            models.Notificacao.usuario_id == current_user.id,
        )
        .first()
    )

    if not notificacao:
        raise HTTPException(status_code=404, detail="Notificacao nao encontrada")

    notificacao.status = "lida"
    notificacao.lida_em = datetime.now()
    db.commit()
    return {"message": "Notificacao marcada como lida"}


@router.put("/marcar-todas-lidas")
def marcar_todas_como_lidas(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
):
    """Marca todas as notificacoes do usuario como lidas."""
    (
        db.query(models.Notificacao)
        .filter(
            models.Notificacao.usuario_id == current_user.id,
            models.Notificacao.status == "nao_lida",
        )
        .update({"status": "lida", "lida_em": datetime.now()})
    )
    db.commit()
    return {"message": "Todas as notificacoes foram marcadas como lidas"}


@router.delete("/{notificacao_id}")
def deletar_notificacao(
    notificacao_id: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
):
    """Deleta uma notificacao."""
    notificacao = (
        db.query(models.Notificacao)
        .filter(
            models.Notificacao.id == notificacao_id,
            models.Notificacao.usuario_id == current_user.id,
        )
        .first()
    )

    if not notificacao:
        raise HTTPException(status_code=404, detail="Notificacao nao encontrada")

    alert_types = {"estoque_critico", "estoque_baixo", "manutencao", "pedido", "demanda"}
    if notificacao.tipo in alert_types and notificacao.acao_id is not None:
        _registrar_supressao_alerta(
            db,
            usuario_id=current_user.id,
            tipo=notificacao.tipo,
            acao_id=int(notificacao.acao_id),
        )

    db.delete(notificacao)
    db.commit()
    return {"message": "Notificacao deletada com sucesso"}


@router.delete("/limpar-antigas")
def limpar_notificacoes_antigas(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
    dias: int = Query(30, description="Idade em dias para manter"),
):
    """Remove notificacoes lidas mais antigas que X dias."""
    from datetime import timedelta

    data_limite = datetime.now() - timedelta(days=dias)
    resultado = (
        db.query(models.Notificacao)
        .filter(
            models.Notificacao.usuario_id == current_user.id,
            models.Notificacao.criado_em < data_limite,
            models.Notificacao.status == "lida",
        )
        .delete()
    )
    db.commit()
    return {"message": f"{resultado} notificacoes antigas removidas"}
