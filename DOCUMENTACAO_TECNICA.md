# Documentação Técnica do Project Parallel

## 1. Visão geral

O **Project Parallel** é um sistema desktop com backend HTTP para controle operacional de estoque, máquinas, manutenções, pedidos, demandas, usuários, notificações, parâmetros e monitoramento de conectividade.

Atualmente, o projeto está organizado em duas camadas principais:

- **Backend**: API REST em FastAPI, com persistência em PostgreSQL via SQLAlchemy.
- **Desktop**: aplicação em PySide6, responsável pela interface principal, autenticação, dashboards, relatórios, notificações, acessibilidade e atualização automática.

Além disso, o repositório inclui:

- scripts de execução do backend;
- fluxo de empacotamento com PyInstaller;
- instalador Windows via Inno Setup;
- infraestrutura local para atualização automática do desktop;
- backlog consolidado em [BACKLOG.md](C:\Users\João\Desktop\PROJECT_PARALLELv2\BACKLOG.md).

## 2. Estado atual do projeto

### 2.1 Nome do produto

O nome operacional atual do sistema no código, no instalador e nas releases é **Project Parallel**.

Existe, porém, uma diretriz registrada em backlog para evolução futura do nome oficial para **Link Flow**.

### 2.2 Versão de referência

A versão declarada no desktop está em [desktop/version.json](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\version.json):

- **versão**: `1.2.3`
- **data da release**: `2026-05-09`

Observação importante:

- o repositório também já contém uma **refatoração estrutural do atualizador**, ainda em andamento, iniciada no commit `a14d253`;
- essa refatoração prepara um fluxo mais confiável com helper externo, staging, estado persistido e rollback.

## 3. Arquitetura de alto nível

```mermaid
flowchart LR
    A["Desktop (PySide6)"] --> B["API REST (FastAPI)"]
    B --> C["PostgreSQL"]
    A --> D["Arquivos locais do usuário"]
    A --> E["Fluxo de atualização"]
    E --> F["GitHub Releases"]
```

### 3.1 Responsabilidades por camada

**Desktop**

- autenticação por código e senha;
- renderização da interface;
- controle de navegação por perfil;
- dashboards e relatórios;
- monitoramento visual de rede, malha LAN-to-LAN e máquinas;
- consumo da API;
- persistência local de preferências e acessibilidade;
- atualização automática e empacotamento.

**Backend**

- autenticação e emissão de JWT;
- regras de negócio;
- persistência;
- trilha de auditoria;
- notificações;
- rotinas de backup;
- endpoints de monitoramento e suporte operacional.

## 4. Estrutura do repositório

```text
PROJECT_PARALLELv2/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── auth.py
│   │   ├── audit.py
│   │   ├── backup.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── routers/
│   ├── run.py
│   ├── run_production.py
│   └── scripts auxiliares
├── desktop/
│   ├── main.py
│   ├── api_client.py
│   ├── updater.py
│   ├── update_helper.py
│   ├── accessibility_manager.py
│   ├── access_control.py
│   ├── app_paths.py
│   ├── create_package.py
│   ├── machine_identity.py
│   ├── user_preferences.py
│   ├── version.py
│   ├── version.json
│   ├── core/
│   ├── styles/
│   └── widgets/
├── installer_output/
├── installer_script.iss
├── requirements.txt
└── BACKLOG.md
```

## 5. Stack tecnológica

### 5.1 Backend

- **Python**
- **FastAPI**
- **SQLAlchemy**
- **PostgreSQL**
- **python-jose** para JWT
- **passlib + bcrypt** para hashing de senha
- **APScheduler** para rotinas de backup
- **psutil** para telemetria local e status do sistema

### 5.2 Desktop

- **Python**
- **PySide6**
- **requests** para comunicação com a API
- **openpyxl** para exportações Excel
- **reportlab** para exportações PDF
- **psutil** e rotinas próprias para monitoramento e update

### 5.3 Empacotamento e distribuição

- **PyInstaller**
- **Inno Setup**
- **GitHub Releases**

