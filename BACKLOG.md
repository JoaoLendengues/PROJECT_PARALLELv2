# Backlog do Produto

Backlog ativo do Project Parallel, revisado em 2026-05-11.

Este arquivo concentra apenas o que ainda faz sentido como próximo trabalho, refinamento ou ideia nova. Itens já entregues foram removidos para deixar a retomada mais objetiva.

## Prioridade imediata

- Refinar o atualizador automático com helper externo, staging validado, estado pendente e relançamento confiável do app.
- Concluir rollback e recuperação automática quando a atualização falhar no meio do processo.
- Melhorar a telemetria local do updater com `update.log`, `update_state.json` e mensagens mais claras na interface.
- Gerar uma build interna `1.2.3B` para teste do novo mecanismo de atualização.
- Validar o fluxo `1.2.3B -> 1.2.4` antes de publicar uma nova release ampla.

## Monitoramento e conectividade

- Evoluir o monitoramento de máquinas para destacar servidores e hosts críticos.
- Enriquecer o diagnóstico da malha LAN-to-LAN com leitura mais analítica de estabilidade e indisponibilidade acumulada.
- Diferenciar melhor, no monitoramento, falha de máquina, falha de rota e falha de unidade.
- Avaliar integração futura com recursos nativos do firewall Netdeep, caso valha a pena tecnicamente.

## Atendimento e demandas

- Evoluir o fluxo do perfil `solicitante` com histórico mais rico das próprias demandas.
- Estudar uma segunda fase de autoatendimento com widget leve ou abertura rápida de chamados.
- Definir se o atendimento evolui para respostas ou encaminhamento dentro da própria demanda antes de virar chat completo.

## Relatórios

- Fazer a rodada final de refinamento da tela de relatórios.
- Melhorar estados vazios, agrupamento visual e leitura das tabelas.
- Refinar a experiência de exportação com nome de arquivo mais amigável e contexto dos filtros aplicados.
- Avaliar se vale adicionar mais indicadores de resumo por aba.

## Notificações

- Fazer uma segunda rodada de refinamento da central de notificações.
- Avaliar agrupamento por tempo (`Agora`, `Hoje`, `Ontem` e `Mais antigas`).
- Aproximar ainda mais a central do padrão visual elegante/tech usado nos pop-ups.
- Estudar filtros rápidos extras, como `só não lidas`, `só críticas` e `só acionáveis`.

## Experiência e produtividade

- Salvar largura das colunas por usuário, além de filtros, busca e ordenação.
- Avaliar salvar a última aba aberta em telas maiores, como Relatórios e Parâmetros.
- Planejar atalhos operacionais para fluxos recorrentes, depois de estabilizar o updater.
- Seguir a passada final de acessibilidade e consistência visual, tela por tela.

## Pedidos e compras

- Avaliar se ainda faz sentido criar uma aba extra em `Pedidos`.
- Estudar melhorias futuras no fluxo de links de compra, como abrir histórico, copiar link e validar domínios mais comuns.

## Auditoria e segurança

- Fazer uma terceira rodada da auditoria ampla, cobrindo mais ações administrativas e operacionais sensíveis.
- Revisar se existem pontos de permissão que ainda dependem mais do desktop do que do backend.

## Ideias novas para avaliar

- Criar um checklist interno de publicação de release para não repetir erros de updater e assets.
- Criar uma tela ou painel de diagnóstico da atualização para suporte técnico.
- Definir uma política clara de releases:
  - release de ponte;
  - release técnica;
  - release funcional.
- Avaliar um canal interno de testes antes de marcar uma versão como `Latest`.
