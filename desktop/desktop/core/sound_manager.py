import os
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect


class SoundManager:
    """Gerenciador de sons para notificações - Singleton"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        self._sons = {}
        self._habilitado = True
        self._volume = 0.7
        self._carregar_sons()
    
    def _carregar_sons(self):
        """Carrega os arquivos de som (usando sons do sistema como fallback)"""
        # Sons personalizados (você pode adicionar arquivos .wav na pasta sounds)
        sons_personalizados = {
            "alta": "sounds/alert.wav",
            "media": "sounds/notice.wav",
            "baixa": "sounds/info.wav"
        }
        
        for prioridade, caminho in sons_personalizados.items():
            if os.path.exists(caminho):
                som = QSoundEffect()
                som.setSource(QUrl.fromLocalFile(caminho))
                som.setVolume(self._volume)
                self._sons[prioridade] = som
        
        # Se não encontrar os arquivos personalizados, não carrega nada
        # (opcional: usar beep do sistema como fallback)
    
    def tocar(self, prioridade):
        """Toca o som correspondente à prioridade"""
        if not self._habilitado:
            return
        
        if prioridade in self._sons:
            self._sons[prioridade].play()
        elif prioridade == "alta":
            # Fallback: beep do sistema para prioridade alta
            import sys
            if sys.platform == "win32":
                import winsound
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    
    def set_habilitado(self, habilitado):
        """Habilita ou desabilita os sons"""
        self._habilitado = habilitado
    
    def set_volume(self, volume):
        """Ajusta o volume (0.0 a 1.0)"""
        self._volume = max(0.0, min(1.0, volume))
        for som in self._sons.values():
            som.setVolume(self._volume)


# Instância global
sound_manager = SoundManager()