As dependências do projeto estão listadas em [requirements.txt](C:\Users\João\Desktop\PROJECT_PARALLELv2\requirements.txt).

## 6. Backend

## 6.1 Bootstrap da aplicação

Arquivo principal: [backend/app/main.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\app\main.py)

Responsabilidades:

- criar a aplicação FastAPI;
- aplicar CORS global;
- criar/verificar tabelas;
- aplicar ajustes de compatibilidade de schema;
- registrar routers;
- iniciar e encerrar o scheduler de backup;
- expor endpoints de saúde e diagnóstico.

### 6.1.1 Ajustes automáticos de schema

Na inicialização, o backend verifica e cria, quando necessário:

- `pedidos.link_compra`
- `maquinas.ip_address`
- `maquinas.ultimo_heartbeat_em`
- `maquinas.ultimo_heartbeat_ip`
- `maquinas.ultimo_heartbeat_hostname`

Isso evita migrações manuais para algumas evoluções incrementais já feitas no sistema.

## 6.2 Banco de dados

Arquivo: [backend/app/database.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\app\database.py)

### 6.2.1 Engine

O backend usa:

- `QueuePool`
- `pool_size=50`
- `max_overflow=100`
- `pool_pre_ping=True`
- `pool_recycle=3600`

Esse desenho foi preparado para suportar cenários de carga mais alta e múltiplas conexões simultâneas.

### 6.2.2 Fonte de configuração

Variável principal:

- `DATABASE_URL`

Valor padrão:

- `postgresql://postgres:postgres@localhost:5432/project_parallel`

## 6.3 Modelagem de dados

Arquivo: [backend/app/models.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\app\models.py)

### 6.3.1 Entidades principais

**Usuario**

- modelo legado de usuário;
- ainda existe para compatibilidades históricas e ligação com parte da auditoria.

**UsuarioSistema**

- usuário efetivo do desktop;
- autenticação por `codigo`;
- campos principais:
  - `codigo`
  - `nome`
  - `senha_hash`
  - `cargo`
  - `empresa`
  - `nivel_acesso`
  - `primeiro_acesso`
  - `ativo`

**Material**

- controle de itens de estoque;
- campos centrais:
  - `nome`
  - `descricao`
  - `quantidade`
  - `categoria`
  - `empresa`
  - `status`

**Maquina**

- cadastro de estações ou equipamentos;
- campos centrais:
  - `nome`
  - `modelo`
  - `empresa`
  - `departamento`
  - `status`
  - `mac_address`
  - `ip_address`
  - dados de último heartbeat

**Movimentacao**

- entrada e saída de materiais;
- referencia material, empresa, destinatário, observação e assinatura digital.

**Manutencao**

- manutenção preventiva, corretiva ou emergencial;
- relacionada a máquina;
- controla datas, responsável, custo e status.

**Pedido**

- solicitações de compra;
- permite material cadastrado ou fluxo compatível com material livre;
- possui `link_compra`.

**Demanda**

- fluxo de chamados internos e autoatendimento;
- campos centrais:
  - `titulo`
  - `descricao`
  - `solicitante`
  - `empresa`
  - `departamento`
  - `prioridade`
  - `urgencia`
  - `status`
  - `responsavel`
  - `criado_por`

**Configuracao**

- chave/valor para parâmetros do sistema.

**Departamento** e **Cargo**

- cadastros auxiliares administrativos.

**Notificacao**

- fila persistida de notificações por usuário;
- campos centrais:
  - `tipo`
  - `titulo`
  - `mensagem`
  - `prioridade`
  - `status`
  - `acao`
  - `acao_id`
  - `dados_extra`

**LogAuditoria**

- trilha de auditoria;
- registra ação, tabela, registro, dados anteriores, dados novos, IP e data/hora.

## 6.4 Schemas da API

Arquivo: [backend/app/schemas.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\app\schemas.py)

Os schemas expõem:

- payloads de criação;
- payloads de atualização;
- modelos de resposta;
- contratos de autenticação;
- contratos de heartbeat;
- contratos específicos de demandas, notificações e auditoria.

