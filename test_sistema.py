"""
test_sistema.py — Testes unitários do ViolenciaBR
21 testes cobrindo todos os módulos + melhorias implementadas

Como rodar:
    python -m pytest testes/test_sistema.py -v 
    instalação prévia de pytest: pip install pytest
"""

import sys, os, unittest
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.processador_dados import ProcessadorDados
from src.analisador_dados import AnalisadorDados
from src.gerador_visualizacoes import GeradorVisualizacoes


def criar_df_teste() -> pd.DataFrame:
    """DataFrame já no formato long, como saído do processador."""
    return pd.DataFrame({
        "ano":          [2015,2015,2016,2016,2017,2017,2018,2018],
        "uf":           ["SP","RJ","SP","RJ","SP","RJ","SP","RJ"],
        "tipo_crime":   ["Feminicídio","Estupro"]*4,
        "total_vitimas":[100,200,120,210,140,220,160,230],
    })


def criar_csv_raw(caminho):
    """CSV no formato raw do FBSP para testar o ProcessadorDados."""
    pd.DataFrame({
        "ano":                         [2015,2016,2017,2018],
        "sigla_uf":                    ["SP","SP","RJ","RJ"],
        "quantidade_feminicidio":      [100, 120,  80,  90],
        "quantidade_estupro":          [200, 210, 180, 190],
        "quantidade_tentativa_estupro":[50,   55,  40,  45],
    }).to_csv(caminho, index=False)


class TestProcessadorDados(unittest.TestCase):

    def setUp(self):
        self.caminho = "testes/tmp_teste.csv"
        os.makedirs("testes", exist_ok=True)
        criar_csv_raw(self.caminho)
        self.proc = ProcessadorDados(self.caminho)

    def tearDown(self):
        if os.path.exists(self.caminho):
            os.remove(self.caminho)

    def test_arquivo_nao_encontrado(self):
        with self.assertRaises(FileNotFoundError):
            ProcessadorDados("nao/existe.csv")

    def test_retorna_dataframe(self):
        df = self.proc.carregar_e_limpar()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)

    def test_colunas_obrigatorias(self):
        df = self.proc.carregar_e_limpar()
        for col in ["ano","uf","tipo_crime","total_vitimas"]:
            self.assertIn(col, df.columns)

    def test_uf_maiusculo(self):
        df = self.proc.carregar_e_limpar()
        self.assertTrue(df["uf"].str.isupper().all())

    def test_ano_inteiro(self):
        df = self.proc.carregar_e_limpar()
        self.assertEqual(df["ano"].dtype, "int64")

    def test_sem_negativos(self):
        df = self.proc.carregar_e_limpar()
        self.assertGreaterEqual(df["total_vitimas"].min(), 0)

    def test_sem_duplicatas(self):
        df = self.proc.carregar_e_limpar()
        self.assertEqual(len(df), len(df.drop_duplicates()))


class TestAnalisadorDados(unittest.TestCase):

    def setUp(self):
        self.df = criar_df_teste()
        self.an = AnalisadorDados(self.df)

    def test_filtro_uf(self):
        df = self.an.aplicar_filtros(uf="SP")
        self.assertTrue((df["uf"] == "SP").all())

    def test_filtro_ano_inicio(self):
        df = self.an.aplicar_filtros(ano_inicio=2016)
        self.assertNotIn(2015, df["ano"].values)

    def test_filtro_ano_fim(self):
        df = self.an.aplicar_filtros(ano_fim=2016)
        self.assertNotIn(2017, df["ano"].values)

    def test_filtro_todos(self):
        df = self.an.aplicar_filtros(uf="TODOS")
        self.assertEqual(len(df), len(self.df))

    def test_kpi_total(self):
        self.an.aplicar_filtros()
        kpis = self.an.calcular_kpis()
        self.assertEqual(kpis["total_casos"], int(self.df["total_vitimas"].sum()))

    def test_kpi_variacao_float(self):
        self.an.aplicar_filtros()
        kpis = self.an.calcular_kpis()
        self.assertIsInstance(kpis["variacao_percentual"], float)

    def test_kpi_estado_critico(self):
        self.an.aplicar_filtros()
        kpis = self.an.calcular_kpis()
        self.assertIn(kpis["estado_critico"], ["SP","RJ"])

    def test_kpi_estado_maior_cresc(self):
        self.an.aplicar_filtros()
        kpis = self.an.calcular_kpis()
        self.assertNotEqual(kpis["estado_maior_cresc"], "")

    def test_filtro_vazio_kpis_zerados(self):
        self.an.aplicar_filtros(uf="AC", ano_inicio=1900, ano_fim=1901)
        kpis = self.an.calcular_kpis()
        self.assertEqual(kpis["total_casos"], 0)

    def test_serie_historica_colunas(self):
        self.an.aplicar_filtros()
        df = self.an.serie_historica()
        for col in ["ano","tipo_crime","total_vitimas"]:
            self.assertIn(col, df.columns)

    def test_ranking_estados_retorna_df(self):
        self.an.aplicar_filtros()
        df = self.an.dados_ranking_estados()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("total", df.columns)

    def test_heatmap_ordenado(self):
        self.an.aplicar_filtros()
        pivot = self.an.dados_heatmap()
        totais = pivot.sum(axis=1)
        self.assertTrue((totais.values[:-1] >= totais.values[1:]).all())

    def test_resumo_textual_nao_vazio(self):
        self.an.aplicar_filtros()
        resumo = self.an.gerar_resumo_textual("TODOS", 2015, 2018, "TODOS")
        self.assertIsInstance(resumo, str)
        self.assertGreater(len(resumo), 20)

    def test_exportar_csv(self):
        caminho = "testes/tmp_export.csv"
        self.an.aplicar_filtros()
        self.an.exportar_csv(caminho)
        self.assertTrue(os.path.exists(caminho))
        os.remove(caminho)


