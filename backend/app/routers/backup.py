from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, auth
from app.backup import configurar_scheduler, backup_manual, listar_backups, restaurar_backup

router = APIRouter(prefix='/api/backup', tags=['Backup'])


@router.post("/configurar")
def configurar_backup(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Reconfigura o scheduler de backup (apenas admin)"""
    try:
        configurar_scheduler()
        return {"message": "Backup configurado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/executar")
def executar_backup_manual(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Executa backup manualmente (apenas admin)"""
    success, result = backup_manual()
    if success:
        return {"message": "Backup realizado com sucesso", "arquivo": result}
    else:
        raise HTTPException(status_code=500, detail=result)


@router.get("/listar")
def listar_backups_disponiveis(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Lista todos os backups disponíveis (apenas admin)"""
    return {"backups": listar_backups()}


@router.post("/restaurar/{filename}")
def restaurar_backup_arquivo(
    filename: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin)
):
    """Restaura um backup específico (apenas admin)"""
    success, message = restaurar_backup(filename)
    if success:
        return {"message": message}
    else:
        raise HTTPException(status_code=500, detail=message)
    