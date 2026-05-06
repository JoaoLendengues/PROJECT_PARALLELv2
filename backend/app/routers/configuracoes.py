import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import auth, models
from app.audit import registrar_log_auditoria
from app.database import get_db

router = APIRouter(prefix="/api/configuracoes", tags=["Configuracoes"])


class ItemListaRequest(BaseModel):
    nome: str


def _get_lista(db: Session, chave: str, default: List[str]) -> List[str]:
    config = db.query(models.Configuracao).filter(models.Configuracao.chave == chave).first()
    if config and config.valor:
        try:
            return json.loads(config.valor)
        except Exception:
            return default
    return default


def _salvar_lista(db: Session, chave: str, lista: List[str], commit: bool = True) -> bool:
    config = db.query(models.Configuracao).filter(models.Configuracao.chave == chave).first()
    valor_json = json.dumps(lista, ensure_ascii=False)

    if config:
        config.valor = valor_json
    else:
        db.add(models.Configuracao(chave=chave, valor=valor_json))

    if commit:
        db.commit()
    return True


def _renomear_empresa_em_registros(db: Session, nome_atual: str, novo_nome: str) -> None:
    campos_empresa = (
        (models.Usuario, models.Usuario.empresa),
        (models.Material, models.Material.empresa),
        (models.Maquina, models.Maquina.empresa),
        (models.Movimentacao, models.Movimentacao.empresa),
        (models.Pedido, models.Pedido.empresa),
        (models.UsuarioSistema, models.UsuarioSistema.empresa),
        (models.Colaborador, models.Colaborador.empresa),
        (models.Demanda, models.Demanda.empresa),
    )

    for model, coluna in campos_empresa:
        db.query(model).filter(coluna == nome_atual).update(
            {coluna: novo_nome},
            synchronize_session=False,
        )


def _renomear_categoria_em_registros(db: Session, nome_atual: str, novo_nome: str) -> None:
    db.query(models.Material).filter(models.Material.categoria == nome_atual).update(
        {models.Material.categoria: novo_nome},
        synchronize_session=False,
    )


def _registrar_lista_auditoria(
    db: Session,
    current_user: models.UsuarioSistema,
    acao: str,
    tabela_afetada: str,
    http_request: Request,
    dados_anteriores: dict = None,
    dados_novos: dict = None,
):
    registrar_log_auditoria(
        db,
        current_user,
        acao=acao,
        tabela_afetada=tabela_afetada,
        dados_anteriores=dados_anteriores,
        dados_novos=dados_novos,
        request=http_request,
    )


@router.get("/empresas", response_model=List[str])
def get_empresas(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
):
    return _get_lista(db, "empresas", ["Matriz", "Filial 1", "Filial 2", "Filial 3"])


@router.post("/empresas")
def add_empresa(
    request: ItemListaRequest,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin),
    http_request: Request = None,
):
    if not request.nome or not request.nome.strip():
        raise HTTPException(status_code=400, detail="Nome da empresa nao pode estar vazio")

    empresas = _get_lista(db, "empresas", [])
    nome_limpo = request.nome.strip()

    if nome_limpo in empresas:
        raise HTTPException(status_code=400, detail="Empresa ja existe")

    empresas.append(nome_limpo)
    empresas.sort()
    _salvar_lista(db, "empresas", empresas, commit=False)
    _registrar_lista_auditoria(
        db,
        current_user,
        acao="CREATE",
        tabela_afetada="configuracoes_empresas",
        http_request=http_request,
        dados_novos={"nome": nome_limpo, "lista_resultante": empresas},
    )
    db.commit()

    return {"success": True, "message": f"Empresa '{nome_limpo}' adicionada", "lista": empresas}


