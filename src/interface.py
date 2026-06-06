"""
interface.py
============
Interface gráfica completa do ViolenciaBR:
- Cores fixas por crime
- Título dinâmico nos gráficos
- 3 tipos de gráfico: Linhas / Heatmap / Ranking de estados
- Heatmap ordenado por total decrescente
- KPI 4: estado com maior crescimento %
- Aba Resumo com texto automático 
- Exportar PNG do gráfico atual
- Nota metodológica sobre Lei do Feminicídio
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.analisador_dados import AnalisadorDados
from src.gerador_pdf import GeradorPDF
from src.gerador_visualizacoes import GeradorVisualizacoes

COR_FUNDO    = "#F8F9FA"
COR_PAINEL   = "#FFFFFF"
COR_TITULO   = "#2C3E50"
COR_DESTAQUE = "#C0392B"
COR_BOTAO    = "#2980B9"
COR_EXPORT   = "#27AE60"
COR_PNG      = "#8E44AD"
COR_PDF      = "#C0392B"
COR_TEXTO    = "#2C3E50"
COR_MUTED    = "#7F8C8D"


class InterfaceApp:

    def __init__(self, df):
        self.analisador  = AnalisadorDados(df)
        self.gerador     = GeradorVisualizacoes()
        self.canvas_fig  = None

        self.root = tk.Tk()

        self.var_uf       = tk.StringVar(value="TODOS")
        self.var_ano_ini  = tk.StringVar()
        self.var_ano_fim  = tk.StringVar()
        self.var_tipo     = tk.StringVar(value="TODOS")
        self.modo_grafico = tk.StringVar(value="linhas")

        anos = self.analisador.listar_anos()
        self.var_ano_ini.set(str(anos[0]))
        self.var_ano_fim.set(str(anos[-1]))

        self.root.title("ViolenciaBR — Dashboard de Violência contra a Mulher")
        self.root.geometry("1150x820")
        self.root.minsize(950, 680)
        self.root.configure(bg=COR_FUNDO)

        self._construir_interface()

    # Construção

    def _construir_interface(self):
        self._criar_cabecalho()
        self._criar_painel_filtros()
        self._criar_painel_kpis()
        self._criar_area_conteudo()
        self._criar_rodape()
        self._atualizar()

    def _criar_cabecalho(self):
        frame = tk.Frame(self.root, bg=COR_DESTAQUE, pady=10)
        frame.pack(fill="x")
        tk.Label(frame, text="ViolenciaBR",
                 bg=COR_DESTAQUE, fg="white",
                 font=("Helvetica", 20, "bold")).pack()
        tk.Label(frame,
                 text="Dashboard de Violência contra a Mulher no Brasil — Dados FBSP 2009–2021",
                 bg=COR_DESTAQUE, fg="#FADBD8",
                 font=("Helvetica", 9)).pack()

    def _criar_painel_filtros(self):
        frame = tk.LabelFrame(self.root, text=" Filtros ",
                              bg=COR_PAINEL, fg=COR_TITULO,
                              font=("Helvetica", 10, "bold"),
                              padx=8, pady=6, relief="flat",
                              highlightbackground="#DDE1E7",
                              highlightthickness=1)
        frame.pack(fill="x", padx=14, pady=(8, 4))

        # Estado
        tk.Label(frame, text="Estado:", bg=COR_PAINEL, fg=COR_TEXTO,
                 font=("Helvetica", 9)).grid(row=0, column=0, sticky="w", padx=5)
        opcoes_uf = ["TODOS"] + self.analisador.listar_ufs()
        ttk.Combobox(frame, textvariable=self.var_uf,
                     values=opcoes_uf, state="readonly",
                     width=8).grid(row=0, column=1, padx=5)

        # Ano início
        anos = [str(a) for a in self.analisador.listar_anos()]
        tk.Label(frame, text="De:", bg=COR_PAINEL, fg=COR_TEXTO,
                 font=("Helvetica", 9)).grid(row=0, column=2, sticky="w", padx=5)
        ttk.Combobox(frame, textvariable=self.var_ano_ini,
                     values=anos, state="readonly",
                     width=6).grid(row=0, column=3, padx=5)

        # Ano fim
        tk.Label(frame, text="Até:", bg=COR_PAINEL, fg=COR_TEXTO,
                 font=("Helvetica", 9)).grid(row=0, column=4, sticky="w", padx=5)
        ttk.Combobox(frame, textvariable=self.var_ano_fim,
                     values=anos, state="readonly",
                     width=6).grid(row=0, column=5, padx=5)

        # Tipo crime
        tk.Label(frame, text="Crime:", bg=COR_PAINEL, fg=COR_TEXTO,
                 font=("Helvetica", 9)).grid(row=0, column=6, sticky="w", padx=5)
        opcoes_tipo = ["TODOS"] + self.analisador.listar_tipos_crime()
        ttk.Combobox(frame, textvariable=self.var_tipo,
                     values=opcoes_tipo, state="readonly",
                     width=20).grid(row=0, column=7, padx=5)

        # Tipo gráfico
        tk.Label(frame, text="Gráfico:", bg=COR_PAINEL, fg=COR_TEXTO,
                 font=("Helvetica", 9)).grid(row=0, column=8, sticky="w", padx=5)
        for i, (label, val) in enumerate([
            ("Linhas", "linhas"), ("Heatmap", "heatmap"), ("Ranking", "ranking"), ("Mapa BR", "mapa")
        ]):
            tk.Radiobutton(frame, text=label, variable=self.modo_grafico,
                           value=val, bg=COR_PAINEL, fg=COR_TEXTO,
                           font=("Helvetica", 9)).grid(row=0, column=9+i, padx=2)

        # Botões
        tk.Button(frame, text="  Atualizar  ",
                  bg=COR_BOTAO, fg="white",
                  font=("Helvetica", 9, "bold"), relief="flat",
                  cursor="hand2", command=self._atualizar
                  ).grid(row=0, column=13, padx=8)

        tk.Button(frame, text="  Exportar CSV  ",
                  bg=COR_EXPORT, fg="white",
                  font=("Helvetica", 9, "bold"), relief="flat",
                  cursor="hand2", command=self._exportar_csv
                  ).grid(row=0, column=14, padx=4)

        tk.Button(frame, text="  Salvar PNG  ",
                  bg=COR_PNG, fg="white",
                  font=("Helvetica", 9, "bold"), relief="flat",
                  cursor="hand2", command=self._salvar_png
                  ).grid(row=0, column=15, padx=4)

        tk.Button(frame, text="  Exportar PDF  ",
                  bg=COR_PDF, fg="white",
                  font=("Helvetica", 9, "bold"), relief="flat",
                  cursor="hand2", command=self._exportar_pdf
                  ).grid(row=0, column=16, padx=4)

    def _criar_painel_kpis(self):
        self.frame_kpis = tk.Frame(self.root, bg=COR_FUNDO)
        self.frame_kpis.pack(fill="x", padx=14, pady=(4, 4))

        self.labels_kpis = {}
        definicoes = [
            ("total_casos",        "Total de casos",              COR_DESTAQUE),
            ("variacao_percentual","Variação % no período",       "#E67E22"),
            ("estado_critico",     "Estado mais afetado",         "#8E44AD"),
            ("estado_maior_cresc", "Maior crescimento %",         "#16A085"),
        ]
        for i, (chave, rotulo, cor) in enumerate(definicoes):
            card = tk.Frame(self.frame_kpis, bg=COR_PAINEL,
                            highlightbackground="#DDE1E7",
                            highlightthickness=1)
            card.grid(row=0, column=i, sticky="nsew",
                      padx=5, pady=2, ipadx=14, ipady=10)
            self.frame_kpis.columnconfigure(i, weight=1)
            tk.Label(card, text=rotulo, bg=COR_PAINEL, fg=COR_MUTED,
                     font=("Helvetica", 8)).pack()
            lbl = tk.Label(card, text="—", bg=COR_PAINEL, fg=cor,
                           font=("Helvetica", 17, "bold"))
            lbl.pack()
            self.labels_kpis[chave] = lbl

    def _criar_area_conteudo(self):
        """Cria notebook com abas: Gráfico | Resumo."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=(4, 4))

        # Aba Gráfico
        self.frame_grafico = tk.Frame(self.notebook, bg=COR_PAINEL)
        self.notebook.add(self.frame_grafico, text="  Gráfico  ")

        # Aba Resumo
        self.frame_resumo = tk.Frame(self.notebook, bg=COR_PAINEL)
        self.notebook.add(self.frame_resumo, text="  Resumo Automático  ")
        self._construir_aba_resumo()

    def _construir_aba_resumo(self):
        tk.Label(self.frame_resumo,
                 text="Resumo gerado automaticamente com base nos filtros ativos:",
                 bg=COR_PAINEL, fg=COR_MUTED,
                 font=("Helvetica", 9)).pack(anchor="w", padx=16, pady=(12, 4))

        self.texto_resumo = tk.Text(
            self.frame_resumo,
            bg="#FAFAFA", fg=COR_TEXTO,
            font=("Helvetica", 11),
            relief="flat", wrap="word",
            padx=16, pady=12,
            state="disabled"
        )
        self.texto_resumo.pack(fill="both", expand=True, padx=14, pady=(0, 12))

    def _criar_rodape(self):
        frame = tk.Frame(self.root, bg="#ECF0F1", pady=4)
        frame.pack(fill="x", side="bottom")
        tk.Label(frame,
                 text="Fonte: Fórum Brasileiro de Segurança Pública (FBSP) — basedosdados.org  |  "
                      "Público: jornalistas de dados e gestores municipais",
                 bg="#ECF0F1", fg=COR_MUTED,
                 font=("Helvetica", 8)).pack()

    # Atualização

    def _atualizar(self):
        uf      = self.var_uf.get()
        ano_ini = int(self.var_ano_ini.get())
        ano_fim = int(self.var_ano_fim.get())
        tipo    = self.var_tipo.get()
        modo    = self.modo_grafico.get()

        if ano_ini > ano_fim:
            messagebox.showwarning("Intervalo inválido",
                                   "O ano inicial não pode ser maior que o final.")
            return

        self.analisador.aplicar_filtros(
            uf=uf, ano_inicio=ano_ini, ano_fim=ano_fim, tipo_crime=tipo)

        # KPIs
        kpis = self.analisador.calcular_kpis()
        self.labels_kpis["total_casos"].config(
            text=f"{kpis['total_casos']:,}".replace(",", "."))
        sinal = "+" if kpis["variacao_percentual"] >= 0 else ""
        self.labels_kpis["variacao_percentual"].config(
            text=f"{sinal}{kpis['variacao_percentual']}%")
        self.labels_kpis["estado_critico"].config(text=kpis["estado_critico"])
        self.labels_kpis["estado_maior_cresc"].config(text=kpis["estado_maior_cresc"])

        # Gráfico
        self.gerador.fechar_figuras()
        if modo == "linhas":
            df_serie = self.analisador.serie_historica()
            fig = self.gerador.grafico_serie_historica(
                df_serie, uf=uf, ano_inicio=ano_ini, ano_fim=ano_fim, tipo_crime=tipo)
        elif modo == "heatmap":
            df_pivot = self.analisador.dados_heatmap()
            fig = self.gerador.grafico_heatmap(
                df_pivot, uf=uf, ano_inicio=ano_ini, ano_fim=ano_fim, tipo_crime=tipo)
        elif modo == "ranking":
            df_rank = self.analisador.dados_ranking_estados()
            fig = self.gerador.grafico_ranking_estados(
                df_rank, uf=uf, ano_inicio=ano_ini, ano_fim=ano_fim, tipo_crime=tipo)
        else:  # mapa
            df_rank = self.analisador.dados_ranking_estados()
            fig = self.gerador.grafico_mapa_brasil(
                df_rank, uf=uf, ano_inicio=ano_ini, ano_fim=ano_fim, tipo_crime=tipo)

        self._renderizar_grafico(fig)

        # Resumo textual
        resumo = self.analisador.gerar_resumo_textual(uf, ano_ini, ano_fim, tipo)
        self.texto_resumo.config(state="normal")
        self.texto_resumo.delete("1.0", tk.END)
        self.texto_resumo.insert(tk.END, resumo)
        self.texto_resumo.config(state="disabled")

    def _renderizar_grafico(self, fig):
        if self.canvas_fig is not None:
            self.canvas_fig.get_tk_widget().destroy()
        self.canvas_fig = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        self.canvas_fig.draw()
        self.canvas_fig.get_tk_widget().pack(fill="both", expand=True)

    # Exportações

    def _exportar_csv(self):
        uf      = self.var_uf.get()
        ano_ini = self.var_ano_ini.get()
        ano_fim = self.var_ano_fim.get()
        tipo    = self.var_tipo.get().replace(" ", "_").lower()
        nome    = f"violenciabr_{uf}_{tipo}_{ano_ini}_{ano_fim}.csv"

        caminho = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=nome, title="Salvar CSV")
        if caminho:
            resultado = self.analisador.exportar_csv(caminho)
            if resultado:
                messagebox.showinfo("Exportado!", f"Arquivo salvo em:\n{caminho}")

    def _salvar_png(self):
        uf      = self.var_uf.get()
        ano_ini = self.var_ano_ini.get()
        ano_fim = self.var_ano_fim.get()
        modo    = self.modo_grafico.get()
        nome    = f"violenciabr_{uf}_{modo}_{ano_ini}_{ano_fim}.png"

        caminho = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png")],
            initialfile=nome, title="Salvar gráfico como PNG")
        if caminho:
            ok = self.gerador.salvar_figura(caminho)
            if ok:
                messagebox.showinfo("Salvo!", f"Gráfico salvo em:\n{caminho}")
            else:
                messagebox.showerror("Erro", "Nenhum gráfico para salvar.")

    def _exportar_pdf(self):
        """Gera relatório PDF completo com KPIs, resumo e todos os gráficos."""
        uf      = self.var_uf.get()
        ano_ini = int(self.var_ano_ini.get())
        ano_fim = int(self.var_ano_fim.get())
        tipo    = self.var_tipo.get()
        crime   = tipo.replace(" ", "_").lower()
        nome    = f"violenciabr_{uf}_{crime}_{ano_ini}_{ano_fim}.pdf"

        caminho = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=nome,
            title="Salvar relatório PDF"
        )
        if not caminho:
            return

        try:
            gen_pdf = GeradorPDF(self.analisador, self.gerador)
            gen_pdf.gerar(
                caminho=caminho,
                uf=uf, ano_inicio=ano_ini,
                ano_fim=ano_fim, tipo_crime=tipo
            )
            messagebox.showinfo(
                "PDF gerado!",
                f"Relatório salvo em:\n{caminho}\n\n"
                "Contém: capa, KPIs, resumo, 3 gráficos."
            )
        except Exception as e:
            messagebox.showerror("Erro ao gerar PDF", str(e))

    def iniciar(self):
        self.root.mainloop()
