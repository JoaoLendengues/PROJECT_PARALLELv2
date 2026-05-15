from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.audit import model_to_dict, registrar_log_auditoria
from app.database import get_db

router = APIRouter(prefix="/api/usuarios", tags=["Usuarios do Sistema"])


def _count_active_admins(db: Session) -> int:
    return (
        db.query(models.UsuarioSistema)
        .filter(
            models.UsuarioSistema.nivel_acesso == "admin",
            models.UsuarioSistema.ativo == True,
        )
        .count()
    )


def _would_remove_admin_access(usuario: models.UsuarioSistema, update_data: dict) -> bool:
    if usuario.nivel_acesso != "admin" or not usuario.ativo:
        return False

    novo_nivel = update_data.get("nivel_acesso", usuario.nivel_acesso)
    novo_ativo = update_data.get("ativo", usuario.ativo)
    return novo_nivel != "admin" or not novo_ativo


@router.get("/", response_model=List[schemas.UsuarioSistemaResponse])
def listar_usuarios(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin),
    ativo: Optional[bool] = Query(None, description="Filtrar por ativo"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    query = db.query(models.UsuarioSistema)

    if ativo is not None:
        query = query.filter(models.UsuarioSistema.ativo == ativo)

    return query.order_by(models.UsuarioSistema.nome).offset(offset).limit(limit).all()


@router.get("/proximo-codigo")
def get_proximo_codigo(
    db: Session = Depends(get_db),
    admin: models.UsuarioSistema = Depends(auth.verificar_admin),
):
    usuarios = db.query(models.UsuarioSistema.codigo).all()

    max_codigo = 0
    for usuario in usuarios:
        try:
            codigo_int = int(str(usuario.codigo).strip())
        except (TypeError, ValueError):
            continue
        max_codigo = max(max_codigo, codigo_int)

    return {"proximo_codigo": str(max_codigo + 1)}


@router.get("/{usuario_id}", response_model=schemas.UsuarioSistemaResponse)
def obter_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    admin: models.UsuarioSistema = Depends(auth.verificar_admin),
):
    usuario = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    return usuario


@router.post("/", response_model=schemas.UsuarioSistemaResponse, status_code=201)
def criar_usuario(
    usuario: schemas.UsuarioSistemaCreate,
    db: Session = Depends(get_db),
    admin: models.UsuarioSistema = Depends(auth.verificar_admin),
    request: Request = None,
):
    existing = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.codigo == usuario.codigo).first()
    if existing:
        raise HTTPException(status_code=400, detail="Codigo de usuario ja existe")

    senha_padrao = "123456"
    novo_usuario = models.UsuarioSistema(
        codigo=usuario.codigo,
        nome=usuario.nome,
        senha_hash=auth.gerar_hash_senha(senha_padrao),
        cargo=usuario.cargo,
        empresa=usuario.empresa,
        nivel_acesso=usuario.nivel_acesso,
        primeiro_acesso=True,
        ativo=usuario.ativo,
    )
    db.add(novo_usuario)
    db.flush()
    registrar_log_auditoria(
        db,
        admin,
        acao="CREATE",
        tabela_afetada="usuarios_sistema",
        registro_id=novo_usuario.id,
        dados_novos=model_to_dict(novo_usuario, exclude={"senha_hash"}),
        request=request,
    )
    db.commit()
    db.refresh(novo_usuario)

    return novo_usuario


