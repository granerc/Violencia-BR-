"""
processador_dados.py
====================
Carrega e limpa os dados reais do FBSP (br_fbsp_absp_uf_csv.gz)

Correções aplicadas:
- Feminicídio: dados válidos só a partir de 2015 (Lei do Feminicídio)
- Estupro: dados válidos a partir de 2009 (2007/2008 ausentes no FBSP)
- Tentativa de estupro: nulos tratados como "não reportado" e removidos

Como usar:
    from src.processador_dados import ProcessadorDados
    proc = ProcessadorDados("dados/br_fbsp_absp_uf_csv.gz")
    df = proc.carregar_e_limpar()
"""

import pandas as pd
import os
import gzip

UFS_VALIDAS = {
    "AC","AL","AP","AM","BA","CE","DF","ES","GO",
    "MA","MT","MS","MG","PA","PB","PR","PE","PI",
    "RJ","RN","RS","RO","RR","SC","SP","SE","TO"
}

# Anos mínimos com dados reais para cada crime
ANO_MINIMO_POR_CRIME = {
    "Feminicídio":         2015,  # Lei do Feminicídio sancionada em março/2015
    "Estupro":             2009,  # FBSP sem dados em 2007 e 2008
    "Tentativa de Estupro": 2009,
}


class ProcessadorDados:

    def __init__(self, caminho_arquivo: str):
        if not os.path.exists(caminho_arquivo):
            raise FileNotFoundError(
                f"Arquivo não encontrado: {caminho_arquivo}\n"
                "Verifique se o arquivo está na pasta dados/."
            )
        self.caminho_arquivo = caminho_arquivo
        self.df = None

    def carregar_e_limpar(self) -> pd.DataFrame:
        print(f"[1/6] Lendo: {self.caminho_arquivo}")
        self._carregar_arquivo()
        print("[2/6] Padronizando colunas...")
        self._padronizar_colunas()
        print("[3/6] Convertendo para formato long...")
        self._converter_para_long()
        print("[4/6] Removendo anos sem dados reais...")
        self._filtrar_anos_validos()
        print("[5/6] Limpando nulos e duplicatas...")
        self._limpar_dados()
        print("[6/6] Validando integridade...")
        self._validar_dados()
        print(f"\nPronto! {len(self.df)} registros carregados.\n")
        return self.df

    def _carregar_arquivo(self):
        if self.caminho_arquivo.endswith(".gz"):
            with gzip.open(self.caminho_arquivo, 'rt', encoding='utf-8') as f:
                self.df = pd.read_csv(f)
        else:
            try:
                self.df = pd.read_csv(self.caminho_arquivo, encoding="utf-8")
            except UnicodeDecodeError:
                self.df = pd.read_csv(self.caminho_arquivo, encoding="latin-1")

    def _padronizar_colunas(self):
        self.df.columns = self.df.columns.str.strip().str.lower()
        if "sigla_uf" in self.df.columns:
            self.df.rename(columns={"sigla_uf": "uf"}, inplace=True)
        self.df["uf"] = self.df["uf"].astype(str).str.strip().str.upper()
        self.df["ano"] = pd.to_numeric(
            self.df["ano"], errors="coerce").fillna(0).astype(int)

    def _converter_para_long(self):
        """
        Converte formato wide → long
        """
        colunas_crimes = {
            "quantidade_feminicidio":       "Feminicídio",
            "quantidade_estupro":           "Estupro",
            "quantidade_tentativa_estupro": "Tentativa de Estupro",
        }

        colunas_presentes = {
            k: v for k, v in colunas_crimes.items()
            if k in self.df.columns
        }

        df_long = self.df[["ano", "uf"] + list(colunas_presentes.keys())].melt(
            id_vars=["ano", "uf"],
            value_vars=list(colunas_presentes.keys()),
            var_name="tipo_crime",
            value_name="total_vitimas"
        )

        df_long["tipo_crime"] = df_long["tipo_crime"].map(colunas_presentes)
        self.df = df_long

    def _filtrar_anos_validos(self):
        """
        Remove registros de anos anteriores ao início real da coleta.

        - Feminicídio: antes de 2015 os estados não registravam
          (Lei do Feminicídio foi sancionada em março de 2015)
        - Estupro e Tentativa: FBSP não tinha dados em 2007/2008

        Também remove linhas onde total_vitimas é nulo (estado
        não reportou aquele crime naquele ano — não é zero real)
        """
        mascaras = []
        for crime, ano_min in ANO_MINIMO_POR_CRIME.items():
            mask = (self.df["tipo_crime"] == crime) & (self.df["ano"] >= ano_min)
            mascaras.append(mask)

        # Mantém só linhas que passam em pelo menos uma máscara
        from functools import reduce
        import operator
        filtro_final = reduce(operator.or_, mascaras)
        antes = len(self.df)
        self.df = self.df[filtro_final].copy()

        # Remove linhas onde total_vitimas é nulo
        # (significa que o estado não reportou — diferente de zero casos)
        nulos = self.df["total_vitimas"].isna().sum()
        if nulos > 0:
            print(f"  {nulos} registros sem dado (estado não reportou) removidos.")
            self.df = self.df[self.df["total_vitimas"].notna()]

        print(f"  {antes - len(self.df)} registros de anos sem dados reais removidos.")

    def _limpar_dados(self):
        antes = len(self.df)
        self.df.drop_duplicates(inplace=True)
        removidas = antes - len(self.df)
        if removidas > 0:
            print(f"  {removidas} duplicatas removidas.")
        self.df["total_vitimas"] = pd.to_numeric(
            self.df["total_vitimas"], errors="coerce").fillna(0).astype(int)

    def _validar_dados(self):
        ufs_invalidas = set(self.df["uf"].unique()) - UFS_VALIDAS
        if ufs_invalidas:
            print(f"  UFs removidas: {ufs_invalidas}")
            self.df = self.df[self.df["uf"].isin(UFS_VALIDAS)]
        negativos = (self.df["total_vitimas"] < 0).sum()
        if negativos > 0:
            self.df.loc[self.df["total_vitimas"] < 0, "total_vitimas"] = 0

    def resumo(self):
        if self.df is None:
            print("Chame carregar_e_limpar() primeiro.")
            return
        print("=" * 45)
        print(f"Linhas     : {len(self.df)}")
        print(f"Colunas    : {list(self.df.columns)}")
        if "ano" in self.df.columns:
            print(f"Anos       : {sorted(self.df['ano'].unique())}")
        if "uf" in self.df.columns:
            print(f"Estados    : {sorted(self.df['uf'].unique())}")
        if "tipo_crime" in self.df.columns:
            print(f"Crimes     : {sorted(self.df['tipo_crime'].unique())}")
        print("=" * 45)
