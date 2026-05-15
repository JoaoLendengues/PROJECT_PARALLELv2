from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import auth, models
from app.audit import registrar_log_auditoria
from app.backup import backup_manual, configurar_scheduler, listar_backups, restaurar_backup
from app.database import get_db

router = APIRouter(prefix="/api/backup", tags=["Backup"])


@router.post("/configurar")
def configurar_backup(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin),
):
    """Reconfigura o scheduler de backup (apenas admin)."""
    try:
        configurar_scheduler()
        registrar_log_auditoria(
            db,
            usuario=current_user,
            acao="CONFIGURE_BACKUP",
            tabela_afetada="backup",
            dados_novos={"scheduler_reconfigurado": True},
            request=request,
        )
        db.commit()
        return {"message": "Backup configurado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/executar")
def executar_backup_manual(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin),
):
    """Executa backup manualmente (apenas admin)."""
    success, result = backup_manual()
    if success:
        try:
            registrar_log_auditoria(
                db,
                usuario=current_user,
                acao="RUN_BACKUP",
                tabela_afetada="backup",
                dados_novos={"arquivo": result},
                request=request,
            )
            db.commit()
        except Exception as log_error:
            print(f"Erro ao registrar log de execucao de backup: {log_error}")
        return {"message": "Backup realizado com sucesso", "arquivo": result}
    raise HTTPException(status_code=500, detail=result)


@router.get("/listar")
def listar_backups_disponiveis(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin),
):
    """Lista todos os backups disponiveis (apenas admin)."""
    return {"backups": listar_backups()}


@router.post("/restaurar/{filename}")
def restaurar_backup_arquivo(
    filename: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(auth.verificar_admin),
):
    """Restaura um backup especifico (apenas admin)."""
    success, message = restaurar_backup(filename)
    if success:
        try:
            registrar_log_auditoria(
                db,
                usuario=current_user,
                acao="RESTORE_BACKUP",
                tabela_afetada="backup",
                dados_novos={"arquivo": filename, "resultado": message},
                request=request,
            )
            db.commit()
        except Exception as log_error:
            print(f"Erro ao registrar log de restauracao de backup: {log_error}")
        return {"message": message}
    raise HTTPException(status_code=500, detail=message)
