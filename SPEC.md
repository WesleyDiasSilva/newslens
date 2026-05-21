# SPEC — Memória do agente

## Visão geral

A funcionalidade de memória permite que o agente reconheça quando um tema já foi consultado antes e use os briefings anteriores como contexto para enriquecer o briefing atual. O objetivo é transformar briefings isolados em uma narrativa contínua: o usuário deve perceber o que mudou, o que evoluiu e o que se repetiu desde a última consulta sobre o mesmo tema.

A memória é uma camada de contexto. Ela não substitui a busca de notícias do dia — ela cruza o que foi encontrado hoje com o que já foi reportado em consultas anteriores sobre o mesmo tema.

## Inputs

- Um pedido de briefing contendo `tema` e `modo` (igual ao endpoint atual).
- O conjunto de notícias coletadas na execução corrente.
- O histórico de briefings anteriores associados ao mesmo tema, quando existir.
- A data/hora da consulta atual.

## Outputs

- Um briefing no formato já existente (título, resumo, fonte por notícia), acrescido de:
  - Marcação por notícia indicando se é **inédita** ou **continuação** de algo já reportado.
  - Uma seção de **mudanças desde o último briefing**: fatos que evoluíram, foram contraditos ou atualizados.
  - Referências explícitas a briefings anteriores quando uma notícia atual estiver diretamente conectada a uma notícia passada.
- Metadados na resposta indicando:
  - Quantos briefings anteriores foram consultados.
  - A data do briefing mais antigo considerado.
  - Se foi a primeira vez que o tema foi consultado.

## Comportamentos esperados

- Reconhecer que dois pedidos com o mesmo tema (mesmo com variações triviais de espaço/caixa) compartilham memória.
- Diferenciar notícias inéditas de notícias que apenas dão continuidade a fatos já reportados.
- Sinalizar quando uma notícia atual contradiz ou atualiza algo afirmado em briefing anterior.
- Manter os briefings em ordem cronológica por tema, permitindo identificar a evolução do assunto.
- Funcionar normalmente na primeira consulta de um tema (sem memória disponível): o briefing sai igual ao comportamento atual e os metadados indicam ausência de histórico.
- Persistir cada briefing gerado para que esteja disponível em consultas futuras do mesmo tema.

## Comportamentos proibidos

- Inventar briefings passados que nunca aconteceram.
- Misturar memória entre temas distintos.
- Usar a memória para reescrever ou alterar fatos da notícia atual — memória enriquece, nunca substitui o que foi coletado hoje.
- Expor ao usuário detalhes internos de armazenamento (IDs, caminhos, estruturas).
- Apagar briefings antigos de forma silenciosa.
- Bloquear ou atrasar significativamente o briefing atual quando a memória estiver indisponível — a funcionalidade deve degradar para o comportamento sem memória.

## Casos de borda

- **Primeira consulta do tema:** nenhuma memória; o briefing deve sair normalmente e os metadados indicar `primeira_vez = true`.
- **Variações superficiais do tema:** `"eleições 2026"`, `"Eleições 2026"` e `"eleições 2026 "` devem compartilhar memória; `"eleições"` e `"eleições 2026"` são temas distintos.
- **Notícia atual que contradiz briefing anterior:** ambas devem aparecer; a contradição deve ser sinalizada.
- **Notícia idêntica à de um briefing recente:** deve ser marcada como continuação, não como novidade.
- **Memória indisponível ou corrompida:** o briefing atual sai normalmente, com aviso nos metadados de que a memória não pôde ser consultada.
- **Histórico muito longo:** o sistema deve priorizar os briefings mais recentes e/ou mais relevantes, sem travar nem estourar limites do modelo.
- **Briefings antigos ficaram irrelevantes** (ex.: tema mudou de fase): devem continuar acessíveis, mas o agente deve sinalizar quando estiver tratando de algo claramente novo dentro do mesmo tema.
- **Dois pedidos simultâneos para o mesmo tema:** ambos devem completar sem corromper a memória; a ordem de persistência deve refletir a ordem real de execução.
