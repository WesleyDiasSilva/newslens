"""Testes do grafo LangGraph (agent/graph.py).

Focados em estrutura e routing — não exercitam nodes que chamam LLM/MCP
(buscar_noticias, refinar_busca, gerar_briefing). Esses dependem de mocks
e ficam pra testes de integração.
"""
from langgraph.checkpoint.memory import MemorySaver


class TestState:
    def test_state_tem_campos_obrigatorios(self):
        from graph import NewsLensState

        esperados = {
            "tema",
            "noticias",
            "qualidade_suficiente",
            "historico",
            "briefing",
            "memoria",
            "num_chamadas",
        }
        assert esperados.issubset(NewsLensState.__annotations__.keys())


class TestRouteQualidade:
    def test_qualidade_suficiente_vai_pra_recuperar_historico(self):
        from graph import route_qualidade

        resultado = route_qualidade({"qualidade_suficiente": True})
        assert resultado == "recuperar_historico"

    def test_qualidade_insuficiente_vai_pra_refinar_busca(self):
        from graph import route_qualidade

        resultado = route_qualidade({"qualidade_suficiente": False})
        assert resultado == "refinar_busca"


class TestAvaliarQualidade:
    def test_acima_de_2500_chars_marca_true(self):
        from graph import avaliar_qualidade

        out = avaliar_qualidade({"noticias": "x" * 3000})
        assert out["qualidade_suficiente"] is True

    def test_abaixo_de_2500_chars_marca_false(self):
        from graph import avaliar_qualidade

        out = avaliar_qualidade({"noticias": "x" * 1000})
        assert out["qualidade_suficiente"] is False

    def test_borda_exatos_2500_chars_marca_true(self):
        from graph import avaliar_qualidade

        out = avaliar_qualidade({"noticias": "x" * 2500})
        assert out["qualidade_suficiente"] is True


class TestEstruturaGrafo:
    def test_compila_sem_erro(self):
        from graph import build_graph

        g = build_graph()
        assert g is not None

    def test_tem_todos_os_nodes_esperados(self):
        from graph import build_graph

        g = build_graph()
        nodes_presentes = set(g.nodes.keys())
        esperados = {
            "buscar_noticias",
            "avaliar_qualidade",
            "refinar_busca",
            "recuperar_historico",
            "gerar_briefing",
            "salvar_briefing",
        }
        assert esperados.issubset(nodes_presentes)

    def test_usa_memorysaver_como_checkpointer(self):
        from graph import build_graph

        g = build_graph()
        assert isinstance(g.checkpointer, MemorySaver)
