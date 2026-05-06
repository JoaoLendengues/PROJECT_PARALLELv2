from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable, Optional

from fastapi import Request
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app import models


def _serialize_audit_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(key): _serialize_audit_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_serialize_audit_value(item) for item in value]
    return value


def model_to_dict(instance: Any, include: Optional[Iterable[str]] = None, exclude: Optional[Iterable[str]] = None) -> dict:
    if instance is None:
        return {}

    include_set = set(include or [])
    exclude_set = set(exclude or [])
    values = {}

    for column in instance.__table__.columns:
        key = column.key
        if include_set and key not in include_set:
            continue
        if key in exclude_set:
            continue
        values[key] = _serialize_audit_value(getattr(instance, key))

    return values


def get_request_ip(request: Optional[Request] = None, fallback: str = "127.0.0.1") -> str:
    if request is None or request.client is None:
        return fallback
    return request.client.host or fallback


def get_request_user(request: Optional[Request], db: Session) -> Optional[models.UsuarioSistema]:
    if request is None:
        return None

    authorization = request.headers.get("Authorization", "").strip()
    if not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None

    try:
        from app.auth import ALGORITHM, SECRET_KEY

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        codigo = payload.get("sub")
        if not codigo:
            return None
    except JWTError:
        return None
    except Exception:
        return None

    return db.query(models.UsuarioSistema).filter(
        models.UsuarioSistema.codigo == codigo,
        models.UsuarioSistema.ativo == True
    ).first()


def _resolve_audit_user_id(db: Session, usuario: Optional[models.UsuarioSistema]) -> Optional[int]:
    if usuario is None:
        return None

    usuario_id = getattr(usuario, "id", None)
    if usuario_id is None:
        return None

    legacy_match = db.query(models.Usuario.id).filter(models.Usuario.id == usuario_id).first()
    return legacy_match[0] if legacy_match else None


def registrar_log_auditoria(
    db: Session,
    usuario: Optional[models.UsuarioSistema],
    acao: str,
    tabela_afetada: str,
    registro_id: Optional[int] = None,
    dados_anteriores: Optional[dict] = None,
    dados_novos: Optional[dict] = None,
    request: Optional[Request] = None,
    ip_origem: Optional[str] = None,
):
    log = models.LogAuditoria(
        usuario_id=_resolve_audit_user_id(db, usuario),
        acao=acao,
        tabela_afetada=tabela_afetada,
        registro_id=registro_id,
        dados_anteriores=_serialize_audit_value(dados_anteriores) if dados_anteriores is not None else None,
        dados_novos=_serialize_audit_value(dados_novos) if dados_novos is not None else None,
        ip_origem=ip_origem or get_request_ip(request),
    )
    db.add(log)
    return log
