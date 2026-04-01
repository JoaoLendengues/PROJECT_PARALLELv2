from app.database import test_connection

if __name__ == '__main__':
    print('=' * 50)
    print('Teste de Conexão com PostgreSQL')
    print('=' * 50)

    success = test_connection()

    if success:
        print('\n✅ Banco de dados configurado corretamente')
        print('📍 IP: 10.1.1.151')
        print('📦 Banco: project_parallel')
    else:
        print('\n❌ Verifique as configurações no arquivo .env')
        print('DATABASE_URL=postgresql://usuario:senha@10.1.1.151:5432/project_parallel')
        