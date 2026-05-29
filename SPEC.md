# SPEC — Memória do agente

## Visão geral

A funcionalidade de memória permite que o agente reconheça quando um tema já foi consultado antes e use os briefings anteriores como contexto para enriquecer o briefing atual. O objetivo é transformar briefings isolados em uma narrativa contínua: o usuário deve perceber o que mudou, o que evoluiu e o que se repetiu desde a última consulta sobre o mesmo tema.

A memória é uma camada de contexto. Ela não substitui a busca de notícias do dia — ela cruza o que foi encontrado hoje com o que já foi reportado em consultas anteriores sobre o mesmo tema.

## Inputs

- Um pedido de briefing contendo `tema` e `modo` (igual ao endpoint atual).
- O conjunto de notícias coletadas na execução corrente.
- O histórico de briefings anteriores associados ao mesmo tema, quando existir.
- A data/hora da consulta atual.

**Validação:** `tema` vazio ou contendo apenas espaços em branco é rejeitado com HTTP 422 antes de qualquer processamento (não consome tokens nem hit no banco).

## Outputs

- Um briefing no formato já existente (título, resumo, fonte por notícia), acrescido de:
  - Marcação por notícia indicando se é **inédita** ou **continuação** de algo já reportado.
  - Uma seção de **mudanças desde o último briefing**: fatos que evoluíram, foram contraditos ou atualizados.
  - Referências explícitas a briefings anteriores quando uma notícia atual estiver diretamente conectada a uma notícia passada.
- Metadados de memória sob a chave `memoria` na resposta, com as seguintes chaves:
  - `briefings_anteriores_consultados` (int ≥ 0): quantidade **total** de briefings persistidos para o mesmo tema normalizado.
  - `primeira_vez` (bool): `true` se e somente se `briefings_anteriores_consultados == 0`.
  - `data_briefing_mais_antigo` (string ISO date ou `null`): data do briefing persistido mais antigo do mesmo tema; `null` se não houver histórico.
  - `disponivel` (bool): `true` se a camada de memória respondeu sem erro; `false` em modo de fallback (banco indisponível, falha de embedding, etc.).

## Arquitetura

- **Banco:** PostgreSQL com a extensão PGVector instalada (`CREATE EXTENSION vector`). A tabela `briefings` armazena `tema`, `conteudo`, `embedding vector(1536)` e `criado_em`.
- **Modelo de embedding:** OpenAI `text-embedding-3-small`, gerando vetores de **1536 dimensões** — mesma dimensionalidade configurada na coluna `embedding`.
- **Busca:** similaridade por **distância coseno** via operador `<=>` do pgvector (`ORDER BY embedding <=> query_vec`), ordenando do mais próximo (semanticamente similar) para o mais distante.
- **Ingestão:** cada briefing gerado pelo endpoint é automaticamente indexado — o `conteudo` é convertido em embedding e persistido em uma única transação ao final da geração, antes do retorno HTTP.
- **Escopo da memória:** **exclusivo por tema normalizado**. Temas distintos nunca compartilham memória — nem para contagem, nem para retrieval.
- **Normalização de tema:** `lower()` + `strip()` aplicados antes de qualquer comparação ou agregação. Variações triviais (caixa, espaços nas bordas) compartilham memória; variações estruturais (`"eleições"` vs `"eleições 2026"`) são temas distintos. Acentos e caracteres unicode são preservados (`"café"` ≠ `"cafe"`).
- **Contagem de histórico:** o campo `briefings_anteriores_consultados` reflete o **total** de briefings persistidos para o mesmo tema normalizado, **independente** de quantos são injetados no prompt do agente.
- **Retrieval para o prompt:** dentro do subconjunto de mesmo tema normalizado, os **top-3 mais similares** semanticamente (via `embedding <=> query_vec`) são selecionados e injetados no contexto do agente. Se o subconjunto tem ≤ 3 briefings, todos são injetados.
- **Chunking:** o **briefing completo é a unidade de indexação** — um único chunk por briefing, sem split por seção ou notícia. Preserva o contexto narrativo do briefing como um todo durante o retrieval.
- **Resiliência:** a camada de memória é encapsulada em um handle único e patchável no módulo `main` (atributo do módulo), permitindo substituição em testes e fallback em produção. Se a camada falhar (banco indisponível, erro de embedding), o endpoint executa em **fallback**: gera o briefing sem contexto histórico e retorna `memoria.disponivel = false`. O briefing é sempre entregue.

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
- **Tema vazio ou só espaços:** rejeitado com HTTP 422 antes de qualquer processamento; não consome tokens nem hit no banco.
- **Histórico grande (>20 briefings do mesmo tema):** `briefings_anteriores_consultados` reflete o total real (≥ 20); o retrieval injetado no prompt continua limitado a top-3 mais similares; o briefing atual sai sem latência adicional significativa.
- **Briefings antigos ficaram irrelevantes** (ex.: tema mudou de fase): devem continuar acessíveis, mas o agente deve sinalizar quando estiver tratando de algo claramente novo dentro do mesmo tema.
- **Concorrência de mesmo tema:** múltiplas requisições simultâneas são serializadas pela transação de INSERT no Postgres; todas devem completar com HTTP 200 sem corromper a memória, e a contagem final reflete a ordem real de persistência.
