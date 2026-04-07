from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, Float, ForeignKey, JSON
from sqlalchemy.sql import func

from app.database import Base


class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    cargo = Column(String(50))
    empresa = Column(String(100))
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, server_default=func.now())

class Material(Base):
    __tablename__ = 'materiais'

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text)
    quantidade = Column(Integer, default=0)
    categoria = Column(String(50))
    empresa = Column(String(100),nullable=False)
    status = Column(String(20), default="ativo")
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Maquina(Base):
    __tablename__ = "maquinas"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    modelo = Column(String(100))
    empresa = Column(String(100), nullable=False)
    departamento = Column(String(100))
    status = Column(String(20), default="ativo")
    observacoes = Column(Text)
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Movimentacao(Base):
    __tablename__ = 'movimentacoes'

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materiais.id"))
    tipo = Column(String(10), nullable=False)
    quantidade = Column(Integer, nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    empresa = Column(String(100), nullable=False)
    destinatario = Column(String(100))
    observacao = Column(Text)
    assinatura_digital = Column(Text)
    ip_origem = Column(String(45))
    data_hora = Column(DateTime, server_default=func.now())


class Manutencao(Base):
    __tablename__ = 'manutencoes'

    id = Column(Integer, primary_key=True, index=True)
    maquina_id = Column(Integer, ForeignKey("maquinas.id"))
    tipo = Column(String(50), nullable=False)
    descricao = Column(Text, nullable=False)
    data_inicio =  Column(Date, nullable=False)
    data_fim = Column(Text)
    data_proxima = Column(Date)
    responsavel = Column(String(100))
    status = Column(String(20), default="pendente")
    custo = Column(Float)
    observacoes = Column(Text)
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em =  Column(DateTime, server_default=func.now(), onupdate=func.now())
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))


class Pedido(Base):
    __tablename__ = 'pedidos'

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materiais.id"))
    quantidade = Column(Integer, nullable=False)
    solicitante = Column(String(100), nullable=False)
    empresa =  Column(String(100), nullable=False)
    departamento = Column(String(100))
    data_solicitacao = Column(Date, server_default=func.current_date())
    data_conclusao = Column(Date)
    status = Column(String(20), default="pedente")
    observacao = Column(Text)
    criado_em = Column(DateTime, server_default=func.now())
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))

    
class LogAuditoria(Base):
    __tablename__ = 'logs_auditoria'

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    acao = Column(String(50), nullable=False)
    tabela_afetada = Column(String(50))
    registro_id = Column(Integer)
    dados_anteriores = Column(JSON)
    dados_novos = Column(JSON)
    ip_origem = Column(String(45))
    data_hora = Column(DateTime, server_default=func.now())


class UsuarioSistema(Base):
    __tablename__ = "usuarios_sistema"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, nullable=False)
    nome = Column(String(100), nullable=False)
    senha_hash = Column(String(255), nullable=False)
    cargo = Column(String(50))
    empresa = Column(String(100))
    nivel_acesso = Column(String(20), default="usuario")
    primeiro_acesso = Column(Boolean, default=True)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Colaborador(Base):
    __tablename__ = "colaboradores"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cargo = Column(String(50))
    departamento = Column(String(100))
    empresa = Column(String(100))
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())
    

class Demanda(Base):
    __tablename__ = 'demandas'

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    descricao = Column(Text, nullable=False)
    solicitante = Column(String(100), nullable=False)
    departamento = Column(String(100))
    empresa = Column(String(100))
    prioridade = Column(String(20), default="media")
    urgencia = Column(String(20), default="media")
    status = Column(String(20), default="aberto")
    data_abertura = Column(DateTime, server_default=func.now())
    data_prevista = Column(Date)
    data_conclusao = Column(Date)
    responsavel = Column(String(100))
    observacao = Column(Text)
    criado_por = Column(Integer, ForeignKey("usuarios_sistema.id"))
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())
    

    