Pontos relevantes:

- o login usa `LoginRequest`, `LoginResponse` e `LoginUserPreviewResponse`;
- o monitoramento de máquinas usa `MaquinaMonitoramentoResponse`;
- o heartbeat do desktop usa `MaquinaHeartbeatRequest` e `MaquinaHeartbeatResponse`.

## 6.5 Autenticação e autorização

Arquivos:

- [backend/app/auth.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\app\auth.py)
- [backend/app/routers/auth.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\app\routers\auth.py)

### 6.5.1 Estratégia

- autenticação por `codigo` e `senha`;
- senha armazenada com hash `bcrypt`;
- emissão de JWT com `python-jose`;
- validade padrão do token: **8 horas**.

### 6.5.2 Endpoints de autenticação

- `GET /api/auth/usuario-preview/{codigo}`
- `POST /api/auth/login`
- `POST /api/auth/confirmar-senha`
- `POST /api/auth/trocar-senha`
- `POST /api/auth/primeiro-acesso`

### 6.5.3 Perfis de acesso

No backend e no desktop, o sistema trabalha principalmente com:

- `admin`
- `gerente`
- `usuario`
- `solicitante`

Além disso, existe uma camada complementar de acesso por **cargo de TI**, inferida por palavras-chave como:

- `ti`
- `tecnologia`
- `suporte`
- `informatica`

## 6.6 Auditoria

Arquivos:

- [backend/app/audit.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\app\audit.py)
- [backend/app/routers/auditoria.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\app\routers\auditoria.py)

### 6.6.1 Funções centrais

- serialização segura de datas, decimais, listas e dicionários;
- transformação de modelos ORM em dicionários auditáveis;
- resolução de IP de requisição;
- tentativa de resolução do usuário autenticado;
- persistência de logs em `logs_auditoria`.

### 6.6.2 Cobertura atual

A auditoria já foi expandida para módulos sensíveis, incluindo:

- usuários do sistema;
- cargos;
- departamentos;
- empresas, categorias e configurações;
- materiais;
- máquinas;
- manutenções;
- colaboradores;
- pedidos;
- demandas.

## 6.7 Routers da API

### 6.7.1 Inventário de módulos

Os routers atuais ficam em [backend/app/routers](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\app\routers) e cobrem:

- `auth`
- `materiais`
- `maquinas`
- `manutencoes`
- `movimentacoes`
- `pedidos`
- `usuarios_sistema`
- `colaboradores`
- `dashboard`
- `demandas`
- `configuracoes`
- `departamentos`
- `cargos`
- `backup`
- `notificacoes`
- `auditoria`

### 6.7.2 Regras de negócio relevantes

**Demandas**

- `solicitante` vê apenas as próprias demandas;
- `gerência`, `admin` e perfis reconhecidos como TI podem assumir, concluir e cancelar;
- existe ação `assumir para mim`;
- criação de demanda gera notificações para gerência, administração e TI elegíveis.

**Pedidos**

- suporta `link_compra`;
- possui fluxo de aprovação, conclusão e cancelamento.

**Máquinas**

- expõe monitoramento por IP/host;
- recebe heartbeat do desktop;
- devolve status operacional mais rico do que simples ping.

**Dashboard**

- expõe resumo operacional;
- expõe status da rede local;
- expõe status LAN-to-LAN;
- usa firewalls mapeados por unidade.

## 6.8 Monitoramento de conectividade

Arquivo principal: [backend/app/routers/dashboard.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\app\routers\dashboard.py)

### 6.8.1 Firewalls mapeados

Atualmente o sistema conhece:

- `PINHEIRO TAGUATINGA` -> `10.1.1.100:8443`
- `PINHEIRO SIA` -> `10.1.1.150:8443`
- `PINHEIRO INDUSTRIA` -> `85.113.93.6:8443`

### 6.8.2 Tipos de leitura

**Status da rede local**

- consulta o firewall da unidade do usuário;
- mede latência via conexão TCP;
- classifica qualidade.

**Status LAN-to-LAN**

