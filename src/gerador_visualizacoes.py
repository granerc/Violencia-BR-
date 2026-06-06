"""
gerador_visualizacoes.py
========================
Gera os gráficos do sistema com melhorias:
- Cores fixas por tipo de crime (vermelho/azul/laranja)
- Título dinâmico baseado no filtro ativo
- Heatmap ordenado pelo total decrescente
- Gráfico de barras horizontais (ranking de estados)
- Método salvar_figura() para exportar PNG
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
try:
    import mplcursors
    MPLCURSORS_OK = True
except ImportError:
    MPLCURSORS_OK = False
import pandas as pd

# Cores fixas por tipo de crime — consistentes em todos os gráficos
CORES_CRIME = {
    "Feminicídio":         "#C0392B",   # vermelho escuro
    "Estupro":             "#2980B9",   # azul
    "Tentativa de Estupro":"#E67E22",   # laranja
    "default":             "#7F8C8D",
}

FONTE_DADOS = "Fonte: Fórum Brasileiro de Segurança Pública (FBSP) | basedosdados.org"


class GeradorVisualizacoes:

    def __init__(self):
        sns.set_theme(style="whitegrid", font_scale=0.95)
        plt.rcParams.update({
            "font.family":       "DejaVu Sans",
            "axes.spines.top":   False,
            "axes.spines.right": False,
        })
        self._ultima_figura = None  # para exportação PNG

    # Gráfico 1 — Série histórica (linhas)

    def grafico_serie_historica(
        self,
        df: pd.DataFrame,
        uf: str = "TODOS",
        ano_inicio: int = None,
        ano_fim: int = None,
        tipo_crime: str = "TODOS"
    ) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(8, 4.5))

        if df.empty:
            ax.text(0.5, 0.5, "Nenhum dado para os filtros selecionados.",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=12, color="#7F8C8D")
            self._adicionar_rodape(fig)
            self._ultima_figura = fig
            return fig

        linhas = []
        for tipo in df["tipo_crime"].unique():
            dados = df[df["tipo_crime"] == tipo].sort_values("ano")
            cor   = CORES_CRIME.get(tipo, CORES_CRIME["default"])
            linha, = ax.plot(dados["ano"], dados["total_vitimas"],
                    marker="o", linewidth=2.2, markersize=6,
                    color=cor, label=tipo,
                    picker=True, pickradius=6)
            linha._dados_ano   = dados["ano"].tolist()
            linha._dados_total = dados["total_vitimas"].tolist()
            linha._tipo_crime  = tipo
            linhas.append(linha)
            if not dados.empty:
                ult = dados.iloc[-1]
                ax.annotate(f"{int(ult['total_vitimas'])}",
                            xy=(ult["ano"], ult["total_vitimas"]),
                            xytext=(5, 3), textcoords="offset points",
                            fontsize=8, color=cor)

        # Tooltip interativo ao passar o mouse
        if MPLCURSORS_OK and linhas:
            cursor = mplcursors.cursor(linhas, hover=True)

            @cursor.connect("add")
            def on_add(sel):
                idx   = int(round(sel.index))
                linha = sel.artist
                anos  = linha._dados_ano
                total = linha._dados_total
                crime = linha._tipo_crime
                if 0 <= idx < len(anos):
                    ano = anos[idx]
                    val = int(total[idx])
                    sel.annotation.set_text(
                        f"{crime}\nAno: {ano}\nCasos: {val:,}".replace(",", ".")
                    )
                    sel.annotation.get_bbox_patch().set(
                        facecolor="white",
                        edgecolor="#C0392B",
                        alpha=0.95,
                        boxstyle="round,pad=0.4"
                    )
                    sel.annotation.set_fontsize(9)

        # Título dinâmico
        titulo = self._montar_titulo(uf, ano_inicio, ano_fim, tipo_crime)
        ax.set_title(titulo, fontsize=12, fontweight="bold", pad=12)
        ax.set_xlabel("Ano", fontsize=10)
        ax.set_ylabel("Número de casos", fontsize=10)
        ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", ".")))
        ax.legend(loc="upper left", frameon=False, fontsize=9)

        # Nota sobre feminicídio se relevante
        if tipo_crime in ("Feminicídio", "TODOS") and (ano_inicio is None or ano_inicio < 2015):
            ax.text(0.01, -0.14,
                    "* Dados de feminicídio disponíveis a partir de 2015 (Lei nº 13.104)",
                    transform=ax.transAxes, fontsize=7.5, color="#888888", style="italic")

        self._adicionar_rodape(fig)
        fig.tight_layout()
        self._ultima_figura = fig
        return fig

    # Gráfico 2 — Heatmap

    def grafico_heatmap(
        self,
        df_pivot: pd.DataFrame,
        uf: str = "TODOS",
        ano_inicio: int = None,
        ano_fim: int = None,
        tipo_crime: str = "TODOS"
    ) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(10, 7))

        if df_pivot.empty:
            ax.text(0.5, 0.5, "Nenhum dado para os filtros selecionados.",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=12, color="#7F8C8D")
            self._adicionar_rodape(fig)
            self._ultima_figura = fig
            return fig

        sns.heatmap(df_pivot, ax=ax, cmap="YlOrRd",
                    linewidths=0.4, linecolor="#EEEEEE",
                    annot=True, fmt=".0f", annot_kws={"size": 7},
                    cbar_kws={"label": "Nº de casos", "shrink": 0.8})

        titulo = self._montar_titulo(uf, ano_inicio, ano_fim, tipo_crime)
        ax.set_title(titulo + "\n(estados ordenados por total de casos)",
                     fontsize=12, fontweight="bold", pad=12)
        ax.set_xlabel("Ano", fontsize=10)
        ax.set_ylabel("Estado (UF)", fontsize=10)
        ax.tick_params(axis="x", rotation=45, labelsize=8)
        ax.tick_params(axis="y", rotation=0,  labelsize=8)

        self._adicionar_rodape(fig)
        fig.tight_layout()
        self._ultima_figura = fig
        return fig

    # Gráfico 3 — Ranking de estados (barras horizontais)

    def grafico_ranking_estados(
        self,
        df_ranking: pd.DataFrame,
        uf: str = "TODOS",
        ano_inicio: int = None,
        ano_fim: int = None,
        tipo_crime: str = "TODOS"
    ) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(8, 6))

        if df_ranking.empty:
            ax.text(0.5, 0.5, "Nenhum dado para os filtros selecionados.",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=12, color="#7F8C8D")
            self._adicionar_rodape(fig)
            self._ultima_figura = fig
            return fig

        # Limita aos 15 maiores para não poluir
        df_plot = df_ranking.tail(15)

        cor_principal = CORES_CRIME.get(tipo_crime, "#C0392B") \
            if tipo_crime != "TODOS" else "#C0392B"

        barras = ax.barh(df_plot["uf"], df_plot["total"],
                         color=cor_principal, alpha=0.85, height=0.65)

        # Rótulo com valor em cada barra
        for barra in barras:
            largura = barra.get_width()
            ax.text(largura + largura * 0.01, barra.get_y() + barra.get_height() / 2,
                    f"{int(largura):,}".replace(",", "."),
                    va="center", ha="left", fontsize=8, color="#555555")

        titulo = self._montar_titulo(uf, ano_inicio, ano_fim, tipo_crime)
        ax.set_title(titulo + "\n(ranking por estado)",
                     fontsize=12, fontweight="bold", pad=12)
        ax.set_xlabel("Número de casos", fontsize=10)
        ax.set_ylabel("")
        ax.xaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", ".")))
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", labelsize=9)

        self._adicionar_rodape(fig)
        fig.tight_layout()
        self._ultima_figura = fig
        return fig


    # Gráfico 4 — Mapa coroplético do Brasil

    def grafico_mapa_brasil(
        self,
        df_ranking: pd.DataFrame,
        uf: str = "TODOS",
        ano_inicio: int = None,
        ano_fim: int = None,
        tipo_crime: str = "TODOS",
        caminho_geojson: str = "dados/brazil_states.geojson"
    ) -> plt.Figure:
        """
        Mapa coroplético colorindo os estados pela intensidade de casos.
        Quanto mais escuro o estado, mais casos registrados.

        Parâmetros
        ----------
        df_ranking      : DataFrame com colunas [uf, total]
        caminho_geojson : caminho para o arquivo GeoJSON dos estados
        """
        fig, ax = plt.subplots(figsize=(9, 9))

        # Verifica se geopandas está disponível
        import os, sys
        gpd = None
        try:
            import geopandas as gpd
        except Exception:
            pass

        # Se não encontrou, tenta o caminho da Microsoft Store
        if gpd is None:
            try:
                store_path = os.path.join(
                    os.environ.get("LOCALAPPDATA",""),
                    "Packages","PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0",
                    "LocalCache","local-packages","Python313","site-packages"
                )
                if store_path not in sys.path and os.path.exists(store_path):
                    sys.path.insert(0, store_path)
                import geopandas as gpd
            except Exception:
                pass

        if gpd is None:
            ax.text(0.5, 0.5,
                    "geopandas não encontrado.\nAbra o terminal e rode:\npip install geopandas",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=11, color="#7F8C8D")
            self._adicionar_rodape(fig)
            self._ultima_figura = fig
            return fig

        # Verifica o caminho do GeoJSON 
        caminhos_geojson = [
            caminho_geojson,
            os.path.join("dados", "brazil_states.geojson"),
            os.path.join(os.path.dirname(__file__), "..", "dados", "brazil_states.geojson"),
        ]
        geojson_encontrado = None
        for c in caminhos_geojson:
            if os.path.exists(c):
                geojson_encontrado = c
                break

        if geojson_encontrado is None:
            ax.text(0.5, 0.5,
                    "Arquivo de mapa não encontrado.\nVerifique se brazil_states.geojson\nestá na pasta dados/",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=11, color="#7F8C8D")
            self._adicionar_rodape(fig)
            self._ultima_figura = fig
            return fig
        
        caminho_geojson = geojson_encontrado

        if df_ranking.empty:
            ax.text(0.5, 0.5, "Nenhum dado para os filtros selecionados.",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=12, color="#7F8C8D")
            self._adicionar_rodape(fig)
            self._ultima_figura = fig
            return fig

        # Carrega shapefile e faz merge com os dados
        gdf = gpd.read_file(caminho_geojson)
        gdf_merged = gdf.merge(df_ranking, left_on="sigla", right_on="uf", how="left")
        gdf_merged["total"] = gdf_merged["total"].fillna(0)

        # Estados sem dado ficam cinza claro
        gdf_sem_dado = gdf_merged[gdf_merged["total"] == 0]
        gdf_com_dado = gdf_merged[gdf_merged["total"] >  0]

        if not gdf_sem_dado.empty:
            gdf_sem_dado.plot(ax=ax, color="#EEEEEE", edgecolor="white", linewidth=0.6)

        if not gdf_com_dado.empty:
            gdf_com_dado.plot(
                column="total", ax=ax,
                cmap="YlOrRd",
                legend=True,
                edgecolor="white", linewidth=0.6,
                legend_kwds={
                    "label":   "Nº de casos",
                    "shrink":  0.55,
                    "pad":     0.02,
                    "aspect":  20,
                }
            )

        # Rótulos: sigla + número em cada estado
        for _, row in gdf_merged.iterrows():
            centroid = row.geometry.centroid
            total    = int(row["total"])
            sigla    = row["sigla"]
            cor_txt  = "white" if total > gdf_merged["total"].quantile(0.65) else "#333333"
            ax.annotate(
                f"{sigla}\n{total:,}".replace(",", "."),
                xy=(centroid.x, centroid.y),
                ha="center", va="center",
                fontsize=6.5, color=cor_txt,
                fontweight="bold"
            )

        titulo = self._montar_titulo(uf, ano_inicio, ano_fim, tipo_crime)
        ax.set_title(titulo + "\n(intensidade por estado)",
                     fontsize=12, fontweight="bold", pad=14)
        ax.axis("off")

        self._adicionar_rodape(fig)
        fig.tight_layout()
        self._ultima_figura = fig
        return fig

    # Exportar PNG

    def salvar_figura(self, caminho: str) -> bool:
        """Salva o último gráfico gerado como PNG."""
        if self._ultima_figura is None:
            return False
        self._ultima_figura.savefig(caminho, dpi=150,
                                     bbox_inches="tight",
                                     facecolor="white")
        return True

    # Auxiliares

    def _montar_titulo(self, uf, ano_inicio, ano_fim, tipo_crime) -> str:
        """Monta título dinâmico baseado nos filtros ativos."""
        crime_label = tipo_crime if tipo_crime != "TODOS" else "Violência contra a Mulher"
        regiao = f"— {uf}" if uf != "TODOS" else "— Brasil"
        periodo = ""
        if ano_inicio and ano_fim:
            periodo = f" ({ano_inicio}–{ano_fim})"
        elif ano_inicio:
            periodo = f" (a partir de {ano_inicio})"
        elif ano_fim:
            periodo = f" (até {ano_fim})"
        return f"{crime_label} {regiao}{periodo}"

    def _adicionar_rodape(self, fig: plt.Figure):
        fig.text(0.99, 0.01, FONTE_DADOS,
                 ha="right", va="bottom", fontsize=7,
                 color="#95A5A6", style="italic")

    def fechar_figuras(self):
        plt.close("all")