@router.put("/{usuario_id}", response_model=schemas.UsuarioSistemaResponse)
def atualizar_usuario(
    usuario_id: int,
    usuario: schemas.UsuarioSistemaUpdate,
    db: Session = Depends(get_db),
    admin: models.UsuarioSistema = Depends(auth.verificar_admin),
    request: Request = None,
):
    usuario_existente = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.id == usuario_id).first()
    if not usuario_existente:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    dados_anteriores = model_to_dict(usuario_existente, exclude={"senha_hash"})
    update_data = usuario.model_dump(exclude_unset=True)

    if admin.id == usuario_existente.id:
        if update_data.get("ativo") is False:
            raise HTTPException(status_code=400, detail="Voce nao pode desativar o proprio usuario.")
        if "nivel_acesso" in update_data and update_data.get("nivel_acesso") != "admin":
            raise HTTPException(status_code=400, detail="Voce nao pode rebaixar o proprio nivel de acesso.")

    if _would_remove_admin_access(usuario_existente, update_data) and _count_active_admins(db) <= 1:
        raise HTTPException(status_code=400, detail="Nao e possivel remover o ultimo administrador ativo.")

    for field, value in update_data.items():
        setattr(usuario_existente, field, value)

    registrar_log_auditoria(
        db,
        admin,
        acao="UPDATE",
        tabela_afetada="usuarios_sistema",
        registro_id=usuario_existente.id,
        dados_anteriores=dados_anteriores,
        dados_novos=model_to_dict(usuario_existente, exclude={"senha_hash"}),
        request=request,
    )
    db.commit()
    db.refresh(usuario_existente)

    return usuario_existente


@router.delete("/{usuario_id}")
def deletar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    admin: models.UsuarioSistema = Depends(auth.verificar_admin),
    request: Request = None,
):
    usuario = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    if admin.id == usuario.id:
        raise HTTPException(status_code=400, detail="Voce nao pode excluir o proprio usuario.")

    if usuario.nivel_acesso == "admin" and usuario.ativo and _count_active_admins(db) <= 1:
        raise HTTPException(status_code=400, detail="Nao e possivel excluir o ultimo administrador ativo.")

    registrar_log_auditoria(
        db,
        admin,
        acao="DELETE",
        tabela_afetada="usuarios_sistema",
        registro_id=usuario.id,
        dados_anteriores=model_to_dict(usuario, exclude={"senha_hash"}),
        request=request,
    )
    db.delete(usuario)
    db.commit()

    return {"message": "Usuario deletado com sucesso"}


@router.post("/{usuario_id}/resetar-senha")
def resetar_senha(
    usuario_id: int,
    db: Session = Depends(get_db),
    admin: models.UsuarioSistema = Depends(auth.verificar_admin),
    request: Request = None,
):
    usuario = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    senha_padrao = "123456"
    usuario.senha_hash = auth.gerar_hash_senha(senha_padrao)
    usuario.primeiro_acesso = True
    registrar_log_auditoria(
        db,
        admin,
        acao="PASSWORD_RESET",
        tabela_afetada="usuarios_sistema",
        registro_id=usuario.id,
        dados_novos={"codigo": usuario.codigo, "primeiro_acesso": True, "senha_padrao_restaurada": True},
        request=request,
    )
    db.commit()

    return {"message": f"Senha resetada para padrao: {senha_padrao}"}


@router.post("/{usuario_id}/alterar-senha")
def alterar_senha(
    usuario_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    admin: models.UsuarioSistema = Depends(auth.verificar_admin),
    request: Request = None,
):
    nova_senha = payload.get("nova_senha")
    if not nova_senha:
        raise HTTPException(status_code=400, detail="Nova senha nao fornecida")
    if len(nova_senha) < 6:
        raise HTTPException(status_code=400, detail="A senha deve ter no minimo 6 caracteres")

    usuario = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    usuario.senha_hash = auth.gerar_hash_senha(nova_senha)
    usuario.primeiro_acesso = False
    registrar_log_auditoria(
        db,
        admin,
        acao="PASSWORD_CHANGE",
        tabela_afetada="usuarios_sistema",
        registro_id=usuario.id,
        dados_novos={"codigo": usuario.codigo, "senha_alterada_por_admin": True, "primeiro_acesso": False},
        request=request,
    )
    db.commit()

    return {"message": "Senha alterada com sucesso"}
