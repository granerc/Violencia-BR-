"""
gerador_pdf.py
==============
Gera um relatório PDF completo com:
  - Capa com título, filtros ativos e data
  - Página de KPIs
  - Página de resumo textual automático
  - Gráfico de série histórica (linhas)
  - Gráfico de heatmap
  - Gráfico de ranking de estados
  - Rodapé com fonte dos dados em todas as páginas

Usa apenas matplotlib (já instalado) — sem dependências novas

Como usar:
    from src.gerador_pdf import GeradorPDF
    gen = GeradorPDF(analisador, gerador_visualizacoes)
    gen.gerar(caminho="relatorio.pdf", uf="SP", ano_inicio=2015,
              ano_fim=2021, tipo_crime="Feminicídio")
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime


FONTE_DADOS  = "Fonte: Fórum Brasileiro de Segurança Pública (FBSP) | basedosdados.org"
COR_DESTAQUE = "#C0392B"
COR_CINZA    = "#7F8C8D"
COR_ESCURO   = "#2C3E50"


class GeradorPDF:
    """
    Gera relatório PDF completo do ViolenciaBR.

    Parâmetros
    ----------
    analisador  : instância de AnalisadorDados já com filtros aplicados
    gerador_viz : instância de GeradorVisualizacoes
    """

    def __init__(self, analisador, gerador_viz):
        self.analisador  = analisador
        self.gerador_viz = gerador_viz

    def gerar(
        self,
        caminho: str,
        uf: str = "TODOS",
        ano_inicio: int = None,
        ano_fim: int = None,
        tipo_crime: str = "TODOS"
    ) -> str:
        """
        Gera o PDF e salva em disco.

        Retorna o caminho do arquivo gerado.
        """
        kpis   = self.analisador.calcular_kpis()
        resumo = self.analisador.gerar_resumo_textual(
            uf, ano_inicio, ano_fim, tipo_crime)

        with PdfPages(caminho) as pdf:
            self._pagina_capa(pdf, uf, ano_inicio, ano_fim, tipo_crime)
            self._pagina_kpis(pdf, kpis, uf, ano_inicio, ano_fim, tipo_crime)
            self._pagina_resumo(pdf, resumo, uf, ano_inicio, ano_fim, tipo_crime)
            self._pagina_grafico_linhas(pdf, uf, ano_inicio, ano_fim, tipo_crime)
            self._pagina_heatmap(pdf, uf, ano_inicio, ano_fim, tipo_crime)
            self._pagina_ranking(pdf, uf, ano_inicio, ano_fim, tipo_crime)
            self._pagina_mapa(pdf, uf, ano_inicio, ano_fim, tipo_crime)
            self._adicionar_metadados(pdf, uf, ano_inicio, ano_fim, tipo_crime)

        print(f"PDF gerado: {caminho}")
        return caminho

    # Páginas

    def _pagina_capa(self, pdf, uf, ano_inicio, ano_fim, tipo_crime):
        fig = plt.figure(figsize=(8.27, 11.69))  # A4
        ax  = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

        # Faixa vermelha no topo
        ax.add_patch(mpatches.FancyBboxPatch(
            (0, 0.82), 1, 0.18,
            boxstyle="square,pad=0",
            facecolor=COR_DESTAQUE, edgecolor="none"
        ))

        # Título principal
        ax.text(0.5, 0.91, "ViolenciaBR",
                ha="center", va="center",
                fontsize=32, fontweight="bold", color="white")
        ax.text(0.5, 0.86,
                "Dashboard de Violência contra a Mulher no Brasil",
                ha="center", va="center",
                fontsize=13, color="#FADBD8")

        # Linha divisória
        ax.axhline(0.80, color="#DDE1E7", linewidth=0.8)

        # Informações do relatório
        crime_label = tipo_crime if tipo_crime != "TODOS" else "Todos os tipos"
        regiao      = uf if uf != "TODOS" else "Brasil (todos os estados)"
        periodo     = f"{ano_inicio} a {ano_fim}" if ano_inicio and ano_fim else "Período completo"

        infos = [
            ("Crime analisado",  crime_label),
            ("Região",           regiao),
            ("Período",          periodo),
            ("Data do relatório", datetime.now().strftime("%d/%m/%Y %H:%M")),
        ]

        y = 0.72
        for label, valor in infos:
            ax.text(0.12, y, label + ":",
                    fontsize=11, color=COR_CINZA, fontweight="bold")
            ax.text(0.45, y, valor,
                    fontsize=11, color=COR_ESCURO)
            y -= 0.07

        # Linha divisória inferior
        ax.axhline(y - 0.02, color="#DDE1E7", linewidth=0.8)

        # Descrição
        ax.text(0.5, y - 0.08,
                "Este relatório foi gerado automaticamente pelo sistema ViolenciaBR\n"
                "com base nos dados do Fórum Brasileiro de Segurança Pública (FBSP).\n"
                "Público-alvo: jornalistas de dados e gestores públicos municipais.",
                ha="center", va="top",
                fontsize=10, color=COR_CINZA,
                linespacing=1.7)

        # Rodapé
        self._rodape(ax)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    def _pagina_kpis(self, pdf, kpis, uf, ano_inicio, ano_fim, tipo_crime):
        fig = plt.figure(figsize=(8.27, 11.69))
        ax  = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

        self._cabecalho_pagina(ax, "Indicadores-Chave (KPIs)")

        cards = [
            ("Total de casos",          str(f"{kpis['total_casos']:,}".replace(",",".")), COR_DESTAQUE),
            ("Variação % no período",
             f"{'+'if kpis['variacao_percentual']>=0 else ''}{kpis['variacao_percentual']}%",
             "#E67E22"),
            ("Estado mais afetado",     kpis["estado_critico"],  "#8E44AD"),
            ("Maior crescimento %",     kpis["estado_maior_cresc"], "#16A085"),
        ]

        posicoes = [(0.05, 0.62), (0.55, 0.62), (0.05, 0.38), (0.55, 0.38)]
        for (x, y), (label, valor, cor) in zip(posicoes, cards):
            # Card
            ax.add_patch(mpatches.FancyBboxPatch(
                (x, y), 0.40, 0.18,
                boxstyle="round,pad=0.01",
                facecolor="#F8F9FA", edgecolor="#DDE1E7", linewidth=0.8
            ))
            ax.text(x + 0.20, y + 0.13, label,
                    ha="center", fontsize=10, color=COR_CINZA)
            ax.text(x + 0.20, y + 0.07, valor,
                    ha="center", fontsize=22, fontweight="bold", color=cor)

        # Contexto
        crime_label = tipo_crime if tipo_crime != "TODOS" else "todos os crimes"
        regiao      = f"em {uf}" if uf != "TODOS" else "no Brasil"
        ax.text(0.5, 0.24,
                f"Filtros ativos: {crime_label} | {regiao} | {ano_inicio}–{ano_fim}",
                ha="center", fontsize=9, color=COR_CINZA, style="italic")

        self._rodape(ax)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    def _pagina_resumo(self, pdf, resumo, uf, ano_inicio, ano_fim, tipo_crime):
        fig = plt.figure(figsize=(8.27, 11.69))
        ax  = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

        self._cabecalho_pagina(ax, "Resumo Analítico")

        # Texto do resumo — quebra automática
        ax.text(0.10, 0.74, resumo,
                ha="left", va="top",
                fontsize=11, color=COR_ESCURO,
                linespacing=1.9,
                wrap=True,
                transform=ax.transAxes if False else ax.transData)

        self._rodape(ax)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    def _pagina_grafico_linhas(self, pdf, uf, ano_inicio, ano_fim, tipo_crime):
        serie = self.analisador.serie_historica()
        fig   = self.gerador_viz.grafico_serie_historica(
            serie, uf=uf, ano_inicio=ano_inicio,
            ano_fim=ano_fim, tipo_crime=tipo_crime)
        fig.set_size_inches(8.27, 5.5)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    def _pagina_heatmap(self, pdf, uf, ano_inicio, ano_fim, tipo_crime):
        pivot = self.analisador.dados_heatmap()
        fig   = self.gerador_viz.grafico_heatmap(
            pivot, uf=uf, ano_inicio=ano_inicio,
            ano_fim=ano_fim, tipo_crime=tipo_crime)
        fig.set_size_inches(8.27, 7.5)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    def _pagina_ranking(self, pdf, uf, ano_inicio, ano_fim, tipo_crime):
        ranking = self.analisador.dados_ranking_estados()
        fig     = self.gerador_viz.grafico_ranking_estados(
            ranking, uf=uf, ano_inicio=ano_inicio,
            ano_fim=ano_fim, tipo_crime=tipo_crime)
        fig.set_size_inches(8.27, 6.5)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    # Auxiliares visuais

    def _cabecalho_pagina(self, ax, titulo: str):
        """Faixa de cabeçalho padrão de cada página interna."""
        ax.add_patch(mpatches.FancyBboxPatch(
            (0, 0.91), 1, 0.09,
            boxstyle="square,pad=0",
            facecolor=COR_DESTAQUE, edgecolor="none"
        ))
        ax.text(0.05, 0.955, "ViolenciaBR",
                fontsize=10, fontweight="bold", color="white", va="center")
        ax.text(0.5, 0.955, titulo,
                ha="center", fontsize=14, fontweight="bold",
                color="white", va="center")

    def _rodape(self, ax):
        """Rodapé padrão com fonte dos dados."""
        ax.axhline(0.04, color="#DDE1E7", linewidth=0.5)
        ax.text(0.5, 0.02, FONTE_DADOS,
                ha="center", fontsize=7,
                color=COR_CINZA, style="italic")


    def _pagina_mapa(self, pdf, uf, ano_inicio, ano_fim, tipo_crime):
        ranking = self.analisador.dados_ranking_estados()
        fig     = self.gerador_viz.grafico_mapa_brasil(
            ranking, uf=uf, ano_inicio=ano_inicio,
            ano_fim=ano_fim, tipo_crime=tipo_crime)
        fig.set_size_inches(8.27, 8.27)
        pdf.savefig(fig, bbox_inches="tight")
        import matplotlib.pyplot as plt
        plt.close(fig)

    def _adicionar_metadados(self, pdf, uf, ano_inicio, ano_fim, tipo_crime):
        """Metadados do PDF (visíveis nas propriedades do arquivo)."""
        crime_label = tipo_crime if tipo_crime != "TODOS" else "Todos os crimes"
        pdf.infodict().update({
            "Title":    "ViolenciaBR — Relatório de Análise",
            "Author":   "ViolenciaBR Dashboard",
            "Subject":  f"{crime_label} | {uf} | {ano_inicio}–{ano_fim}",
            "Keywords": "feminicídio, violência doméstica, FBSP, segurança pública",
            "Creator":  "ViolenciaBR — Disciplina Novas Tecnologias UCB",
        })