- avalia a conectividade da unidade atual para os demais firewalls;
- retorna resumo com links online, offline e com erro.

## 6.9 Backup

Arquivo: [backend/app/backup.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\app\backup.py)

### 6.9.1 Capacidades

- backup automático com scheduler;
- backup manual;
- listagem de backups;
- restauração;
- política de retenção.

### 6.9.2 Fonte de configuração

As configurações vêm da tabela `configuracoes`, por chaves como:

- `backup_automatico`
- `frequencia_backup`
- `horario_backup`
- `dias_retencao`

### 6.9.3 Dependências externas

O fluxo atual de backup/restauração depende de ferramentas do PostgreSQL, especialmente `pg_dump` e `psql`, com caminhos que podem precisar de ajuste por ambiente.

## 6.10 Execução do backend

Scripts principais:

- [backend/run.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\run.py)
- [backend/run_production.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\run_production.py)

### 6.10.1 run.py

- sobe a API com `uvicorn`;
- configuração voltada a carga maior;
- expõe em `0.0.0.0:8000`.

### 6.10.2 run_production.py

- sobe a aplicação com `waitress`;
- perfil mais simples de produção local.

## 7. Desktop

## 7.1 Bootstrap da aplicação

Arquivo: [desktop/main.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\main.py)

Fluxo principal:

1. carrega `.env`;
2. cria `QApplication`;
3. aplica stylesheet base;
4. inicializa acessibilidade;
5. finaliza possível atualização pendente;
6. exibe a tela de login;
7. após login, carrega configurações do backend;
8. abre `MainWindow` maximizada;
9. inicia alertas e verificação de atualizações.

## 7.2 Comunicação com a API

Arquivo: [desktop/api_client.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\api_client.py)

### 7.2.1 Papel

`APIClient` centraliza:

- login;
- headers com JWT;
- cache simples de dados estáticos;
- chamadas para todos os módulos do backend;
- chamadas de monitoramento;
- chamadas de heartbeat;
- notificações;
- parâmetros;
- relatórios e dados de apoio.

### 7.2.2 URL da API

Variável:

- `API_URL`

Valor padrão atual:

- `http://10.1.1.151:8000`

## 7.3 Janela principal e navegação

Arquivo: [desktop/widgets/main_window.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\widgets\main_window.py)

### 7.3.1 Funções da MainWindow

- montar sidebar;
- inicializar widgets principais;
- controlar navegação por `QStackedWidget`;
- filtrar telas por permissão;
- iniciar heartbeat da estação;
- acoplar badge e central de notificações;
- definir a primeira tela acessível de acordo com o perfil.

### 7.3.2 Telas principais carregadas

- Home
- Materiais
- Máquinas
- Movimentações
- Manutenções
- Pedidos
- Colaboradores
- Demandas
- Relatórios
- Usuários
- Parâmetros
- Atualizações

## 7.4 Controle de acesso no desktop

Arquivo: [desktop/access_control.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\access_control.py)

### 7.4.1 Conceito

O desktop controla acesso por:

- **tela**
- **ação interna**

### 7.4.2 Perfis

- `admin`
- `gerente`
- `usuario`
- `solicitante`
- `ti` como tag complementar baseada em cargo

### 7.4.3 Exemplos

- `solicitante` acessa apenas o fluxo de demandas;
- `usuario` não exporta relatórios;
- `admin` retém ações destrutivas e telas administrativas.

## 7.5 Acessibilidade

Arquivo principal: [desktop/accessibility_manager.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\accessibility_manager.py)

### 7.5.1 Recursos

- tema claro/escuro;
- tamanhos de fonte:
  - Muito pequena
  - Pequena
  - Padrão
  - Grande
  - Muito grande
- escala de interface:
  - Automática
  - 90%
  - 100%
  - 110%
  - 125%
  - 150%
  - 175%
- navegação por teclado;
- reestilização de widgets já abertos e novos;
- adaptação por resolução.

### 7.5.2 Persistência

As preferências de acessibilidade são persistidas localmente em:

