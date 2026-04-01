import requests
import json

# URL da API
url = "http://localhost:8000/api/materiais"

# Dados do material
data = {
    "nome": "Mouse Logitech M90",
    "descricao": "Mouse óptico com fio USB",
    "quantidade": 25,
    "categoria": "Periféricos",
    "empresa": "Matriz",
    "status": "ativo"
}

print("📦 Criando material...")
response = requests.post(url, json=data)

if response.status_code == 201:
    print("✅ Material criado com sucesso!")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
else:
    print(f"❌ Erro: {response.status_code}")
    print(response.json())