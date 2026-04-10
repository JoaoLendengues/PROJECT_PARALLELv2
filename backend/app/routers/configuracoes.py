from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.database import get_db
from app import models, auth
import json

router = APIRouter(prefix='/api/configuracoes', tags=['Configurações'])

# Schema para requisições
class ItemListaRequest(BaseModel):
    nome: str


def _get_lista(db: Session, chave: str, default: List[str]) -> List[str]:
    """Obtém uma lista do banco de dados"""
    config = db.query(models.Configuracao).filter(models.Configuracao.chave == chave).first()
    if config and config.valor:
        try:
            return json.loads(config.valor)
        except:
            return default
    return default


def _salvar_lista(db: Session, chave: str, lista: List[str]) -> bool:
    """Salva uma lista no banco de dados"""
    config = db.query(models.Configuracao).filter(models.Configuracao.chave == chave).first()
    valor_json = json.dumps(lista, ensure_ascii=False)
    
    if config:
        config.valor = valor_json
    else:
        config = models.Configuracao(chave=chave, valor=valor_json)
        db.add(config)
    
    db.commit()
    return True


# =====================================================
# EMPRESAS
# =====================================================

@router.get('/empresas', response_model=List[str])
def get_empresas(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Retorna lista de empresas"""
    return _get_lista(db, 'empresas', ["Matriz", "Filial 1", "Filial 2", "Filial 3"])


@router.post('/empresas')
def add_empresa(
    request: ItemListaRequest,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Adiciona uma nova empresa"""
    if not request.nome or not request.nome.strip():
        raise HTTPException(status_code=400, detail="Nome da empresa não pode estar vazio")
    
    empresas = _get_lista(db, 'empresas', [])
    nome_limpo = request.nome.strip()
    
    if nome_limpo in empresas:
        raise HTTPException(status_code=400, detail="Empresa já existe")
    
    empresas.append(nome_limpo)
    empresas.sort()
    _salvar_lista(db, 'empresas', empresas)
    
    return {"success": True, "message": f"Empresa '{nome_limpo}' adicionada", "lista": empresas}


@router.delete('/empresas/{nome}')
def delete_empresa(
    nome: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Remove uma empresa"""
    empresas = _get_lista(db, 'empresas', [])
    
    if nome not in empresas:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    
    # Verificar se está sendo usada
    material_uso = db.query(models.Material).filter(models.Material.empresa == nome).first()
    maquina_uso = db.query(models.Maquina).filter(models.Maquina.empresa == nome).first()
    
    if material_uso or maquina_uso:
        raise HTTPException(status_code=400, detail="Empresa está sendo usada em materiais ou máquinas")
    
    empresas.remove(nome)
    _salvar_lista(db, 'empresas', empresas)
    
    return {"success": True, "message": f"Empresa '{nome}' removida", "lista": empresas}


# =====================================================
# DEPARTAMENTOS
# =====================================================

@router.get('/departamentos', response_model=List[str])
def get_departamentos(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Retorna lista de departamentos"""
    return _get_lista(db, 'departamentos', ["TI", "Administrativo", "Financeiro", "RH", "Comercial", "Marketing", "Logística"])


@router.post('/departamentos')
def add_departamento(
    request: ItemListaRequest,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Adiciona um novo departamento"""
    if not request.nome or not request.nome.strip():
        raise HTTPException(status_code=400, detail="Nome do departamento não pode estar vazio")
    
    departamentos = _get_lista(db, 'departamentos', [])
    nome_limpo = request.nome.strip()
    
    if nome_limpo in departamentos:
        raise HTTPException(status_code=400, detail="Departamento já existe")
    
    departamentos.append(nome_limpo)
    departamentos.sort()
    _salvar_lista(db, 'departamentos', departamentos)
    
    return {"success": True, "message": f"Departamento '{nome_limpo}' adicionado", "lista": departamentos}


@router.delete('/departamentos/{nome}')
def delete_departamento(
    nome: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Remove um departamento"""
    departamentos = _get_lista(db, 'departamentos', [])
    
    if nome not in departamentos:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")
    
    # Verificar se está sendo usado
    maquina_uso = db.query(models.Maquina).filter(models.Maquina.departamento == nome).first()
    
    if maquina_uso:
        raise HTTPException(status_code=400, detail="Departamento está sendo usado em máquinas")
    
    departamentos.remove(nome)
    _salvar_lista(db, 'departamentos', departamentos)
    
    return {"success": True, "message": f"Departamento '{nome}' removido", "lista": departamentos}


# =====================================================
# CATEGORIAS
# =====================================================

@router.get('/categorias', response_model=List[str])
def get_categorias(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Retorna lista de categorias de materiais"""
    return _get_lista(db, 'categorias', ["Periféricos", "Hardware", "Armazenamento", "Monitores", "Cabos", "Redes", "Consumíveis", "Softwares"])


@router.post('/categorias')
def add_categoria(
    request: ItemListaRequest,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Adiciona uma nova categoria"""
    if not request.nome or not request.nome.strip():
        raise HTTPException(status_code=400, detail="Nome da categoria não pode estar vazio")
    
    categorias = _get_lista(db, 'categorias', [])
    nome_limpo = request.nome.strip()
    
    if nome_limpo in categorias:
        raise HTTPException(status_code=400, detail="Categoria já existe")
    
    categorias.append(nome_limpo)
    categorias.sort()
    _salvar_lista(db, 'categorias', categorias)
    
    return {"success": True, "message": f"Categoria '{nome_limpo}' adicionada", "lista": categorias}


@router.delete('/categorias/{nome}')
def delete_categoria(
    nome: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Remove uma categoria"""
    categorias = _get_lista(db, 'categorias', [])
    
    if nome not in categorias:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    # Verificar se está sendo usada
    material_uso = db.query(models.Material).filter(models.Material.categoria == nome).first()
    
    if material_uso:
        raise HTTPException(status_code=400, detail="Categoria está sendo usada em materiais")
    
    categorias.remove(nome)
    _salvar_lista(db, 'categorias', categorias)
    
    return {"success": True, "message": f"Categoria '{nome}' removida", "lista": categorias}

# =====================================================
# CONFIGURAÇÕES GERAIS DO SISTEMA
# =====================================================

@router.get('/')
def get_configuracoes(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.get_current_user)
):
    """Obtém todas as configurações gerais do sistema"""
    
    configs = db.query(models.Configuracao).all()
    
    result = {}
    for config in configs:
        valor = config.valor
        # Converter tipos quando possível
        if valor == 'true':
            valor = True
        elif valor == 'false':
            valor = False
        elif valor and valor.isdigit():
            valor = int(valor)
        result[config.chave] = valor
    
    # Valores padrão se não existirem
    defaults = {
        "alerta_estoque": 5,
        "alerta_estoque_critico": 2,
        "backup_automatico": True,
        "frequencia_backup": "Diário",
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
        "empresa_padrao": "Matriz"
    }
    
    for key, default in defaults.items():
        if key not in result:
            result[key] = default
    
    return result


@router.post('/')
def salvar_configuracoes(
    configuracoes: dict,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Salva as configurações gerais do sistema (apenas admin)"""
    
    for chave, valor in configuracoes.items():
        # Pular listas (empresas, departamentos, categorias) - já têm endpoints próprios
        if chave in ['empresas', 'departamentos', 'categorias']:
            continue
        
        # Converter para string para salvar
        if isinstance(valor, bool):
            valor_str = str(valor).lower()
        else:
            valor_str = str(valor)
        
        existing = db.query(models.Configuracao).filter(
            models.Configuracao.chave == chave
        ).first()
        
        if existing:
            existing.valor = valor_str
        else:
            nova_config = models.Configuracao(chave=chave, valor=valor_str)
            db.add(nova_config)
    
    db.commit()
    
    return {"message": "Configurações salvas com sucesso"}
