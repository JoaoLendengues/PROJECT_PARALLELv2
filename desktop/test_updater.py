from updater import UpdateChecker
import sys

def test():
    print("Testando UpdateChecker...")
    checker = UpdateChecker("1.0.0")
    
    def on_update(info):
        print(f"✅ ATUALIZAÇÃO ENCONTRADA!")
        print(f"Versão: {info['version']}")
        print(f"Download: {info['download_url']}")
    
    def on_no_update():
        print("ℹ️ Nenhuma atualização")
    
    def on_error(msg):
        print(f"❌ Erro: {msg}")
    
    checker.update_available.connect(on_update)
    checker.no_update.connect(on_no_update)
    checker.error.connect(on_error)
    
    checker.start()
    
    # Aguardar um pouco
    import time
    time.sleep(5)

if __name__ == "__main__":
    test()
    