- [desktop/app_paths.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\app_paths.py)
- arquivo resultante: `%LOCALAPPDATA%\ProjectParallel\accessibility.json`

## 7.6 Preferências por usuário

Arquivo: [desktop/user_preferences.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\user_preferences.py)

### 7.6.1 O que persiste hoje

- filtros;
- busca;
- ordenação de tabelas;
- estado por widget;
- separação por usuário.

### 7.6.2 Armazenamento

Arquivo local:

- `%LOCALAPPDATA%\ProjectParallel\user_preferences.json`

## 7.7 Identidade da máquina

Arquivo: [desktop/machine_identity.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\machine_identity.py)

Funções:

- obter hostname;
- obter MAC address;
- inferir IP local a partir do alvo de rede;
- montar payload de identidade da estação.

Essa camada é usada principalmente no heartbeat e no monitoramento de máquinas.

## 7.8 Notificações

Arquivos principais:

- [desktop/core/notification_manager.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\core\notification_manager.py)
- [desktop/widgets/toast_notification.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\widgets\toast_notification.py)
- [desktop/widgets/notification_center.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\widgets\notification_center.py)
- [desktop/widgets/notification_badge.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\widgets\notification_badge.py)

### 7.8.1 NotificationManager

Responsável por:

- verificação periódica de novas notificações;
- controle de contador;
- modo não perturbe;
- cooldown por tipo;
- criação de notificações no backend;
- disparo de toasts.

### 7.8.2 ToastNotification

O popup de notificação atual foi refinado para:

- formato de cápsula;
- animação inspirada na Dynamic Island;
- abertura a partir do centro;
- fechamento recolhendo para o centro;
- posicionamento topo-central da aplicação.

### 7.8.3 Central de notificações

A central já oferece:

- filtros por status, prioridade e origem;
- busca rápida;
- seleção múltipla;
- marcação em lote;
- exclusão em lote;
- painel lateral de detalhes.

## 7.9 Login

Arquivo: [desktop/widgets/login_widget.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\widgets\login_widget.py)

Fluxo:

1. usuário informa o código;
2. o sistema consulta `usuario-preview`;
3. o nome do usuário é exibido;
4. o campo de senha é habilitado;
5. o login é realizado;
6. a aplicação abre a janela principal.

A tela foi refinada para:

- maior espaçamento;
- visual elegante/moderno;
- adaptação a tema claro e escuro;
- feedback visual mais claro.

## 7.10 Home e dashboard

Arquivo principal: [desktop/widgets/home_widget.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\widgets\home_widget.py)

### 7.10.1 Recursos da home

- cards operacionais refinados;
- painel técnico;
- status da rede local;
- malha LAN-to-LAN;
- gráficos em tempo real;
- histórico expandido de conectividade;
- comportamento dependente do perfil.

### 7.10.2 Papel da home

Ela funciona como dashboard operacional e também como camada de monitoramento resumido.

## 7.11 Relatórios

Arquivo: [desktop/widgets/relatorios_widget.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\widgets\relatorios_widget.py)

### 7.11.1 Abas principais

- Movimentações
- Estoque
- Pedidos
- Demandas

### 7.11.2 Recursos

- filtros por contexto da aba;
- busca rápida local;
- cards de resumo;
- painel lateral de detalhes;
- exportação para Excel;
- exportação para PDF.

## 7.12 Demandas

Arquivo: [desktop/widgets/demandas_widget.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\widgets\demandas_widget.py)

O módulo de demandas já suporta:

- fluxo padrão de gestão;
- fluxo de `solicitante`;
- visualização apenas das próprias demandas para quem é solicitante;
- integração com notificações;
- ações de assumir, concluir e cancelar de acordo com o perfil.

## 7.13 Atualizações

Arquivo da tela: [desktop/widgets/update_widget.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\widgets\update_widget.py)

Funções:

- verificar versão mais recente;
- exibir changelog;
- baixar asset da release;
- acionar instalação.

## 8. Atualizador automático

Arquivos principais:

