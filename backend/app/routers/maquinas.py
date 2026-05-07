import platform
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix='/api/maquinas', tags=['Máquinas'])


def _latency_from_ping_output(output: str) -> Optional[int]:
    if not output:
        return None

    match = re.search(r'(?:time|tempo)[=<]\s*(\d+(?:[.,]\d+)?)\s*ms', output, re.IGNORECASE)
    if not match:
        return None

    value = match.group(1).replace(",", ".")
    try:
        return int(float(value))
    except ValueError:
        return None


def _monitor_machine(maquina: models.Maquina) -> dict:
    alvo = (maquina.ip_address or maquina.nome or "").strip()
    atualizado_em = datetime.now()

    if not alvo:
        return {
            "id": maquina.id,
            "nome": maquina.nome,
            "empresa": maquina.empresa,
            "departamento": maquina.departamento,
            "status": maquina.status,
            "mac_address": maquina.mac_address,
            "ip_address": maquina.ip_address,
            "alvo_monitoramento": None,
            "monitor_status": "nao_configurado",
            "monitor_label": "Sem alvo",
            "latencia_ms": None,
            "detalhe": "Cadastre um IP ou hostname para monitorar esta máquina.",
            "atualizado_em": atualizado_em,
        }

    sistema = platform.system().lower()
    timeout_ms = 1200
    comando = ["ping", "-n", "1", "-w", str(timeout_ms), alvo] if sistema == "windows" else [
        "ping", "-c", "1", "-W", str(max(1, timeout_ms // 1000)), alvo
    ]

    inicio = time.perf_counter()
    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        duracao_ms = int((time.perf_counter() - inicio) * 1000)
        output = "\n".join(part for part in (resultado.stdout, resultado.stderr) if part)

        if resultado.returncode == 0:
            latencia_ms = _latency_from_ping_output(output) or duracao_ms
            if latencia_ms < 20:
                label = "Excelente"
            elif latencia_ms < 80:
                label = "Online"
            elif latencia_ms < 180:
                label = "Oscilando"
            else:
                label = "Lento"
            detalhe = f"Resposta em {latencia_ms} ms"
            monitor_status = "online"
        else:
            latencia_ms = None
            label = "Offline"
            detalhe = "Sem resposta no ping"
            monitor_status = "offline"
    except Exception as exc:
        latencia_ms = None
        label = "Erro"
        detalhe = str(exc)
        monitor_status = "erro"

    return {
        "id": maquina.id,
        "nome": maquina.nome,
        "empresa": maquina.empresa,
        "departamento": maquina.departamento,
        "status": maquina.status,
        "mac_address": maquina.mac_address,
        "ip_address": maquina.ip_address,
        "alvo_monitoramento": alvo,
        "monitor_status": monitor_status,
        "monitor_label": label,
        "latencia_ms": latencia_ms,
        "detalhe": detalhe,
        "atualizado_em": atualizado_em,
    }


@router.get('/', response_model=List[schemas.MaquinaResponse])
def listar_maquinas(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description='Termo de busca'),
    empresa: Optional[str] = Query(None, description='Filtrar por empresa'),
    departamento: Optional[str] = Query(None, description='Filtrar por departamento'),
    status: Optional[str] = Query('ativo', description='Filtrar por status'),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Lista todas as máquinas com filtros opcionais"""
    print(f'🔎 GET /api/maquinas - status filter: {status}')

    query = db.query(models.Maquina)

    if search:
        query = query.filter(
            (models.Maquina.nome.ilike(f'%{search}%')) |
            (models.Maquina.modelo.ilike(f'%{search}%')) |
            (models.Maquina.ip_address.ilike(f'%{search}%')) |
            (models.Maquina.mac_address.ilike(f'%{search}%'))
        )

    if empresa:
        query = query.filter(models.Maquina.empresa == empresa)

    if departamento:
        query = query.filter(models.Maquina.departamento == departamento)

    if status:
        query = query.filter(models.Maquina.status == status)

    maquinas = query.order_by(models.Maquina.nome).offset(offset).limit(limit).all()

    print(f'🖥️ Encontradas {len(maquinas)} máquinas')

    return maquinas


@router.get('/monitoramento', response_model=List[schemas.MaquinaMonitoramentoResponse])
def monitorar_maquinas(
    db: Session = Depends(get_db),
    empresa: Optional[str] = Query(None, description='Filtrar por empresa'),
    departamento: Optional[str] = Query(None, description='Filtrar por departamento'),
    status: Optional[str] = Query(None, description='Filtrar por status operacional'),
    limit: int = Query(200, ge=1, le=500),
):
    """Retorna o status de conectividade das máquinas cadastradas."""
    query = db.query(models.Maquina)

    if empresa:
        query = query.filter(models.Maquina.empresa == empresa)

    if departamento:
        query = query.filter(models.Maquina.departamento == departamento)

    if status:
        query = query.filter(models.Maquina.status == status)

    maquinas = query.order_by(models.Maquina.nome).limit(limit).all()
    if not maquinas:
        return []

    workers = min(12, max(1, len(maquinas)))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        snapshots = list(executor.map(_monitor_machine, maquinas))

    return snapshots


@router.get('/{maquina_id}', response_model=schemas.MaquinaResponse)
def obter_maquina(maquina_id: int, db: Session = Depends(get_db)):
    """Obtém uma máquina específica pelo ID"""
    maquina = db.query(models.Maquina).filter(models.Maquina.id == maquina_id).first()

    if not maquina:
        raise HTTPException(status_code=404, detail='Máquina não encontrada')
    
    return maquina


@router.post('/', response_model=schemas.MaquinaResponse, status_code=201)
def criar_maquina(
    maquina: schemas.MaquinaCreate,
    db: Session = Depends(get_db)
):
    """Cria uma nova máquina"""

    # Verificar se já existe máquina com mesmo nome e empresa
    existing = db.query(models.Maquina).filter(
        models.Maquina.nome == maquina.nome,
        models.Maquina.empresa == maquina.empresa
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail='Já existe uma máquina com este nome nesta empresa')
    
    # Criar nova máquina
    nova_maquina = models.Maquina(**maquina.model_dump())
    db.add(nova_maquina)
    db.commit()
    db.refresh(nova_maquina)

    print(f'✅ Máquina criada: {nova_maquina.nome} (ID: {nova_maquina.id})')

    return nova_maquina


@router.put('/{maquina_id}', response_model=schemas.MaquinaResponse)
def atualizar_maquina(
    maquina_id: int,
    maquina: schemas.MaquinaUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza uma máquina existente"""

    maquina_existente = db.query(models.Maquina).filter(models.Maquina.id == maquina_id). first()

    if not maquina_existente:
        raise HTTPException(status_code=404, detail='Máquina não encontrada')
    
    update_data = maquina.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(maquina_existente, field, value)

    db.commit()
    db.refresh(maquina_existente)

    return maquina_existente


@router.delete('/{maquina_id}')
def deletar_maquina(
    maquina_id: int,
    db: Session = Depends(get_db)
):
    """Remove uma máquina (apenas se não tiver manutenções)"""

    maquina = db.query(models.Maquina).filter(models.Maquina.id == maquina_id).first()

    if not maquina:
        raise HTTPException(status_code=404, detail='Máquina não encontrada')
    
    # Verificar se existem manutenções
    manutencoes = db.query(models.Manutencao).filter(
        models.Manutencao.maquina_id == maquina_id
    ).first()

    if manutencoes:
        raise HTTPException(
            status_code=400,
            detail='Não é possível deletar máquina com manutenções registradas'
        )
    
    db.delete(maquina)
    db.commit()

    return {'message': 'Máquina deletada com sucesso'}


@router.get('/departamento/lista')
def listar_departamentos(db: Session = Depends(get_db)):
    """Lista todos os departamentos com máquinas"""

    departamentos = db.query(models.Maquina.departamento).distinct().filter(
        models.Maquina.departamento.isnot(None),
        models.Maquina.departamento != ''
    ).all()

    return {'departamentos': [dept[0] for dept in departamentos if dept[0]]}

# @router.patch('/{maquina_id}/status')
# def alterar_status_maquina(
#     maquina_id: int,
#     novo_status: str,
#     db: Session = Depends(get_db)
# ):
#     """Altera o status de uma máquina"""
#     maquina = db.query(models.Maquina).filter(models.Maquina.id == maquina_id).first()

#     if not maquina:
#         raise HTTPException(status_code=404, detail='Máquina não encontrada')
    
#     # Validar status
#     status_validos = ['ativo', 'manutencao', 'inativo']
#     if novo_status not in status_validos:
#         raise HTTPException(status_code=400, detail=f'status inválido. Use: {status_validos}')
    
#     maquina.status = novo_status
#     db.commit()
#     db.refresh(maquina)

#     return {'message': f'Status alterado para {novo_status}', 'maquina': maquina}
