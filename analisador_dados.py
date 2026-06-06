"""
analisador_dados.py
===================
Aplica filtros e calcula KPIs:
- KPI 4: estado com maior crescimento percentual
- Método para gerar resumo textual automático em português
- Dados de ranking por estado para gráfico de barras
"""

import pandas as pd


class AnalisadorDados:

    def __init__(self, df: pd.DataFrame):
        self.df_original = df.copy()
        self.df_filtrado = df.copy()

    def aplicar_filtros(
        self,
        uf: str = "TODOS",
        ano_inicio: int = None,
        ano_fim: int = None,
        tipo_crime: str = "TODOS"
    ) -> pd.DataFrame:
        df = self.df_original.copy()
        if uf != "TODOS":
            df = df[df["uf"] == uf.upper()]
        if ano_inicio is not None:
            df = df[df["ano"] >= ano_inicio]
        if ano_fim is not None:
            df = df[df["ano"] <= ano_fim]
        if tipo_crime != "TODOS":
            df = df[df["tipo_crime"] == tipo_crime]
        self.df_filtrado = df
        return self.df_filtrado

    def calcular_kpis(self) -> dict:
        """
        KPIs:
        1. total_casos         — soma total de vítimas
        2. variacao_percentual — variação % entre primeiro e último ano
        3. estado_critico      — estado com mais ocorrências
        4. estado_maior_cresc  — estado com maior crescimento %
        """
        df = self.df_filtrado
        if df.empty:
            return {
                "total_casos":        0,
                "variacao_percentual": 0.0,
                "estado_critico":     "—",
                "estado_maior_cresc": "—",
            }

        total_casos = int(df["total_vitimas"].sum())
        variacao    = self._calcular_variacao()

        estado_critico = "—"
        if "uf" in df.columns:
            estado_critico = df.groupby("uf")["total_vitimas"].sum().idxmax()

        estado_maior_cresc = self._estado_maior_crescimento()

        return {
            "total_casos":        total_casos,
            "variacao_percentual": variacao,
            "estado_critico":     estado_critico,
            "estado_maior_cresc": estado_maior_cresc,
        }

    def _calcular_variacao(self) -> float:
        df = self.df_filtrado
        if df.empty or "ano" not in df.columns:
            return 0.0
        anos = sorted(df["ano"].unique())
        if len(anos) < 2:
            return 0.0
        primeiro = int(df[df["ano"] == anos[0]]["total_vitimas"].sum())
        ultimo   = int(df[df["ano"] == anos[-1]]["total_vitimas"].sum())
        if primeiro == 0:
            return 0.0
        return round(((ultimo - primeiro) / primeiro) * 100, 1)

    def _estado_maior_crescimento(self) -> str:
        """Retorna a UF com maior crescimento % entre primeiro e último ano."""
        df = self.df_filtrado
        if df.empty or "ano" not in df.columns:
            return "—"
        anos = sorted(df["ano"].unique())
        if len(anos) < 2:
            return "—"
        primeiro_ano = anos[0]
        ultimo_ano   = anos[-1]
        ini = df[df["ano"] == primeiro_ano].groupby("uf")["total_vitimas"].sum()
        fim = df[df["ano"] == ultimo_ano].groupby("uf")["total_vitimas"].sum()
        ufs_comuns = ini.index.intersection(fim.index)
        ini = ini[ufs_comuns]
        fim = fim[ufs_comuns]
        ini = ini[ini > 0]
        fim = fim[ini.index]
        if ini.empty:
            return "—"
        crescimento = ((fim - ini) / ini * 100)
        return str(crescimento.idxmax())

    # Agregações para gráficos
    def serie_historica(self) -> pd.DataFrame:
        if self.df_filtrado.empty:
            return pd.DataFrame()
        return (
            self.df_filtrado
            .groupby(["ano", "tipo_crime"])["total_vitimas"]
            .sum().reset_index().sort_values("ano")
        )

    def dados_heatmap(self) -> pd.DataFrame:
        """Pivot UF × ano, ordenado pelo total decrescente."""
        if self.df_filtrado.empty:
            return pd.DataFrame()
        pivot = (
            self.df_filtrado
            .groupby(["uf", "ano"])["total_vitimas"]
            .sum().reset_index()
            .pivot(index="uf", columns="ano", values="total_vitimas")
            .fillna(0)
        )
        # Ordena estados do maior para o menor total
        pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
        return pivot

    def dados_ranking_estados(self) -> pd.DataFrame:
        """Ranking dos estados por total de vítimas no filtro atual."""
        if self.df_filtrado.empty:
            return pd.DataFrame()
        return (
            self.df_filtrado
            .groupby("uf")["total_vitimas"]
            .sum().reset_index()
            .rename(columns={"total_vitimas": "total"})
            .sort_values("total", ascending=True)  # ascendente p/ barras horizontais
        )

    # Resumo textual automático

    def gerar_resumo_textual(
        self,
        uf: str,
        ano_inicio: int,
        ano_fim: int,
        tipo_crime: str
    ) -> str:
        """
        Gera parágrafo em português com os principais dados do filtro ativo
        Usado na aba 'Resumo' da interface
        """
        df = self.df_filtrado
        if df.empty:
            return "Nenhum dado encontrado para os filtros selecionados."

        kpis   = self.calcular_kpis()
        total  = kpis["total_casos"]
        var    = kpis["variacao_percentual"]
        estado = kpis["estado_critico"]
        cresc  = kpis["estado_maior_cresc"]

        regiao = f"no estado {uf}" if uf != "TODOS" else "no Brasil"
        crime  = tipo_crime if tipo_crime != "TODOS" else "violência contra a mulher"
        periodo = f"{ano_inicio} a {ano_fim}"

        sinal_var = "aumento" if var >= 0 else "queda"
        abs_var   = abs(var)

        linhas = [
            f"No período de {periodo}, foram registrados {total:,} casos de {crime.lower()} {regiao}.".replace(",", "."),
            "",
            f"Isso representa um {sinal_var} de {abs_var}% em relação ao início do período analisado.",
        ]

        if uf == "TODOS":
            linhas.append(f"O estado com maior número absoluto de casos foi {estado}.")
            if cresc != "—" and cresc != estado:
                linhas.append(f"Já o maior crescimento percentual foi registrado em {cresc}.")

        ano_pico_val = df.groupby("ano")["total_vitimas"].sum().idxmax()
        linhas.append(f"O ano com mais registros no período foi {ano_pico_val}.")

        if tipo_crime == "Feminicídio":
            linhas.append("")
            linhas.append(
                "Nota metodológica: os dados de feminicídio estão disponíveis "
                "a partir de 2015, ano de sanção da Lei nº 13.104 (Lei do Feminicídio)."
            )

        return "\n".join(linhas)

    # Auxiliares para a interface

    def exportar_csv(self, caminho_saida: str = "relatorio_filtrado.csv") -> str:
        if self.df_filtrado.empty:
            print("Nenhum dado para exportar.")
            return ""
        self.df_filtrado.to_csv(caminho_saida, index=False, encoding="utf-8-sig")
        print(f"CSV exportado: {caminho_saida} ({len(self.df_filtrado)} linhas)")
        return caminho_saida

    def listar_ufs(self) -> list:
        return sorted(self.df_original["uf"].unique().tolist())

    def listar_anos(self) -> list:
        return sorted(self.df_original["ano"].unique().tolist())

    def listar_tipos_crime(self) -> list:
        return sorted(self.df_original["tipo_crime"].unique().tolist())
