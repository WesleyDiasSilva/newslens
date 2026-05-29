"""Popula a tabela briefings com dados fictícios para testes manuais do RAG.

Cobre os últimos 21 dias com 8 briefings em 4 temas. Os embeddings são gerados
via OpenAI (text-embedding-3-small), então requer OPENAI_API_KEY e o container
do Postgres rodando.

Uso:
    python seed.py
"""
from datetime import datetime

from dotenv import load_dotenv

import memory

load_dotenv()


BRIEFINGS = [
    {
        "tema": "inteligência artificial",
        "criado_em": datetime(2026, 5, 9),
        "conteudo": (
            "# Reguladores europeus apertam compliance de IA generativa\n\n"
            "## Comissão Europeia publica diretrizes finais do AI Act\n"
            "A Comissão divulgou as diretrizes finais do AI Act para modelos de propósito geral, "
            "com prazo de adequação até dezembro de 2026 e multas que podem chegar a 7% do faturamento global.\n"
            "Fonte: https://euractiv.com/2026/05/09/ai-act-final-guidelines\n\n"
            "## OpenAI e Anthropic aderem ao código de conduta voluntário\n"
            "Antes do prazo regulatório, as principais labs confirmaram adesão ao código de conduta "
            "europeu, com compromissos de transparência sobre dados de treino e avaliações de risco sistêmico.\n"
            "Fonte: https://theverge.com/ai/2026/05/08/anthropic-openai-eu-code\n\n"
            "## Política interna de IA ainda é exceção no Brasil\n"
            "Estudo do Stanford HAI mostra que 73% das empresas brasileiras de médio porte ainda não têm "
            "política formal para uso de IA generativa por colaboradores.\n"
            "Fonte: https://stanford.edu/hai/2026/brasil-policy-report\n"
        ),
    },
    {
        "tema": "inteligência artificial",
        "criado_em": datetime(2026, 5, 17),
        "conteudo": (
            "# Modelos abertos ganham terreno sobre proprietários\n\n"
            "## Llama 4 supera GPT-5 turbo em raciocínio matemático\n"
            "A Meta liberou pesos do Llama 4 com janela de contexto de 2M tokens; o modelo lidera o "
            "benchmark MATH-500 com 91,3% de acerto, ultrapassando GPT-5 turbo pela primeira vez.\n"
            "Fonte: https://arxiv.org/abs/2026.05.1142\n\n"
            "## Mistral lança modelo de 200B parâmetros com licença comercial irrestrita\n"
            "A startup francesa publicou o Mistral-Large-3 sob licença Apache 2.0, sem restrições "
            "de uso comercial, em movimento que pressiona a estratégia da OpenAI no segmento enterprise.\n"
            "Fonte: https://techcrunch.com/2026/05/16/mistral-large-3-open\n\n"
            "## Hugging Face cruza marca de 2 milhões de modelos hospedados\n"
            "A plataforma reportou crescimento de 140% no último ano, com 60% dos uploads sendo "
            "variantes de fine-tuning de modelos abertos como Llama e Mistral.\n"
            "Fonte: https://huggingface.co/blog/2m-models-milestone\n"
        ),
    },
    {
        "tema": "inteligência artificial",
        "criado_em": datetime(2026, 5, 26),
        "conteudo": (
            "# Custos de inferência caem, mas demanda explode\n\n"
            "## Anthropic reduz preço do Claude Opus 4.7 em 35%\n"
            "A empresa atribui o corte a ganhos com prompt caching e otimizações no servidor; "
            "o preço por milhão de tokens de entrada cai para US$ 9,75, ainda acima do GPT-5.\n"
            "Fonte: https://anthropic.com/news/2026-05-26-pricing\n\n"
            "## Nvidia projeta receita recorde em data centers\n"
            "Resultados do 1T fiscal mostram crescimento de 78% em data center; chips Blackwell B200 "
            "estão esgotados até o Q4 e a empresa eleva guidance para o ano.\n"
            "Fonte: https://reuters.com/tech/2026/05/25/nvidia-q1-results\n\n"
            "## IDC: gasto global com IA generativa deve dobrar em 2026\n"
            "Relatório estima que empresas investirão US$ 297 bilhões em IA generativa este ano, com "
            "Brasil entre os dez maiores mercados pela primeira vez.\n"
            "Fonte: https://idc.com/getdoc.jsp?containerId=US52026\n"
        ),
    },
    {
        "tema": "mercado financeiro",
        "criado_em": datetime(2026, 5, 12),
        "conteudo": (
            "# Selic estável em 10,5% após reunião do Copom\n\n"
            "## Copom mantém taxa por unanimidade\n"
            "O comitê manteve a Selic em 10,5% a.a. pela terceira reunião consecutiva; ata cita "
            "inflação de serviços persistente e expectativas desancoradas como principais riscos.\n"
            "Fonte: https://bcb.gov.br/copom/atas/2026-05-12\n\n"
            "## Ibovespa fecha em alta de 1,2%\n"
            "O índice encerrou aos 142.380 pontos, impulsionado por commodities; Vale e Petrobras "
            "lideraram os ganhos após o anúncio do estímulo chinês ao setor de construção.\n"
            "Fonte: https://valor.globo.com/financas/2026/05/12/ibovespa-fecha\n\n"
            "## Dólar recua para R$ 5,18 após sinalização do Fed\n"
            "A moeda americana caiu 0,8% frente ao real depois que Powell sinalizou possíveis "
            "cortes de juros em junho, reforçando o apetite por emergentes.\n"
            "Fonte: https://reuters.com/markets/2026/05/12/brl-fed\n"
        ),
    },
    {
        "tema": "mercado financeiro",
        "criado_em": datetime(2026, 5, 23),
        "conteudo": (
            "# Temporada de balanços do 1T26 surpreende positivamente\n\n"
            "## Petrobras reporta lucro líquido de R$ 32 bilhões\n"
            "Resultado veio 18% acima do consenso de analistas; companhia anuncia dividendo "
            "extraordinário de R$ 1,85 por ação e mantém plano de capex em US$ 18 bilhões.\n"
            "Fonte: https://ri.petrobras.com.br/2026/1T26-release\n\n"
            "## Banco do Brasil eleva guidance e anuncia recompra\n"
            "O banco revisou para cima a projeção de lucro do ano e aprovou programa de recompra "
            "de R$ 4 bilhões em ações; ROE atingiu 21,3% no trimestre.\n"
            "Fonte: https://bb.com.br/ri/divulgacao-1T26\n\n"
            "## Vale supera projeções com produção recorde de minério\n"
            "A mineradora produziu 78,5 milhões de toneladas de minério no trimestre, recorde "
            "histórico; ação subiu 4% no dia da divulgação.\n"
            "Fonte: https://vale.com/investidores/2026-1T-resultado\n"
        ),
    },
    {
        "tema": "energia renovável",
        "criado_em": datetime(2026, 5, 14),
        "conteudo": (
            "# Solar distribuída ultrapassa 40 GW no Brasil\n\n"
            "## ANEEL confirma marca histórica\n"
            "A geração distribuída solar atingiu 40,2 GW de potência instalada, representando 16% "
            "da matriz elétrica brasileira; setor cresceu 22% em 12 meses.\n"
            "Fonte: https://aneel.gov.br/noticias/2026-05-14-gd-40gw\n\n"
            "## Leilão de transmissão atrai R$ 18 bilhões\n"
            "O certame da ANEEL contratou 14 lotes para escoar energia renovável do Nordeste; "
            "deságio médio foi de 41% sobre o teto regulatório.\n"
            "Fonte: https://epe.gov.br/leiloes/transmissao-2026-01\n\n"
            "## Nordeste lidera expansão solar\n"
            "Estados do Nordeste concentram 58% dos novos projetos solares fotovoltaicos em "
            "implantação, segundo anuário da ABSOLAR.\n"
            "Fonte: https://absolar.org.br/anuario-2026\n"
        ),
    },
    {
        "tema": "energia renovável",
        "criado_em": datetime(2026, 5, 21),
        "conteudo": (
            "# Hidrogênio verde avança no Pecém\n\n"
            "## Fortescue assina contrato de US$ 6 bilhões\n"
            "A australiana fechou contrato para hub de hidrogênio verde no Complexo do Pecém (CE); "
            "primeira fase prevê produção de 800 mil toneladas anuais a partir de 2029.\n"
            "Fonte: https://fortescue.com/news/2026/05/21/pecem-h2v-deal\n\n"
            "## Marco regulatório do hidrogênio é sancionado\n"
            "O governo federal aprovou o marco do hidrogênio de baixo carbono, com regime "
            "tributário especial e linhas de crédito de R$ 18,3 bilhões via BNDES.\n"
            "Fonte: https://planalto.gov.br/leis/2026/h2v-marco\n\n"
            "## Eólica offshore: leilão previsto para outubro\n"
            "O MME confirmou cronograma do primeiro leilão de eólica offshore do país; expectativa "
            "é mobilizar R$ 200 bilhões em investimentos até 2032.\n"
            "Fonte: https://mme.gov.br/eolica-offshore-leilao-2026\n"
        ),
    },
    {
        "tema": "agronegócio",
        "criado_em": datetime(2026, 5, 19),
        "conteudo": (
            "# Safra 25/26 fecha com produção recorde de grãos\n\n"
            "## Conab eleva projeção para 332 milhões de toneladas\n"
            "O 8º levantamento da safra projeta 332,1 mi t de grãos, alta de 4,8% sobre a safra "
            "anterior; soja e milho lideram, com clima favorável no Centro-Oeste.\n"
            "Fonte: https://conab.gov.br/safra-25-26-8o-levantamento\n\n"
            "## Soja brasileira mantém liderança nas exportações para China\n"
            "Em abril, o Brasil respondeu por 81% das importações chinesas de soja; preço FOB "
            "Paranaguá ficou em US$ 472 por tonelada, com prêmio reduzido.\n"
            "Fonte: https://comexstat.mdic.gov.br/relatorios/2026-04-soja\n\n"
            "## Plano Safra 26/27 será anunciado em junho\n"
            "O Mapa antecipa que o próximo Plano Safra terá foco em descarbonização da produção, "
            "com taxas reduzidas para sistemas integrados e agricultura de baixo carbono.\n"
            "Fonte: https://agricultura.gov.br/plano-safra-2627-anuncio\n"
        ),
    },
]


def run() -> None:
    memory.init_db()
    conn = memory._connect()
    try:
        with conn, conn.cursor() as cur:
            for b in BRIEFINGS:
                embedding = memory._embed(b["conteudo"])
                cur.execute(
                    "INSERT INTO briefings (tema, conteudo, embedding, criado_em) "
                    "VALUES (%s, %s, %s, %s)",
                    (
                        b["tema"],
                        b["conteudo"],
                        memory._vector_literal(embedding),
                        b["criado_em"],
                    ),
                )
        print(f"Inseridos {len(BRIEFINGS)} briefings.")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
