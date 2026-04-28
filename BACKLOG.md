# Backlog do Produto

Ideias registradas em 2026-04-24 e atualizadas em 2026-04-27 para evolucao futura do desktop.

## Atendimento e monitoramento

- Chat para atendimento rapido dentro do sistema.
- Monitoramento em tempo real das maquinas da mesma rede.
- Suporte a rede compartilhada entre empresas com comunicacao LAN-to-LAN entre pontos e lojas.

## Parametros e administracao

- Permitir edicao de parametros de empresa, cargos, departamentos e categorias.
- Criar um botao de edicao para os itens cadastrados dentro dessas tabelas de parametros.
- Implementar um sistema de nivel de acesso mais moderno e mais restritivo por perfil.
- Exibir mensagem visual de "Acesso nao permitido" quando o usuario tentar abrir uma tela sem permissao.
- Definir o comportamento de permissao em duas camadas: menu visivel por perfil e bloqueio real ao entrar na tela.
- Criar trilha de auditoria para registrar quem criou, editou ou excluiu itens sensiveis do sistema.
- Regras iniciais sugeridas:
  - Administrador com acesso total ao sistema, backup, parametros, telas e relatorios.
  - Gerencia com acesso a relatorios, movimentacoes e telas operacionais selecionadas.
  - Usuario comum com acesso a movimentacoes e relatorios basicos.

## Grids e widgets

- Realinhar o tamanho das colunas dos widgets para caber todo o conteudo do grid.
- Ajustar colunas que hoje cortam informacoes, incluindo cabecalhos como "Departamentos".
- Centralizar textos e fontes em todas as colunas.
- Implementar ordenacao em todos os grids ao clicar no cabecalho das colunas.
- Permitir ordenacao crescente e decrescente por codigo, nome e demais campos relevantes.
- Reforcar a prioridade da ordenacao dos grids com base nos testes recentes de uso.

## Acessibilidade e interface

- Criar uma tabela ou configuracao de acessibilidade em Parametros.
- Priorizar um MVP com tema, tamanho da fonte, escala da interface e navegacao por teclado.
- Salvar preferencias de acessibilidade por usuario.
- Tema previsto inicialmente: claro e escuro.
- Tamanho da fonte previsto inicialmente: pequeno, padrao e grande.
- Escala da interface prevista inicialmente: 100, 110, 125 e 150.
- Navegacao por teclado prevista inicialmente: ativa ou inativa.

## Pedidos e compras

- Implementar uma aba em Pedidos.
- Criar um campo para insercao de links de compra.
- Exemplos de links previstos: Mercado Livre, Amazon, Kabum e sites semelhantes.

## Experiencia e produtividade

- Salvar preferencias por usuario, como ordenacao do grid, largura das colunas e filtros mais usados.
- Melhorar mensagens de retorno para confirmar acoes e explicar erros com mais clareza.
- Destacar melhor os campos obrigatorios nas telas de cadastro.
- Implementar busca rapida dentro dos widgets por codigo, nome, status e outros campos relevantes.
- Criar um painel tecnico discreto com status da API, banco, rede e versao atual do app.
- Planejar atalhos operacionais para fluxos comuns depois que a navegacao por teclado estiver consolidada.

## Notificacoes e atualizacao em tempo real

- Adicionar um modo "Nao perturbe" para notificacoes.
- Corrigir o bug em que o card de manutencoes pendentes nao atualiza em tempo real quando o status e alterado.

## Movimentacoes e rastreabilidade

- Exigir confirmacao por senha sempre que registrar uma nova movimentacao, seja entrada ou saida.
- Aproveitar o sistema de logs ja existente para registrar confirmacoes e operacoes de movimentacao.

## Proximo passo quando retomarmos

- Quebrar cada bloco em tarefas menores.
- Definir prioridade entre UX, seguranca de acesso e monitoramento.
- Avaliar impacto de banco, API e desktop em cada item antes de desenvolver.
