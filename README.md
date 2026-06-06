# ViolenciaBR

> Dashboard desktop para análise de violência contra a mulher no Brasil — feminicídio, estupro e tentativa de estupro por estado e ano.

**Disciplina:** Novas Tecnologias — UCB  
**Turma:** C — Segurança Digital e Pública  
**Biblioteca principal:** Pandas  
**Professor:** Adam Smith Gontijo

---

## Sumário

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Como Usar](#como-usar)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Arquitetura (MVC)](#arquitetura-mvc)
- [Diagramas](#diagramas)
- [Fonte dos Dados](#fonte-dos-dados)
- [Testes](#testes)
- [Bibliotecas Utilizadas](#bibliotecas-utilizadas)
- [Considerações Éticas](#considerações-éticas)
- [Equipe](#equipe)

---

## Sobre o Projeto

O Brasil registrou **1.492 feminicídios em 2024** — o maior número desde o início da série histórica em 2015 (FBSP, 2025). Apesar da existência de dados oficiais, eles permanecem dispersos, em formato bruto e de difícil interpretação para quem não tem conhecimento técnico.

O **ViolenciaBR** transforma esses dados do Fórum Brasileiro de Segurança Pública (FBSP) em visualizações interativas e acessíveis, rodando **100% localmente**, sem necessidade de servidor ou internet após a instalação.

### Público-alvo

| Perfil | Necessidade |
|--------|-------------|
| **Jornalistas e pesquisadoras de dados** | Visualizar tendências nacionais/regionais e exportar dados filtrados para reportagens investigativas, sem precisar programar |
| **Gestores públicos municipais** (secretarias de assistência social, conselhos tutelares) | Monitorar tendências regionais para embasar decisões de políticas públicas e justificar orçamentos |

---

## Funcionalidades

| # | Funcionalidade | Detalhe |
|---|----------------|---------|
| ✅ | Importar CSV/GZ do FBSP | Detecção automática de encoding (UTF-8 / Latin-1) |
| ✅ | Filtros interativos | Por estado (UF), intervalo de anos e tipo de crime |
| ✅ | Gráfico de série histórica | Linhas com tooltip interativo ao passar o mouse |
| ✅ | Heatmap UF × Ano | Escala de cores YlOrRd, ordenado do maior para menor |
| ✅ | Ranking de estados | Top 15 estados em barras horizontais com rótulos |
| ✅ | Mapa coroplético do Brasil | Shapefile IBGE embutido — funciona offline |
| ✅ | Painel de KPIs | 4 indicadores recalculados em tempo real |
| ✅ | Resumo automático em português | Parágrafo gerado com base nos filtros ativos |
| ✅ | Exportar tabela CSV filtrada | Arquivo salvo com encoding UTF-8-sig |
| ✅ | Salvar gráfico como PNG | Resolução 150 DPI |
| ✅ | Relatório PDF completo | 7 páginas: capa, KPIs, resumo textual e 4 gráficos |

### KPIs calculados

| KPI | O que mede |
|-----|-----------|
| Total de casos | Soma de vítimas no filtro ativo |
| Variação % no período | Diferença percentual entre o primeiro e o último ano filtrado |
| Estado mais afetado | UF com maior número absoluto de casos |
| Maior crescimento % | UF com maior crescimento percentual entre o início e o fim do período |

---

## Pré-requisitos

- **Python 3.10 ou superior**
- pip (gerenciador de pacotes do Python)
- ~200 MB de espaço em disco (inclui dados e dependências)

> O sistema roda em **Windows 10+**, **Ubuntu 20.04+** e **macOS 12+**.

---

## Instalação

### 1. Clone ou baixe o repositório

```bash
git clone https://github.com/seu-usuario/violenciabr.git
cd violenciabr
```

Ou baixe o ZIP pelo GitHub e extraia.

### 2. (Recomendado) Crie um ambiente virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Coloque o arquivo de dados

O arquivo `br_fbsp_absp_uf_csv.gz` já está incluído na pasta `dados/`.

Caso queira usar os dados mais recentes, baixe em:  
https://basedosdados.org/dataset/br-fbsp-violencia  
e salve como `dados/br_fbsp_absp_uf_csv.gz`.

---

## Como Usar

### Iniciar o dashboard

```bash
python main.py
```

O sistema detecta automaticamente o arquivo de dados na pasta `dados/` e abre a interface gráfica.

### Fluxo de uso

```
1. Selecione um estado (ou deixe "TODOS" para o Brasil inteiro)
2. Ajuste o intervalo de anos com os controles deslizantes
3. Escolha o tipo de crime (Feminicídio / Estupro / Tentativa de Estupro / Todos)
4. Os gráficos, KPIs e o resumo textual atualizam automaticamente
5. Use os botões de exportação: CSV, PNG ou Relatório PDF
```

### Exportações disponíveis

```bash
# O sistema gera os arquivos diretamente via interface, mas você também pode
# usar os módulos individualmente para scripts personalizados:

from src.processador_dados import ProcessadorDados
from src.analisador_dados import AnalisadorDados

proc = ProcessadorDados("dados/br_fbsp_absp_uf_csv.gz")
df = proc.carregar_e_limpar()

analisador = AnalisadorDados(df)
analisador.aplicar_filtros(uf="SP", ano_inicio=2018, ano_fim=2021, tipo_crime="Feminicídio")
analisador.exportar_csv("meu_relatorio.csv")
```

---

## Estrutura do Projeto

```
violenciabr/
│
├── main.py                          ← Ponto de entrada — detecta dados e abre a interface
├── requirements.txt                 ← Dependências Python
├── README.md
├── .gitignore
│
├── dados/
│   ├── br_fbsp_absp_uf_csv.gz       ← Base de dados do FBSP (incluída)
│   └── brazil_states.geojson        ← Shapefile do Brasil (IBGE) — uso offline
│
├── src/
│   ├── __init__.py
│   ├── processador_dados.py         ← [Model] Lê .gz, limpa, padroniza, valida
│   ├── analisador_dados.py          ← [Controller] Filtros, KPIs, resumo textual, CSV
│   ├── gerador_visualizacoes.py     ← [Model] Linhas, heatmap, ranking, mapa, PNG
│   ├── interface.py                 ← [View] Janela Tkinter, filtros, abas, botões
│   └── gerador_pdf.py               ← [Controller] Relatório PDF de 7 páginas
│
└── testes/
    └── test_sistema.py              ← 29 testes unitários (pytest / unittest)
```

---

## Arquitetura (MVC)

O sistema segue o padrão **Model-View-Controller**:

```
           CSV/GZ do FBSP
                │
                ▼
    ┌─────────────────────┐
    │  ProcessadorDados   │  ← Model: lê, limpa, valida, formata long
    │  (processador_      │
    │   dados.py)         │
    └──────────┬──────────┘
               │  DataFrame limpo
               ▼
    ┌─────────────────────┐      ┌─────────────────────┐
    │  AnalisadorDados    │      │  GeradorPDF         │
    │  (Controller)       │      │  (Controller)       │
    │  - aplicarFiltros() │      │  - gerarRelatorio() │
    │  - calcularKPIs()   │      └──────────┬──────────┘
    │  - gerarResumo()    │                 │
    └──────────┬──────────┘                 │
               │  dados analíticos          │
               ▼                            │
    ┌─────────────────────┐                 │
    │  GeradorVisuali-    │  ← Model:       │
    │  zacoes             │   gráficos      │
    │  - linhas()         │                 │
    │  - heatmap()        │                 │
    │  - ranking()        │                 │
    │  - mapaCoropletico()│                 │
    └──────────┬──────────┘                 │
               │  figuras Matplotlib        │
               ▼                            ▼
    ┌──────────────────────────────────────────┐
    │            InterfaceApp (View)           │
    │  Tkinter — filtros, KPIs, abas, botões   │
    └──────────────────────────────────────────┘
```

---

## Diagramas

Os diagramas foram elaborados no FigJam e estão disponíveis para visualização interativa nos links abaixo.

| Diagrama | O que mostra | Link |
|----------|-------------|------|
| Fluxo de Dados | Pipeline completo: CSV do FBSP → processamento → 4 saídas (CSV, PNG, PDF, tela) | [Abrir no FigJam](https://www.figma.com/board/DcUyRXKhudu4WzATNoc5Ec/ViolenciaBR---Diagrama-de-Fluxo-de-Dados) |
| Diagrama de Classes | 5 classes com atributos, métodos e relacionamentos (Model / Controller / View) | [Abrir no FigJam](https://www.figma.com/board/lDwVMs03MlusPLFnmFAx5T/ViolenciaBR---Diagrama-de-Classes) |
| Casos de Uso | 2 atores e 9 casos de uso com relações include/extend | [Abrir no FigJam](https://www.figma.com/board/XRnkKCK6EZDfgd68sCgh2T/ViolenciaBR---Diagrama-de-Casos-de-Uso) |

---

## Fonte dos Dados

| Campo | Informação |
|-------|-----------|
| **Fonte** | Fórum Brasileiro de Segurança Pública (FBSP) |
| **Dataset** | Anuário Brasileiro de Segurança Pública |
| **URL** | https://basedosdados.org/dataset/br-fbsp-violencia |
| **Formato** | CSV comprimido (.gz) |
| **Cobertura temporal** | 2009–2021 |
| **Cobertura geográfica** | 27 estados brasileiros (UF) |
| **Crimes analisados** | Feminicídio (a partir de 2015), Estupro e Tentativa de Estupro (a partir de 2009) |

### Por que Feminicídio só a partir de 2015?

A **Lei nº 13.104 (Lei do Feminicídio)** foi sancionada em março de 2015. Antes disso, os estados não registravam essa tipificação separadamente. O sistema exibe automaticamente essa nota metodológica quando o filtro de feminicídio é ativado.

---

## Testes

```bash
# Rodar todos os testes com saída detalhada
python -m pytest testes/test_sistema.py -v

# Instalar pytest (se não tiver)
pip install pytest
```

**Resultado esperado:** `29 passed`

### Cobertura por módulo

| Módulo | Testes | O que é verificado |
|--------|--------|-------------------|
| `ProcessadorDados` | 7 | Arquivo não encontrado, colunas obrigatórias, UF maiúsculo, ano como inteiro, ausência de negativos, ausência de duplicatas |
| `AnalisadorDados` | 14 | Filtros por UF/ano/tipo, KPIs corretos, heatmap ordenado, resumo textual gerado, exportação CSV |
| `GeradorVisualizacoes` | 5 | 3 tipos de gráfico, comportamento com DataFrame vazio, exportação PNG |
| `GeradorPDF` | 3 | Arquivo criado em disco, tamanho > 0, caminho retornado corretamente |

---

## Bibliotecas Utilizadas

| Biblioteca | Papel no sistema | Justificativa |
|------------|-----------------|---------------|
| **Pandas** | PRINCIPAL | Motor central: lê o .gz, limpa, filtra e agrega. Cobre todos os requisitos de dados. |
| Matplotlib | Auxiliar | Gráfico de linhas com tooltip e renderização no Tkinter via `FigureCanvasTkAgg` |
| Seaborn | Auxiliar | Heatmap com escala YlOrRd — visual profissional e legível para público leigo |
| Tkinter | Auxiliar | Interface desktop nativa do Python — roda sem servidor em qualquer OS |
| GeoPandas | Auxiliar | Mapa coroplético com shapefile GeoJSON do IBGE, embutido no projeto |
| mplcursors | Auxiliar | Tooltip interativo ao passar o mouse nos pontos do gráfico de linhas |
| matplotlib PdfPages | Auxiliar | Relatório PDF nativo do Matplotlib — sem bibliotecas extras |

---

## Considerações Éticas

- **Dados exclusivamente agregados e anonimizados** — nenhuma vítima individual é identificável em qualquer tela do sistema
- **Fonte identificada** em todos os gráficos e KPIs (rastreabilidade total — RNF04/RNF05)
- **Processamento local** — nenhum dado é enviado para servidores externos (RNF03)
- **Nota metodológica automática** sobre a Lei do Feminicídio (2015) exibida quando relevante
- **Subnotificação**: os dados refletem apenas casos registrados em Boletins de Ocorrência — o número real de ocorrências é maior
- Variações metodológicas entre estados na tipificação do feminicídio podem gerar distorções pontuais
- Os arquivos CSV são acessados apenas em **modo leitura** para evitar corrupção acidental

---

## Próximos Passos

- [ ] Integração com dados do SINAN (Ministério da Saúde) para análise de agressões não-letais
- [ ] Filtro por município para granularidade local
- [ ] Versão web com Flask para acesso sem instalação local
- [ ] Script de atualização anual automática com o Anuário FBSP mais recente

---

## Equipe

Projeto desenvolvido para a disciplina **Novas Tecnologias** — Universidade Católica de Brasília  
Professor: **Adam Smith Gontijo**

---

> **Dados:** Fórum Brasileiro de Segurança Pública (FBSP) — basedosdados.org  
> Todos os dados são públicos, agregados e anonimizados.