@router.put("/empresas/{nome_atual}")
def update_empresa(
    nome_atual: str,
    request: ItemListaRequest,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin),
    http_request: Request = None,
):
    if not request.nome or not request.nome.strip():
        raise HTTPException(status_code=400, detail="Nome da empresa nao pode estar vazio")

    empresas = _get_lista(db, "empresas", [])
    if nome_atual not in empresas:
        raise HTTPException(status_code=404, detail="Empresa nao encontrada")

    novo_nome = request.nome.strip()
    if novo_nome != nome_atual and novo_nome in empresas:
        raise HTTPException(status_code=400, detail="Empresa ja existe")

    if novo_nome == nome_atual:
        return {"success": True, "message": "Nenhuma alteracao realizada", "lista": empresas}

    empresas_antes = list(empresas)
    empresas = [novo_nome if empresa == nome_atual else empresa for empresa in empresas]
    empresas.sort()

    _renomear_empresa_em_registros(db, nome_atual, novo_nome)
    _salvar_lista(db, "empresas", empresas, commit=False)

    empresa_padrao = db.query(models.Configuracao).filter(models.Configuracao.chave == "empresa_padrao").first()
    if empresa_padrao and empresa_padrao.valor == nome_atual:
        empresa_padrao.valor = novo_nome

    _registrar_lista_auditoria(
        db,
        current_user,
        acao="UPDATE",
        tabela_afetada="configuracoes_empresas",
        http_request=http_request,
        dados_anteriores={"nome": nome_atual, "lista_anterior": empresas_antes},
        dados_novos={"nome": novo_nome, "lista_resultante": empresas},
    )
    db.commit()

    return {"success": True, "message": f"Empresa '{nome_atual}' atualizada", "lista": empresas}


@router.delete("/empresas/{nome}")
def delete_empresa(
    nome: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin),
    http_request: Request = None,
):
    empresas = _get_lista(db, "empresas", [])
    if nome not in empresas:
        raise HTTPException(status_code=404, detail="Empresa nao encontrada")

    em_uso = any(
        (
            db.query(models.Material).filter(models.Material.empresa == nome).first(),
            db.query(models.Maquina).filter(models.Maquina.empresa == nome).first(),
            db.query(models.Movimentacao).filter(models.Movimentacao.empresa == nome).first(),
            db.query(models.Pedido).filter(models.Pedido.empresa == nome).first(),
            db.query(models.Usuario).filter(models.Usuario.empresa == nome).first(),
            db.query(models.UsuarioSistema).filter(models.UsuarioSistema.empresa == nome).first(),
            db.query(models.Colaborador).filter(models.Colaborador.empresa == nome).first(),
            db.query(models.Demanda).filter(models.Demanda.empresa == nome).first(),
        )
    )
    if em_uso:
        raise HTTPException(status_code=400, detail="Empresa esta sendo usada em outros registros do sistema")

    empresas_antes = list(empresas)
    empresas.remove(nome)
    _salvar_lista(db, "empresas", empresas, commit=False)
    _registrar_lista_auditoria(
        db,
        current_user,
        acao="DELETE",
        tabela_afetada="configuracoes_empresas",
        http_request=http_request,
        dados_anteriores={"nome": nome, "lista_anterior": empresas_antes},
        dados_novos={"lista_resultante": empresas},
    )
    db.commit()

    return {"success": True, "message": f"Empresa '{nome}' removida", "lista": empresas}


@router.get("/departamentos", response_model=List[str])
def get_departamentos(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
):
    return _get_lista(
        db,
        "departamentos",
        ["TI", "Administrativo", "Financeiro", "RH", "Comercial", "Marketing", "Logistica"],
    )


@router.post("/departamentos")
def add_departamento(
    request: ItemListaRequest,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin),
    http_request: Request = None,
):
    if not request.nome or not request.nome.strip():
        raise HTTPException(status_code=400, detail="Nome do departamento nao pode estar vazio")

    departamentos = _get_lista(db, "departamentos", [])
    nome_limpo = request.nome.strip()
    if nome_limpo in departamentos:
        raise HTTPException(status_code=400, detail="Departamento ja existe")

    departamentos.append(nome_limpo)
    departamentos.sort()
    _salvar_lista(db, "departamentos", departamentos, commit=False)
    _registrar_lista_auditoria(
        db,
        current_user,
        acao="CREATE",
        tabela_afetada="configuracoes_departamentos",
        http_request=http_request,
        dados_novos={"nome": nome_limpo, "lista_resultante": departamentos},
    )
    db.commit()

    return {"success": True, "message": f"Departamento '{nome_limpo}' adicionado", "lista": departamentos}