- [desktop/updater.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\updater.py)
- [desktop/update_helper.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\update_helper.py)
- [desktop/update_helper.spec](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\update_helper.spec)

## 8.1 Histórico resumido

O projeto passou por uma fase de releases de ponte (`1.2.1` e `1.2.2`) para corrigir incompatibilidades do fluxo de atualização.

Como resposta, o repositório já começou uma refatoração mais segura do updater.

## 8.2 Fluxo atual em refatoração

### 8.2.1 UpdateChecker

- consulta a última release no GitHub;
- prefere o **ZIP portátil**;
- compara versão atual com `tag_name`.

### 8.2.2 Download

- baixa o asset selecionado para pasta temporária.

### 8.2.3 Instalação

Para ZIP portátil, o fluxo novo já contempla:

1. extração em staging;
2. validação do payload;
3. gravação de `update_state.json`;
4. cópia de `update_helper.exe` para execução externa;
5. encerramento do app principal;
6. troca de arquivos fora do processo principal;
7. reabertura do aplicativo;
8. confirmação no próximo startup.

### 8.2.4 Rollback

O helper já prevê:

- backup da instalação atual;
- rollback em caso de falha de cópia;
- tentativa de reabertura após rollback.

## 8.3 Arquivos locais de update

A infraestrutura local usa:

- `update_state.json`
- `update.log`
- pasta `updates/`

Todos são resolvidos por [desktop/app_paths.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\app_paths.py) dentro de `%LOCALAPPDATA%\ProjectParallel`.

## 8.4 Ponto de atenção

O mecanismo de atualização ainda está em estabilização. O backlog registra como prioridade máxima a reescrita completa e a validação intensiva desse fluxo antes de novas liberações mais ambiciosas.

## 9. Empacotamento e distribuição

## 9.1 Builder de release

Arquivo: [desktop/create_package.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\create_package.py)

### 9.1.1 Responsabilidades

- atualizar `desktop/version.json`;
- gerar build do `main.exe` via PyInstaller;
- gerar build do `update_helper.exe`;
- montar ZIP portátil;
- opcionalmente gerar instalador com Inno Setup.

### 9.1.2 Artefatos finais

Os artefatos são gerados em:

- [installer_output](C:\Users\João\Desktop\PROJECT_PARALLELv2\installer_output)

Padrões:

- `ProjectParallel_Portable_vX.Y.Z.zip`
- `ProjectParallel_Setup_vX.Y.Z.exe`

## 9.2 Instalador Inno Setup

Arquivo: [installer_script.iss](C:\Users\João\Desktop\PROJECT_PARALLELv2\installer_script.iss)

Características:

- instalação em `%LOCALAPPDATA%\Programs\ProjectParallel`;
- privilégios mínimos;
- suporte a ícone de área de trabalho;
- preservação de `.env` quando já existir;
- exclusão da pasta `_internal` antes da reinstalação.

## 9.3 Estratégia de releases

O projeto já adotou duas estratégias de publicação:

**Release completa**

- ZIP portátil;
- instalador `.exe`.

**Release de ponte**

- apenas ZIP portátil;
- usada para consertar o comportamento do updater em versões antigas.

## 10. Variáveis de ambiente e configuração

## 10.1 Backend

### Obrigatórias ou relevantes

- `DATABASE_URL`
- `SECRET_KEY`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `REDE_LOCAL_HOST`
- `REDE_LOCAL_PORT`
- `LOCAL_NETWORK_HOST`
- `LOCAL_NETWORK_PORT`

## 10.2 Desktop

- `API_URL`

## 10.3 Arquivo `.env`

O desktop usa uma estratégia híbrida:

- prefere `.env` externo da instalação;
- usa o `.env` empacotado apenas como fallback.

Essa lógica está em [desktop/app_paths.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\app_paths.py).

## 11. Persistência local fora do banco

Arquivos principais gerados no perfil do usuário:

- `accessibility.json`
- `user_preferences.json`
- `update_state.json`
- `update.log`
- pasta `updates/`

Objetivos:

