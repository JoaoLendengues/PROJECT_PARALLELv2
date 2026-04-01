from app.database import SessionLocal
from app import models

db = SessionLocal()

try:
    materiais = db.query(models.Material).all()
    print(f'Total: {len(materiais)}')
    for m in materiais:
        print(f'{m.id} - {m.nome}')

except Exception as e:
    print(f'Erro: {e}')

finally:
    db.close()