class TestGeradorVisualizacoes(unittest.TestCase):

    def setUp(self):
        self.df = criar_df_teste()
        self.an = AnalisadorDados(self.df)
        self.an.aplicar_filtros()
        self.gen = GeradorVisualizacoes()

    def tearDown(self):
        self.gen.fechar_figuras()

    def test_serie_retorna_figure(self):
        import matplotlib.pyplot as plt
        fig = self.gen.grafico_serie_historica(self.an.serie_historica())
        self.assertIsInstance(fig, plt.Figure)

    def test_heatmap_retorna_figure(self):
        import matplotlib.pyplot as plt
        fig = self.gen.grafico_heatmap(self.an.dados_heatmap())
        self.assertIsInstance(fig, plt.Figure)

    def test_ranking_retorna_figure(self):
        import matplotlib.pyplot as plt
        fig = self.gen.grafico_ranking_estados(self.an.dados_ranking_estados())
        self.assertIsInstance(fig, plt.Figure)

    def test_df_vazio_nao_quebra(self):
        import matplotlib.pyplot as plt
        fig = self.gen.grafico_serie_historica(pd.DataFrame())
        self.assertIsInstance(fig, plt.Figure)

    def test_salvar_png(self):
        self.gen.grafico_serie_historica(self.an.serie_historica())
        ok = self.gen.salvar_figura("testes/tmp_grafico.png")
        self.assertTrue(ok)
        if os.path.exists("testes/tmp_grafico.png"):
            os.remove("testes/tmp_grafico.png")




class TestGeradorPDF(unittest.TestCase):

    def setUp(self):
        import matplotlib
        matplotlib.use("Agg")
        self.df  = criar_df_teste()
        self.an  = AnalisadorDados(self.df)
        self.an.aplicar_filtros()
        from src.gerador_visualizacoes import GeradorVisualizacoes
        from src.gerador_pdf import GeradorPDF
        self.gen = GeradorVisualizacoes()
        self.pdf = GeradorPDF(self.an, self.gen)

    def tearDown(self):
        self.gen.fechar_figuras()
        if os.path.exists("testes/tmp_relatorio.pdf"):
            os.remove("testes/tmp_relatorio.pdf")

    def test_pdf_gerado_em_disco(self):
        """PDF deve ser criado no caminho especificado."""
        caminho = "testes/tmp_relatorio.pdf"
        resultado = self.pdf.gerar(
            caminho, uf="TODOS",
            ano_inicio=2015, ano_fim=2018,
            tipo_crime="Feminicídio"
        )
        self.assertTrue(os.path.exists(caminho))

    def test_pdf_nao_vazio(self):
        """PDF gerado deve ter tamanho maior que zero."""
        caminho = "testes/tmp_relatorio.pdf"
        self.pdf.gerar(caminho, uf="TODOS",
                       ano_inicio=2015, ano_fim=2018,
                       tipo_crime="Feminicídio")
        self.assertGreater(os.path.getsize(caminho), 0)

    def test_pdf_retorna_caminho(self):
        """gerar() deve retornar o caminho do arquivo."""
        caminho = "testes/tmp_relatorio.pdf"
        resultado = self.pdf.gerar(caminho, uf="TODOS",
                                    ano_inicio=2015, ano_fim=2018,
                                    tipo_crime="TODOS")
        self.assertEqual(resultado, caminho)


if __name__ == "__main__":
    unittest.main(verbosity=2)