- preservar acessibilidade entre sessões;
- preservar preferências por usuário;
- suportar atualização automática com staging e diagnóstico.

## 12. Execução local recomendada

## 12.1 Backend

Exemplo:

```powershell
cd C:\Users\João\Desktop\PROJECT_PARALLELv2\backend
python run.py
```

ou:

```powershell
cd C:\Users\João\Desktop\PROJECT_PARALLELv2\backend
python run_production.py
```

## 12.2 Desktop

Exemplo:

```powershell
cd C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop
python main.py
```

## 12.3 Build de release

Exemplo:

```powershell
cd C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop
python create_package.py
```

## 13. Pontos fortes atuais do projeto

- separação clara entre backend e desktop;
- cobertura funcional ampla do domínio operacional;
- controle de acesso já integrado à navegação e às ações;
- monitoramento de conectividade com LAN-to-LAN;
- notificações persistidas e refinadas;
- acessibilidade relativamente madura;
- relatórios e dashboards já em um nível bom de produto.

## 14. Pontos de atenção técnicos

### 14.1 Atualizador

É o principal ponto crítico atual do projeto e já está em processo de reestruturação.

### 14.2 Migração de schema

O projeto usa ajustes incrementais de compatibilidade no startup do backend. Isso é funcional, mas, no médio prazo, pode pedir uma estratégia formal de migração.

### 14.3 Qualidade textual do código-fonte

Alguns arquivos ainda exibem trechos com encoding antigo em comentários e strings históricas. A interface já recebeu várias correções textuais, mas ainda vale manter atenção a esse tema em próximas manutenções.

### 14.4 Versionamento operacional

O `version.json` pode ficar atrás do estado real do repositório quando uma refatoração é iniciada antes de uma nova release formal. Em documentação e suporte, é importante distinguir:

- **versão publicada do produto**;
- **estado atual do código em `main`**.

## 15. Próximos passos recomendados

Com base no estado atual do repositório e no backlog consolidado, os próximos passos mais importantes são:

1. concluir a reescrita do atualizador com helper externo, rollback e diagnóstico completo;
2. validar o fluxo de atualização em ambiente real, ponta a ponta;
3. continuar o refinamento de telas operacionais estratégicas, especialmente máquinas e colaboradores;
4. evoluir permissões para um modelo mais personalizável, além dos níveis pré-definidos;
5. avaliar a transição de marca para **Link Flow**;
6. discutir estratégia de hospedagem, versão web e versão mobile.

## 16. Arquivos-chave para manutenção

### Backend

- [backend/app/main.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\app\main.py)
- [backend/app/database.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\app\database.py)
- [backend/app/models.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\app\models.py)
- [backend/app/schemas.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\app\schemas.py)
- [backend/app/auth.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\app\auth.py)
- [backend/app/audit.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\app\audit.py)
- [backend/app/backup.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\backend\app\backup.py)

### Desktop

- [desktop/main.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\main.py)
- [desktop/api_client.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\api_client.py)
- [desktop/access_control.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\access_control.py)
- [desktop/accessibility_manager.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\accessibility_manager.py)
- [desktop/user_preferences.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\user_preferences.py)
- [desktop/updater.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\updater.py)
- [desktop/update_helper.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\update_helper.py)
- [desktop/create_package.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\create_package.py)

### Widgets estratégicos

- [desktop/widgets/main_window.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\widgets\main_window.py)
- [desktop/widgets/login_widget.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\widgets\login_widget.py)
- [desktop/widgets/home_widget.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\widgets\home_widget.py)
- [desktop/widgets/notification_center.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\widgets\notification_center.py)
- [desktop/widgets/toast_notification.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\widgets\toast_notification.py)
- [desktop/widgets/relatorios_widget.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\widgets\relatorios_widget.py)
- [desktop/widgets/update_widget.py](C:\Users\João\Desktop\PROJECT_PARALLELv2\desktop\widgets\update_widget.py)

---

Esta documentação foi gerada com base no estado atual do repositório em `main`, considerando tanto a versão publicada do desktop quanto as refatorações em andamento já presentes no código.
