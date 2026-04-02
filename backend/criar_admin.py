from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Senha padrão
senha = "admin123"

# Gerar hash
hash_senha = pwd_context.hash(senha)

print(f"Senha: {senha}")
print(f"Hash: {hash_senha}")
