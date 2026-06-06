"""
main.py — Ponto de entrada do sistema ViolenciaBR.

Como rodar:
    python main.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.processador_dados import ProcessadorDados
from src.interface import InterfaceApp

# Tenta o arquivo real primeiro, senão usa o de exemplo
CAMINHOS = [
    os.path.join("dados", "br_fbsp_absp_uf_csv.gz"),
    os.path.join("dados", "fbsp_violencia.csv"),
]

def main():
    print("=" * 50)
    print("  ViolenciaBR — Iniciando sistema...")
    print("=" * 50)

    caminho = None
    for c in CAMINHOS:
        if os.path.exists(c):
            caminho = c
            break

    if not caminho:
        print("\nERRO: Nenhum arquivo de dados encontrado.")
        print("Gere dados de exemplo com:")
        print("  python dados/gerar_dados_exemplo.py")
        sys.exit(1)

    print(f"Usando: {caminho}\n")
    proc = ProcessadorDados(caminho)
    df   = proc.carregar_e_limpar()
    proc.resumo()

    print("Abrindo o dashboard...\n")
    app = InterfaceApp(df)
    app.iniciar()

if __name__ == "__main__":
    main()