@router.delete("/departamentos/{nome}")
def delete_departamento(
    nome: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin),
    http_request: Request = None,
):
    departamentos = _get_lista(db, "departamentos", [])
    if nome not in departamentos:
        raise HTTPException(status_code=404, detail="Departamento nao encontrado")

    em_uso = any(
        (
            db.query(models.Maquina).filter(models.Maquina.departamento == nome).first(),
            db.query(models.Colaborador).filter(models.Colaborador.departamento == nome).first(),
            db.query(models.Pedido).filter(models.Pedido.departamento == nome).first(),
            db.query(models.Demanda).filter(models.Demanda.departamento == nome).first(),
        )
    )
    if em_uso:
        raise HTTPException(status_code=400, detail="Departamento esta sendo usado em outros registros do sistema")

    departamentos_antes = list(departamentos)
    departamentos.remove(nome)
    _salvar_lista(db, "departamentos", departamentos, commit=False)
    _registrar_lista_auditoria(
        db,
        current_user,
        acao="DELETE",
        tabela_afetada="configuracoes_departamentos",
        http_request=http_request,
        dados_anteriores={"nome": nome, "lista_anterior": departamentos_antes},
        dados_novos={"lista_resultante": departamentos},
    )
    db.commit()

    return {"success": True, "message": f"Departamento '{nome}' removido", "lista": departamentos}


@router.get("/categorias", response_model=List[str])
def get_categorias(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
):
    return _get_lista(
        db,
        "categorias",
        ["Perifericos", "Hardware", "Armazenamento", "Monitores", "Cabos", "Redes", "Consumiveis", "Softwares"],
    )


@router.post("/categorias")
def add_categoria(
    request: ItemListaRequest,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin),
    http_request: Request = None,
):
    if not request.nome or not request.nome.strip():
        raise HTTPException(status_code=400, detail="Nome da categoria nao pode estar vazio")

    categorias = _get_lista(db, "categorias", [])
    nome_limpo = request.nome.strip()
    if nome_limpo in categorias:
        raise HTTPException(status_code=400, detail="Categoria ja existe")

    categorias.append(nome_limpo)
    categorias.sort()
    _salvar_lista(db, "categorias", categorias, commit=False)
    _registrar_lista_auditoria(
        db,
        current_user,
        acao="CREATE",
        tabela_afetada="configuracoes_categorias",
        http_request=http_request,
        dados_novos={"nome": nome_limpo, "lista_resultante": categorias},
    )
    db.commit()

    return {"success": True, "message": f"Categoria '{nome_limpo}' adicionada", "lista": categorias}


@router.put("/categorias/{nome_atual}")
def update_categoria(
    nome_atual: str,
    request: ItemListaRequest,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin),
    http_request: Request = None,
):
    if not request.nome or not request.nome.strip():
        raise HTTPException(status_code=400, detail="Nome da categoria nao pode estar vazio")

    categorias = _get_lista(db, "categorias", [])
    if nome_atual not in categorias:
        raise HTTPException(status_code=404, detail="Categoria nao encontrada")

    novo_nome = request.nome.strip()
    if novo_nome != nome_atual and novo_nome in categorias:
        raise HTTPException(status_code=400, detail="Categoria ja existe")

    if novo_nome == nome_atual:
        return {"success": True, "message": "Nenhuma alteracao realizada", "lista": categorias}

    categorias_antes = list(categorias)
    categorias = [novo_nome if categoria == nome_atual else categoria for categoria in categorias]
    categorias.sort()

    _renomear_categoria_em_registros(db, nome_atual, novo_nome)
    _salvar_lista(db, "categorias", categorias, commit=False)
    _registrar_lista_auditoria(
        db,
        current_user,
        acao="UPDATE",
        tabela_afetada="configuracoes_categorias",
        http_request=http_request,
        dados_anteriores={"nome": nome_atual, "lista_anterior": categorias_antes},
        dados_novos={"nome": novo_nome, "lista_resultante": categorias},
    )
    db.commit()

    return {"success": True, "message": f"Categoria '{nome_atual}' atualizada", "lista": categorias}


