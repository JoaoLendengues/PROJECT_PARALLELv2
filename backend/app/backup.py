import os
import subprocess
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
import json

# Configurações de backup
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# Scheduler global
scheduler = BackgroundScheduler()
scheduler_started = False


def get_backup_config(db: Session):
    """Obtém as configurações de backup do banco"""
    configs = {}
    
    # Buscar configurações
    backup_auto = db.query(models.Configuracao).filter(
        models.Configuracao.chave == "backup_automatico"
    ).first()
    configs["backup_automatico"] = backup_auto.valor == "true" if backup_auto else True
    
    frequencia = db.query(models.Configuracao).filter(
        models.Configuracao.chave == "frequencia_backup"
    ).first()
    configs["frequencia_backup"] = frequencia.valor if frequencia else "Diário"
    
    horario = db.query(models.Configuracao).filter(
        models.Configuracao.chave == "horario_backup"
    ).first()
    configs["horario_backup"] = horario.valor if horario else "02:00"
    
    dias_retencao = db.query(models.Configuracao).filter(
        models.Configuracao.chave == "dias_retencao"
    ).first()
    configs["dias_retencao"] = int(dias_retencao.valor) if dias_retencao else 30
    
    return configs


def realizar_backup():
    """Executa o backup do banco de dados"""
    try:
        # Configurações do banco (ajuste conforme seu PostgreSQL)
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "project_parallel")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "postgres")
        
        # Nome do arquivo de backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{db_name}_{timestamp}.sql"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # Comando pg_dump
        # IMPORTANTE: Ajuste o caminho do pg_dump conforme sua instalação
        pg_dump_path = "pg_dump"  # ou "C:\\Program Files\\PostgreSQL\\16\\bin\\pg_dump.exe"
        
        # Definir variável de ambiente para senha
        env = os.environ.copy()
        env["PGPASSWORD"] = db_password
        
        cmd = [
            pg_dump_path,
            "-h", db_host,
            "-p", db_port,
            "-U", db_user,
            "-d", db_name,
            "-F", "p",  # Plain SQL format
            "-f", backup_path
        ]
        
        print(f"📁 Iniciando backup: {backup_filename}")
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Comprimir o arquivo
            import gzip
            with open(backup_path, 'rb') as f_in:
                with gzip.open(f"{backup_path}.gz", 'wb') as f_out:
                    f_out.write(f_in.read())
            
            # Remover arquivo não comprimido
            os.remove(backup_path)
            
            print(f"✅ Backup concluído: {backup_filename}.gz")
            
            # Limpar backups antigos
            limpar_backups_antigos()
            
            return True, backup_filename
        else:
            print(f"❌ Erro no backup: {result.stderr}")
            return False, result.stderr
            
    except Exception as e:
        print(f"❌ Erro ao realizar backup: {e}")
        return False, str(e)


def limpar_backups_antigos():
    """Remove backups mais antigos que o período de retenção"""
    try:
        db = SessionLocal()
        config = get_backup_config(db)
        db.close()
        
        dias_retencao = config.get("dias_retencao", 30)
        
        # Calcular data limite
        from datetime import timedelta
        data_limite = datetime.now() - timedelta(days=dias_retencao)
        
        # Percorrer arquivos de backup
        for filename in os.listdir(BACKUP_DIR):
            if filename.startswith("backup_") and filename.endswith(".gz"):
                filepath = os.path.join(BACKUP_DIR, filename)
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_mtime < data_limite:
                    os.remove(filepath)
                    print(f"🗑️ Backup antigo removido: {filename}")
                    
    except Exception as e:
        print(f"❌ Erro ao limpar backups antigos: {e}")


def configurar_scheduler():
    """Configura o scheduler de backup baseado nas configurações do banco"""
    global scheduler_started
    
    try:
        db = SessionLocal()
        config = get_backup_config(db)
        db.close()
        
        # Se backup automático não estiver habilitado, para o scheduler
        if not config.get("backup_automatico", False):
            if scheduler.running:
                scheduler.shutdown()
                scheduler_started = False
            print("⏸️ Backup automático desabilitado")
            return
        
        # Remover jobs existentes
        scheduler.remove_all_jobs()
        
        # Configurar trigger baseado na frequência
        frequencia = config.get("frequencia_backup", "Diário")
        horario = config.get("horario_backup", "02:00")
        hora, minuto = map(int, horario.split(":"))
        
        if frequencia == "Diário":
            trigger = CronTrigger(hour=hora, minute=minuto)
            print(f"⏰ Backup diário configurado para {horario}")
        elif frequencia == "Semanal":
            trigger = CronTrigger(day_of_week='sun', hour=hora, minute=minuto)
            print(f"⏰ Backup semanal configurado para domingo às {horario}")
        elif frequencia == "Mensal":
            trigger = CronTrigger(day=1, hour=hora, minute=minuto)
            print(f"⏰ Backup mensal configurado para dia 1 às {horario}")
        else:
            trigger = CronTrigger(hour=hora, minute=minuto)
            print(f"⏰ Backup {frequencia} configurado para {horario}")
        
        # Adicionar job
        scheduler.add_job(realizar_backup, trigger, id="backup_job")
        
        # Iniciar scheduler se não estiver rodando
        if not scheduler.running:
            scheduler.start()
            scheduler_started = True
            print("✅ Scheduler de backup iniciado")
            
    except Exception as e:
        print(f"❌ Erro ao configurar scheduler: {e}")


def backup_manual():
    """Executa backup manualmente (para teste)"""
    return realizar_backup()


def listar_backups():
    """Lista todos os backups disponíveis"""
    backups = []
    for filename in os.listdir(BACKUP_DIR):
        if filename.startswith("backup_") and filename.endswith(".gz"):
            filepath = os.path.join(BACKUP_DIR, filename)
            size = os.path.getsize(filepath) / (1024 * 1024)  # MB
            modified = datetime.fromtimestamp(os.path.getmtime(filepath))
            backups.append({
                "nome": filename,
                "tamanho_mb": round(size, 2),
                "data": modified.strftime("%d/%m/%Y %H:%M:%S")
            })
    
    # Ordenar por data (mais recente primeiro)
    backups.sort(key=lambda x: x["data"], reverse=True)
    return backups


def restaurar_backup(filename):
    """Restaura um backup específico"""
    try:
        backup_path = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(backup_path):
            return False, "Arquivo de backup não encontrado"
        
        # Configurações do banco
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "project_parallel")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "postgres")
        
        # Descomprimir arquivo
        import gzip
        temp_sql = backup_path.replace(".gz", "")
        with gzip.open(backup_path, 'rb') as f_in:
            with open(temp_sql, 'wb') as f_out:
                f_out.write(f_in.read())
        
        # Executar restauração
        env = os.environ.copy()
        env["PGPASSWORD"] = db_password
        
        pg_restore_path = "psql"  # ou "C:\\Program Files\\PostgreSQL\\16\\bin\\psql.exe"
        
        cmd = [
            pg_restore_path,
            "-h", db_host,
            "-p", db_port,
            "-U", db_user,
            "-d", db_name,
            "-f", temp_sql
        ]
        
        # Na verdade, para restaurar um dump SQL, usamos:
        cmd = [
            pg_restore_path,
            "-h", db_host,
            "-p", db_port,
            "-U", db_user,
            "-d", db_name,
            "-f", temp_sql
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        # Remover arquivo temporário
        os.remove(temp_sql)
        
        if result.returncode == 0:
            return True, "Backup restaurado com sucesso"
        else:
            return False, result.stderr
            
    except Exception as e:
        return False, str(e)
    