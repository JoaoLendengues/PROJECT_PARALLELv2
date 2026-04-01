from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Conectando a: {DATABASE_URL}")

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM materiais"))
    rows = result.fetchall()
    print(f"Total de materiais: {len(rows)}")
    for row in rows:
        print(row)