@router.delete("/categorias/{nome}")
def delete_categoria(
    nome: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin),
    http_request: Request = None,
):
    categorias = _get_lista(db, "categorias", [])
    if nome not in categorias:
        raise HTTPException(status_code=404, detail="Categoria nao encontrada")

    material_uso = db.query(models.Material).filter(models.Material.categoria == nome).first()
    if material_uso:
        raise HTTPException(status_code=400, detail="Categoria esta sendo usada em materiais")

    categorias_antes = list(categorias)
    categorias.remove(nome)
    _salvar_lista(db, "categorias", categorias, commit=False)
    _registrar_lista_auditoria(
        db,
        current_user,
        acao="DELETE",
        tabela_afetada="configuracoes_categorias",
        http_request=http_request,
        dados_anteriores={"nome": nome, "lista_anterior": categorias_antes},
        dados_novos={"lista_resultante": categorias},
    )
    db.commit()

    return {"success": True, "message": f"Categoria '{nome}' removida", "lista": categorias}


@router.get("/")
def get_configuracoes(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user),
):
    configs = db.query(models.Configuracao).all()

    result = {}
    for config in configs:
        valor = config.valor
        if valor == "true":
            valor = True
        elif valor == "false":
            valor = False
        elif valor and valor.isdigit():
            valor = int(valor)
        result[config.chave] = valor

    defaults = {
        "tema": "Claro",
        "tamanho_fonte": "Padrao",
        "escala_interface": "Automatica",
        "navegacao_teclado": False,
        "alerta_estoque": 5,
        "alerta_estoque_critico": 2,
        "backup_automatico": True,
        "frequencia_backup": "Diario",
        "horario_backup": "02:00",
        "dias_retencao": 30,
        "notif_estoque_baixo": True,
        "notif_estoque_critico": True,
        "notif_manutencao": True,
        "notif_pedidos": True,
        "notif_demandas": True,
        "notif_movimentacoes": False,
        "valor_alto": 5000,
        "verificar_alertas_auto": True,
        "intervalo_verificacao": "5 minutos",
        "tempo_notificacao": "5 segundos",
        "modo_nao_perturbe": False,
        "empresa_padrao": "Matriz",
    }

    for key, default in defaults.items():
        if key not in result:
            result[key] = default

    return result


@router.post("/")
def salvar_configuracoes(
    configuracoes: dict,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin),
    http_request: Request = None,
):
    dados_anteriores = {}
    dados_novos = {}

    for chave, valor in configuracoes.items():
        if chave in ["empresas", "departamentos", "categorias"]:
            continue

        valor_str = str(valor).lower() if isinstance(valor, bool) else str(valor)
        existing = db.query(models.Configuracao).filter(models.Configuracao.chave == chave).first()
        valor_antigo = existing.valor if existing else None

        if existing:
            existing.valor = valor_str
        else:
            db.add(models.Configuracao(chave=chave, valor=valor_str))

        if valor_antigo != valor_str:
            dados_anteriores[chave] = valor_antigo
            dados_novos[chave] = valor

    if dados_novos:
        registrar_log_auditoria(
            db,
            current_user,
            acao="UPDATE",
            tabela_afetada="configuracoes",
            dados_anteriores=dados_anteriores,
            dados_novos=dados_novos,
            request=http_request,
        )

    db.commit()
    return {"message": "Configuracoes salvas com sucesso"}
