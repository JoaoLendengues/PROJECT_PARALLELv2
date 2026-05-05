ROLE_ADMIN = "admin"
ROLE_MANAGER = "gerente"
ROLE_USER = "usuario"

ROLE_LABELS = {
    ROLE_ADMIN: "Administrador",
    ROLE_MANAGER: "Gerência",
    ROLE_USER: "Usuário",
}

ROLE_ALIASES = {
    "admin": ROLE_ADMIN,
    "administrador": ROLE_ADMIN,
    "gerente": ROLE_MANAGER,
    "gerencia": ROLE_MANAGER,
    "manager": ROLE_MANAGER,
    "usuario": ROLE_USER,
    "usuário": ROLE_USER,
    "comum": ROLE_USER,
}

SCREEN_LABELS = {
    "home": "Home",
    "materiais": "Materiais",
    "maquinas": "Máquinas",
    "movimentacoes": "Movimentações",
    "manutencoes": "Manutenções",
    "pedidos": "Pedidos",
    "colaboradores": "Colaboradores",
    "demandas": "Demandas",
    "relatorios": "Relatórios",
    "usuarios": "Usuários",
    "parametros": "Parâmetros",
    "updates": "Atualizações",
    "notificacoes": "Notificações",
}

SCREEN_PERMISSIONS = {
    "home": {ROLE_ADMIN, ROLE_MANAGER, ROLE_USER},
    "materiais": {ROLE_ADMIN, ROLE_MANAGER},
    "maquinas": {ROLE_ADMIN, ROLE_MANAGER},
    "movimentacoes": {ROLE_ADMIN, ROLE_MANAGER, ROLE_USER},
    "manutencoes": {ROLE_ADMIN, ROLE_MANAGER},
    "pedidos": {ROLE_ADMIN, ROLE_MANAGER},
    "colaboradores": {ROLE_ADMIN, ROLE_MANAGER},
    "demandas": {ROLE_ADMIN, ROLE_MANAGER},
    "relatorios": {ROLE_ADMIN, ROLE_MANAGER},
    "usuarios": {ROLE_ADMIN},
    "parametros": {ROLE_ADMIN},
    "updates": {ROLE_ADMIN, ROLE_MANAGER, ROLE_USER},
    "notificacoes": {ROLE_ADMIN, ROLE_MANAGER, ROLE_USER},
}

ACTION_PERMISSIONS = {
    "materiais.create": {ROLE_ADMIN, ROLE_MANAGER},
    "materiais.edit": {ROLE_ADMIN, ROLE_MANAGER},
    "materiais.delete": {ROLE_ADMIN},
    "maquinas.create": {ROLE_ADMIN, ROLE_MANAGER},
    "maquinas.edit": {ROLE_ADMIN, ROLE_MANAGER},
    "maquinas.delete": {ROLE_ADMIN},
    "colaboradores.create": {ROLE_ADMIN, ROLE_MANAGER},
    "colaboradores.edit": {ROLE_ADMIN, ROLE_MANAGER},
    "colaboradores.delete": {ROLE_ADMIN},
    "manutencoes.create": {ROLE_ADMIN, ROLE_MANAGER},
    "manutencoes.edit": {ROLE_ADMIN, ROLE_MANAGER},
    "manutencoes.complete": {ROLE_ADMIN, ROLE_MANAGER},
    "manutencoes.delete": {ROLE_ADMIN},
    "pedidos.create": {ROLE_ADMIN, ROLE_MANAGER},
    "pedidos.edit": {ROLE_ADMIN, ROLE_MANAGER},
    "pedidos.approve": {ROLE_ADMIN, ROLE_MANAGER},
    "pedidos.complete": {ROLE_ADMIN, ROLE_MANAGER},
    "pedidos.cancel": {ROLE_ADMIN, ROLE_MANAGER},
    "pedidos.delete": {ROLE_ADMIN},
    "demandas.create": {ROLE_ADMIN, ROLE_MANAGER},
    "demandas.edit": {ROLE_ADMIN, ROLE_MANAGER},
    "demandas.complete": {ROLE_ADMIN, ROLE_MANAGER},
    "demandas.cancel": {ROLE_ADMIN, ROLE_MANAGER},
    "demandas.delete": {ROLE_ADMIN},
    "relatorios.export": {ROLE_ADMIN, ROLE_MANAGER},
    "movimentacoes.deletar": {ROLE_ADMIN},
}

ACTION_LABELS = {
    "materiais.create": "criar materiais",
    "materiais.edit": "editar materiais",
    "materiais.delete": "deletar materiais",
    "maquinas.create": "criar máquinas",
    "maquinas.edit": "editar máquinas",
    "maquinas.delete": "deletar máquinas",
    "colaboradores.create": "criar colaboradores",
    "colaboradores.edit": "editar colaboradores",
    "colaboradores.delete": "deletar colaboradores",
    "manutencoes.create": "criar manutenções",
    "manutencoes.edit": "editar manutenções",
    "manutencoes.complete": "concluir manutenções",
    "manutencoes.delete": "deletar manutenções",
    "pedidos.create": "criar pedidos",
    "pedidos.edit": "editar pedidos",
    "pedidos.approve": "aprovar pedidos",
    "pedidos.complete": "concluir pedidos",
    "pedidos.cancel": "cancelar pedidos",
    "pedidos.delete": "deletar pedidos",
    "demandas.create": "criar demandas",
    "demandas.edit": "editar demandas",
    "demandas.complete": "concluir demandas",
    "demandas.cancel": "cancelar demandas",
    "demandas.delete": "deletar demandas",
    "relatorios.export": "exportar relatórios",
    "movimentacoes.deletar": "deletar movimentações",
}


def normalize_access_level(level):
    value = str(level or ROLE_USER).strip().lower()
    return ROLE_ALIASES.get(value, ROLE_USER)


def get_role_label(level):
    return ROLE_LABELS.get(normalize_access_level(level), ROLE_LABELS[ROLE_USER])


def get_screen_label(screen_key):
    return SCREEN_LABELS.get(screen_key, "esta tela")


def has_screen_access(usuario, screen_key):
    role = normalize_access_level((usuario or {}).get("nivel_acesso"))
    allowed_roles = SCREEN_PERMISSIONS.get(screen_key, {ROLE_ADMIN})
    return role in allowed_roles


def has_action_access(usuario, action_key):
    role = normalize_access_level((usuario or {}).get("nivel_acesso"))
    allowed_roles = ACTION_PERMISSIONS.get(action_key, {ROLE_ADMIN})
    return role in allowed_roles


def get_action_label(action_key):
    return ACTION_LABELS.get(action_key, "executar esta ação")
