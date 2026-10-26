import sqlite3
import pandas as pd
import streamlit as st
import mysql.connector
import pandas as pd
import streamlit as st

from io import BytesIO

import warnings
warnings.filterwarnings("ignore",message="pandas only supports SQLAlchemy")

from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode
)

DB = "garantia_receita.db"
st.set_page_config(
    page_title="Garantia de Receita",layout="wide",
    initial_sidebar_state="expanded",page_icon="💶")

st.markdown("""
<style>
section[data-testid="stSidebar"] .stRadio label {
    font-size: 18px !important;}

section[data-testid="stSidebar"] .stRadio p {
    font-size: 18px !important;}

.sidebar-title {
    font-size: 30px;
    font-weight: bold;
    color: white;
    margin-bottom: 20px;}

.menu-title {
    font-size: 22px;
    font-weight: bold;
    margin-top: 20px;}


/* Sidebar preta */
section[data-testid="stSidebar"] {
    background-color: #111111 !important;
    border-right: 2px solid rgba(255,255,255,0.25) !important;}

/* Texto branco */
section[data-testid="stSidebar"] * {
    color: white !important;}

/* Área principal */
.stApp {
    background-color: #000510 !important;}

/* Container central */
.main {
    background-color: #000510 !important;}

/* Conteúdo */
[data-testid="stAppViewContainer"] {
    background-color: #000510 !important;}
/* Área após a sidebar */


/* Texto */
h1, h2, h3, p, label, div {
    color: white;}

#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header[data-testid="stHeader"] {background: transparent;}
section[data-testid="stSidebar"] {width: 320px !important;}
.block-container {padding-top: 1rem;}
header[data-testid="stHeader"] {height: 0.8rem !important;min-height: 0.8rem !important;background: transparent !important;}
</style>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("💶 Garantia Receita", width="stretch"):
        st.markdown("<meta http-equiv='refresh' content='0; " "url=http://192.168.16.65:5'>",unsafe_allow_html=True)
with col2:
    if st.button("💵 Destrava Ai", width="stretch"):
        st.markdown("<meta http-equiv='refresh' content='0; " "url=http://192.168.16.65:6'>",unsafe_allow_html=True)
with col3:
    if st.button("💷 Chargeback", width="stretch"):
        st.markdown("<meta http-equiv='refresh' content='0; " "url=http://192.168.16.65:8'>",unsafe_allow_html=True)
with col4:
    if st.button("📊 Locação POS", width="stretch"):
        st.markdown("<meta http-equiv='refresh' content='0; url=http://192.168.16.65:2'>",unsafe_allow_html=True)







st.title("Garantia de Receita")

# ==========================
# FUNÇÕES
# ==========================

def formatar_brl(valor, casas=2, prefixo=True):
    """Formata número no padrão brasileiro: R$ 1.234,56"""
    if pd.isna(valor):
        return ""
    texto = (
        f"{valor:,.{casas}f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    return f"R$ {texto}" if prefixo else texto

def limpar_cnpj(valor):
    """Retorna só os 14 dígitos do CNPJ (formato salvo no banco)."""
    if valor is None or pd.isna(valor):
        return ""
    texto = str(valor).strip()
    if texto.endswith(".0"):
        texto = texto[:-2]
    digitos = "".join(c for c in texto if c.isdigit())
    return digitos.zfill(14) if digitos else ""

def formatar_cnpj(valor):
    """Formata para exibição: 12.345.678/0001-90"""
    d = limpar_cnpj(valor)
    if len(d) != 14:
        return d
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"

def gerar_excel(df):
    """Gera o Excel em memória (sem gravar arquivo no disco)."""
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer.getvalue()

def conectar():
    return sqlite3.connect(DB)

@st.cache_data
def carregar_dados():

    conn = conectar()

    df = pd.read_sql(
        "SELECT * FROM cadastro",
        conn
    )

    conn.close()

    return df

@st.cache_data
def carregar_receitas():

    conn = conectar()

    df = pd.read_sql(
        "SELECT * FROM receitas",
        conn
    )

    conn.close()

    return df

def atualizar_linha(id_registro, dados):

    conn = conectar()

    cursor = conn.cursor()

    # Captura dados antigos
    cursor.execute(
        """
        SELECT PARCEIRO, CNPJ
        FROM cadastro
        WHERE id = ?
        """,
        (id_registro,)
    )

    registro_antigo = cursor.fetchone()

    parceiro_antigo = registro_antigo[0]

    campos = []

    valores = []

    for coluna, valor in dados.items():

        if coluna == "id":
            continue

        if isinstance(valor, pd.Timestamp):

            valor = valor.strftime("%Y-%m-%d")

        elif pd.isna(valor):

            valor = None

        # CNPJ sempre salvo só com dígitos no cadastro
        if coluna == "CNPJ":

            valor = limpar_cnpj(valor) or None

        campos.append(f'"{coluna}"=?')
        valores.append(valor)

    valores.append(id_registro)

    sql = f"""
    UPDATE cadastro
    SET {', '.join(campos)}
    WHERE id = ?
    """

    cursor.execute(sql, valores)

    # Atualiza receitas vinculadas
    cursor.execute(
        """
        UPDATE receitas
        SET parceiro = ?,
            cnpj = ?
        WHERE parceiro = ?
        """,
        (
            dados["PARCEIRO"],
            formatar_cnpj(dados["CNPJ"]),
            parceiro_antigo
        )
    )

    conn.commit()
    conn.close()

@st.cache_data
def carregar_full_service():
    arquivo = r"C:\Users\dylan.richards\OneDrive - SERVNET INSTITUICAO\Pré-Venda e CS - General\Sistemas\Logística\Consolidado_Gertec.xlsx"
    df = pd.read_excel(arquivo,sheet_name="Full Service")
    return df

@st.cache_data
def carregar_tpv():

    arquivo = r"C:\Users\dylan.richards\OneDrive - SERVNET INSTITUICAO\Pré-Venda e CS - General\Sistemas\Logística\Consolidado_Gertec.xlsx"

    df = pd.read_excel(
        arquivo,
        sheet_name="TPV (2)"
    )

    return df

@st.cache_data(ttl=3600)
def carregar_fechamento_no_dw():

    conn = mysql.connector.connect(
        host="dw-mysqlhwdb.valecard.com.br",       # servidor
        user="DYLAN.RICHARDS",         # usuário
        password="(Hhemjy}K]c9!*PXuwKe",       # senha
        database="bi"    # banco de dados
    )

    query = """
   WITH motivos AS (
        select CONCAT(TRIM(c.NR_TITULO + 0),TRIM(c.VALOR_TITULO)) AS opa,c.MOTIVO,c.TIPO_TITULO as TIPO
        FROM bi.dw_dm_baixas c
        WHERE c.MOTIVO IN ('COI','DAC','NOR')),
    tipos AS (
        SELECT distinct CONCAT(TRIM(a.NR_TITULO + 0),TRIM(a.VALOR_TITULO)) AS opa,a.TIPO
        FROM bi.dw_dm_titulo a
        WHERE a.TIPO IN ('BOL','NF '))
    SELECT DISTINCT
        b.PREFIXO as Prefixo,
        b.NUMERO_TITULO as `No. Titulo`,
        COALESCE(tipos.TIPO, motivos.TIPO) as Tipo,
        COALESCE(NULLIF(TRIM(b.RAZAO_SOCIAL_PROTHEUS), ''), dde.NOME_FANTASIA_PARCEIRO) as 'Razao Social',
        b.TK_EMISSAO as `DT Emissao`,
        b.TK_DT_BAIXA as `DT Baixa`, 
        b.VALOR_TITULO as `Vlr.Titulo`,
        b.SALDO as Saldo,
        b.VALOR_BAIXA as `Vlr.Liq Baix`,
        b.PARCELA as Parcela,
        motivos.MOTIVO as Motivo
    FROM bi.dw_ft_efetividade_ac b
    LEFT JOIN tipos
        ON CONCAT(TRIM(b.NUMERO_TITULO + 0),TRIM(b.VALOR_TITULO)) = tipos.opa
    LEFT JOIN motivos
        ON CONCAT(TRIM(b.NUMERO_TITULO + 0),TRIM(b.VALOR_TITULO)) = motivos.opa
    left join bi.dw_dm_estabelecimento dde 
        on b.CONTRATO_ADC_PROTHEUS = dde.NR_CONTRATO
    WHERE b.PREFIXO IN ('FRA','SET','OGE','CNW','OSF','FIM')           
    ORDER BY b.NUMERO_TITULO ASC;
    """

    df = pd.read_sql(query, conn)
    df["DT Emissao"] = pd.to_datetime(
        df["DT Emissao"]
        .astype(str)
        .str.replace(".", "", regex=False),
        format="%Y%m%d",
        errors="coerce"
    )

    df["DT Baixa"] = pd.to_datetime(
        df["DT Baixa"]
        .astype(str)
        .str.replace(".", "", regex=False),
        format="%Y%m%d",
        errors="coerce"
    )

    conn.close()

    df["DT Emissao"] = pd.to_datetime(
        df["DT Emissao"],
        errors="coerce"
    )

    df["DT Baixa"] = pd.to_datetime(
        df["DT Baixa"],
        errors="coerce"
    )

    return df

@st.cache_data
def carregar_fra():

    conn = conectar()

    df = pd.read_sql(
        "SELECT * FROM FRA",
        conn
    )

    conn.close()

    df["DT Emissao"] = pd.to_datetime(
        df["DT Emissao"],
        errors="coerce"
    )

    df["DT Baixa"] = pd.to_datetime(
        df["DT Baixa"],
        errors="coerce"
    )

    return df

# ==========================
# MENU
# ==========================

col_logo, col_titulo = st.sidebar.columns([1, 4])

with col_logo:
    st.image(r"C:\Users\dylan.richards\OneDrive - SERVNET INSTITUICAO\Pré-Venda e CS - General\Sistemas\0 - Outras melhorias\logo_own.png",width="stretch")

with col_titulo:
    st.markdown(
        """
        <div style="
            font-size:22px;
            font-weight:bold;
            margin-top:10px;
        ">
            Garantia de Receita
        </div>
        """,
        unsafe_allow_html=True
    )


st.sidebar.markdown('<div class="menu-title">Menu</div>',unsafe_allow_html=True)

menu = st.sidebar.radio(
    "Navegação",
    [
        "Home",
        "Tabela de Parceiros",
        "Tabela de Receitas",
        "Full Service",
        "Fechamento"
    ],
    label_visibility="collapsed"
)

# ==========================
# HOME
# ==========================

if menu == "Home":

    import plotly.express as px

    df = carregar_dados()

    df_receitas = carregar_receitas()

    # =====================================
    # DADOS FECHAMENTO
    # =====================================

    try:
        df_fra = carregar_fechamento_no_dw()

        df_fra["DT Emissao"] = pd.to_datetime(
            df_fra["DT Emissao"],
            errors="coerce"
        )

        df_fra["DT Baixa"] = pd.to_datetime(
            df_fra["DT Baixa"],
            errors="coerce"
        )

            

        with st.sidebar:

            st.header("Filtros Home")

            parceiro_filtro = st.selectbox(
                "Razão Social",
                ["Todos"]
                +
                sorted(
                    df_fra["Razao Social"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )
            )

            meses_emissao = sorted(
                df_fra["DT Emissao"]
                .dt.to_period("M")
                .dropna()
                .astype(str)
                .unique()
                .tolist(),
                reverse=True
            )

            mes_emissao_filtro = st.selectbox(
                "Mês/Ano Emissão",
                ["Todos"] + meses_emissao
            )

            meses_baixa = sorted(
                df_fra["DT Baixa"]
                .dt.to_period("M")
                .dropna()
                .astype(str)
                .unique()
                .tolist(),
                reverse=True
            )

            mes_baixa_filtro = st.selectbox(
                "Mês/Ano Baixa",
                ["Todos", "Não Pago"] + meses_baixa
            )

            produto_filtro = st.selectbox(
                "Produto",
                ["Todos"]
                +
                sorted(
                    df_fra["Prefixo"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )
            )

            tipo_filtro = st.selectbox(
                "Tipo",
                ["Todos"]
                +
                sorted(
                    df_fra["Tipo"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )
            )

            motivo_filtro = st.selectbox(
                "Motivo",
                ["Todos"] +
                sorted(
                    df_fra["Motivo"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()))
                    
        if motivo_filtro != "Todos":

            df_fra = df_fra[
            df_fra["Motivo"]
            .astype(str)
            .str.strip()
            == motivo_filtro
            ]

        if parceiro_filtro != "Todos":

            df_fra = df_fra[
                df_fra["Razao Social"]
                == parceiro_filtro
            ]

        if mes_emissao_filtro != "Todos":

            df_fra = df_fra[
                df_fra["DT Emissao"]
                .dt.to_period("M")
                .astype(str)
                == mes_emissao_filtro
            ]

        if mes_baixa_filtro == "Não Pago":

            df_fra = df_fra[
                df_fra["DT Baixa"].isna()
            ]

        elif mes_baixa_filtro != "Todos":

            df_fra = df_fra[
                df_fra["DT Baixa"]
                .dt.to_period("M")
                .astype(str)
                == mes_baixa_filtro
            ]

        if produto_filtro != "Todos":

            df_fra = df_fra[
                df_fra["Prefixo"]
                .astype(str)
                .str.strip()
                == produto_filtro
            ]

        if tipo_filtro != "Todos":

            df_fra = df_fra[
                df_fra["Tipo"]
                .astype(str)
                .str.strip()
                == tipo_filtro
            ]


        valor_total_fra = (
            df_fra["Vlr.Titulo"]
            .fillna(0)
            .sum()
        )

        valor_pago_fra = (
            df_fra.loc[
                df_fra["DT Baixa"].notna(),
                "Vlr.Titulo"
            ]
            .fillna(0)
            .sum()
        )

        valor_aberto_fra = (
            df_fra.loc[
                df_fra["DT Baixa"].isna(),
                "Vlr.Titulo"
            ]
            .fillna(0)
            .sum()
        )

        taxa_recebimento = (
            valor_pago_fra
            /
            valor_total_fra
            * 100
        ) if valor_total_fra > 0 else 0

    except:

        df_fra = pd.DataFrame()

        valor_total_fra = 0
        valor_pago_fra = 0
        valor_aberto_fra = 0
        taxa_recebimento = 0

    # =====================================
    # GESTÃO FINANCEIRA
    # =====================================


    st.header(" 💰 Gestão Financeira")

    col1, col2, col3, col4 = st.columns(4)
    with col1:

        st.metric(
            "Carteira Total",
            formatar_brl(valor_total_fra, 0)
        )

    with col2:

        st.metric(
            "Recebido",
            formatar_brl(valor_pago_fra, 0)
        )

    with col3:

        st.metric(
            "Em Aberto",
            formatar_brl(valor_aberto_fra, 0)
        )

    with col4:

        st.metric(
            "Taxa de Recebimento",
            f"{taxa_recebimento:.1f}%"
        )

    st.divider()

    # =====================================
    # QUEM MAIS ESTÁ DEVENDO?
    # =====================================

    st.subheader("❓ Quem mais está devendo?")

    if not df_fra.empty:

        top_devedores = (
            df_fra[
                df_fra["DT Baixa"].isna()
            ]
            .groupby(
                ["Razao Social", "Prefixo"],
                as_index=False
            )["Vlr.Titulo"]
            .sum()
        )

        top10 = (
            top_devedores
            .groupby("Razao Social")["Vlr.Titulo"]
            .sum()
            .nlargest(10)
            .reset_index()
        )

        top_devedores = top_devedores[
            top_devedores["Razao Social"]
            .isin(top10["Razao Social"])
        ]

        top_devedores = top_devedores.sort_values(
        "Vlr.Titulo",
        ascending=True
    )

        top_devedores["Valor_Formatado"] = (
            top_devedores["Vlr.Titulo"]
            .apply(
                lambda x:
                formatar_brl(x, 0)
            )
        )
        
        fig = px.bar(
            top_devedores,
            y="Razao Social",
            x="Vlr.Titulo",
            color="Prefixo",
            orientation="h"
        )

        fig.update_traces(
            customdata=top_devedores[["Valor_Formatado"]],
            hovertemplate=
            "<b>%{y}</b><br>" +
            "📦 Produto: %{fullData.name}<br>" +
            "💰 Valor: %{customdata[0]}" +
            "<extra></extra>"
        )

        fig.update_layout(
            paper_bgcolor="#000510",
            plot_bgcolor="#000510",
            font=dict(color="white"),
            xaxis_title="",
            yaxis_title="",
            legend_title_text="Produto",
            hoverlabel=dict(
                font_size=16,
                font_family="Arial",
                bgcolor="#08090A",
                bordercolor="#7DB7E8"
            )
        )

        totais = (
            top_devedores
            .groupby("Razao Social")["Vlr.Titulo"]
            .sum()
            .reset_index()
        )

        for _, row in totais.iterrows():

            fig.add_annotation(
                x=row["Vlr.Titulo"],
                y=row["Razao Social"],
                text=(
                    formatar_brl(row["Vlr.Titulo"], 0)
                ),
                showarrow=False,
                xanchor="left",
                font=dict(
                    color="white",
                    size=15
                )
            )


        fig.update_traces(
            texttemplate="%{text:,.0f}",
            textposition="outside",
            textfont=dict(
                color="white",
                size=12
            )
        )

        fig.update_yaxes(
            categoryorder="total ascending",
            tickfont=dict(
                size=14,
                color="white"
            )
        )

        fig.update_xaxes(
            tickfont=dict(
                size=16,
                color="white"
            )
        )



        st.plotly_chart(
            fig,
            width="stretch"
        )

    # =====================================
    # RECEBIMENTO E EVOLUÇÃO
    # =====================================

    col1, col2 = st.columns(2)

    with col1:

        import plotly.graph_objects as go

        st.subheader(
            "❓ Qual percentual já recebemos?"
        )

        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=taxa_recebimento,
                number={
                    "suffix": "%",
                    "font": {
                        "size": 50,
                        "color": "white"
                    }
                },
                gauge={
                    "axis": {
                        "range": [0, 100],
                        "tickmode": "array",
                        "tickvals": [50, 80],
                        "ticktext": ["50%", "80%"],
                        "tickcolor": "white",
                        "tickfont": {
                            "size": 13,
                            "color": "white"
                        }
                    },

                    "bar": {
                        "color": "#7DB7E8",
                        "thickness": 0.55
                    },

                    "steps": [
                        {
                            "range": [0, 50],
                            "color": "rgba(220,53,69,0.20)"
                        },
                        {
                            "range": [50, 80],
                            "color": "rgba(255,193,7,0.15)"
                        },
                        {
                            "range": [80, 100],
                            "color": "rgba(25,135,84,0.20)"
                        }
                    ]

                }
            )
        )

        fig.update_layout(
            paper_bgcolor="#000510",
            plot_bgcolor="#000510",
            font=dict(
                color="white"
            ),
            height=350,
            margin=dict(
                t=20,
                b=10,
                l=10,
                r=10
            )
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )

    with col2:

        st.subheader("❓ Quais parceiros representam o maior risco financeiro?")

        devedores = (df_fra[
                df_fra["DT Baixa"].isna()].copy())

        risco = (
            devedores
            .groupby(
                ["Razao Social", "Prefixo"],
                as_index=False
            )
            .agg(
                Valor_Aberto=(
                    "Vlr.Titulo",
                    "sum"
                ),
                Quantidade=(
                    "Vlr.Titulo",
                    "count"
                )
            )
        )

        risco["Valor_Aberto_BR"] = risco["Valor_Aberto"].map(
            lambda x: formatar_brl(x, 0)
        )

        carteira_total = (
            df_fra
            .groupby("Razao Social")
            ["Vlr.Titulo"]
            .sum()
            .reset_index()
        )

        carteira_total.columns = [
            "Razao Social",
            "Carteira_Total"
        ]

        risco = risco.merge(
            carteira_total,
            on="Razao Social",
            how="left"
        )

        fig = px.scatter(
            risco,
            x="Quantidade",
            y="Valor_Aberto",
            size="Carteira_Total",
            color="Prefixo",
            hover_name="Razao Social",
            size_max=60
        )

        fig.update_traces(
            marker=dict(
                line=dict(
                    width=1,
                    color="white"
                )
            ),

            customdata=risco[["Prefixo", "Valor_Aberto_BR"]],

            hovertemplate=
            "<b>%{hovertext}</b><br>" +

            "📦 Produto: %{customdata[0]}<br>" +

            "📄 Qtd. Títulos: %{x}<br>" +

            "💰 Em Aberto: %{customdata[1]}" +

            "<extra></extra>"
        )

        fig.update_layout(
            paper_bgcolor="#000510",
            plot_bgcolor="#000510",
            font=dict(
                color="white"
            ),
            xaxis_title="Quantidade de Títulos",
            yaxis_title="Valor em Aberto",
            legend_title_text="Produto",
            hoverlabel=dict(
                font_size=16,
                font_family="Arial",
                bgcolor="#011627",
                bordercolor="#7DB7E8"
            )
        )

        fig.update_yaxes(
            tickfont=dict(
                size=16,
                color="white"
            )
        )
        fig.update_xaxes(
            tickfont=dict(
                size=16,
                color="white"
            )
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )


    st.subheader("📊 Cobranças x Pagamentos ao Longo do Tempo")
    st.write("Este gráfico responde: Quanto cobramos naquele mês? Quanto recebemos naquele mês? E a efetivade é Quanto foi liquidado dentro do próprio mês cobrado?")

    if not df_fra.empty:

        data_inicio = pd.Timestamp("2026-01-01")

        # =====================================
        # COBRANÇAS
        # =====================================

        cobrancas = df_fra[
            df_fra["DT Emissao"] >= data_inicio].copy()

        cobrancas["Mes"] = (
            cobrancas["DT Emissao"]
            .dt.to_period("M")
            .astype(str))

        cobrancas_agrupado = (
            cobrancas
            .groupby("Mes")["Vlr.Titulo"]
            .sum()
            .reset_index())

        cobrancas_agrupado["Tipo"] = "Cobrado"

        # =====================================
        # PAGAMENTOS
        # =====================================

        pagamentos = df_fra[
            (df_fra["DT Baixa"].notna()) &
            (df_fra["DT Baixa"] >= data_inicio)
        ].copy()

        pagamentos["Mes"] = (
            pagamentos["DT Baixa"]
            .dt.to_period("M")
            .astype(str))

        pagamentos_agrupado = (
            pagamentos
            .groupby("Mes")["Vlr.Titulo"]
            .sum()
            .reset_index())

        pagamentos_agrupado["Tipo"] = "Pago"

        # =====================================
        # EFETIVIDADE
        # =====================================

        efetividade = df_fra.copy()

        efetividade = efetividade[
            efetividade["DT Emissao"] >= data_inicio]

        efetividade["Mes_Emissao"] = (
            efetividade["DT Emissao"]
            .dt.to_period("M"))

        efetividade["Mes_Baixa"] = (
            efetividade["DT Baixa"]
            .dt.to_period("M"))

        efetividade["Efetivo"] = (
            efetividade["Mes_Emissao"]
            ==
            efetividade["Mes_Baixa"])

        emitidos = (
            efetividade
            .groupby("Mes_Emissao")
            ["Vlr.Titulo"]
            .sum()
            .reset_index())

        emitidos.columns = [
            "Mes",
            "Emitido"]

        efetivos = (
            efetividade[
                efetividade["Efetivo"]]
            .groupby("Mes_Emissao")
            ["Vlr.Titulo"]
            .sum()
            .reset_index())

        efetivos.columns = [
            "Mes",
            "Efetivo"]

        taxa = emitidos.merge(
            efetivos,
            on="Mes",
            how="left")

        taxa["Efetivo"] = (
            taxa["Efetivo"]
            .fillna(0))

        taxa["Efetividade"] = (
            taxa["Efetivo"]
            /
            taxa["Emitido"]
            * 100)

        taxa["Mes"] = (
            taxa["Mes"]
            .astype(str))

        #Mensagem ao passar o mouse
        taxa["Cobrado_Formatado"] = taxa["Emitido"].apply(
            lambda x:
            formatar_brl(x, 0))

        taxa["Recebido_Formatado"] = taxa["Mes"].map(
            pagamentos_agrupado.set_index("Mes")["Vlr.Titulo"]).fillna(0)

        taxa["Recebido_Formatado"] = taxa[
            "Recebido_Formatado"].apply(
            lambda x:
            formatar_brl(x, 0))

        taxa["Efetivo_Formatado"] = taxa["Efetivo"].apply(
            lambda x:
            formatar_brl(x, 0))

        # =====================================
        # BARRAS
        # =====================================

        comparativo = pd.concat(
            [
                cobrancas_agrupado,
                pagamentos_agrupado],
            ignore_index=True)

        comparativo["Valor_Formatado"] = comparativo["Vlr.Titulo"].apply(
            lambda x:
            formatar_brl(x, 0, prefixo=False))

        fig = px.bar(
            comparativo,
            x="Mes",
            y="Vlr.Titulo",
            color="Tipo",
            barmode="group",
            text="Valor_Formatado",
            color_discrete_map={
                "Cobrado": "#1E5AA8",
                "Pago": "#7DB7E8"
            })

        fig.update_traces(
            texttemplate="%{text}",
            textposition="outside",
            textangle=0,
            textfont=dict(
                color="white",
                size=16))

        # =====================================
        # LINHA EFETIVIDADE
        # =====================================

        taxa["Efetividade_Formatada"] = (
            taxa["Efetividade"]
            .round(1)
            .astype(str)
            + "%")

        nomes_meses = {
            1: "Janeiro",
            2: "Fevereiro",
            3: "Março",
            4: "Abril",
            5: "Maio",
            6: "Junho",
            7: "Julho",
            8: "Agosto",
            9: "Setembro",
            10: "Outubro",
            11: "Novembro",
            12: "Dezembro"
        }

        taxa["Mes_Hover"] = pd.to_datetime(
            taxa["Mes"]).apply(
            lambda x:
            f"{nomes_meses[x.month]} {x.year}")

        fig.add_scatter(
            x=taxa["Mes"],
            y=taxa["Efetividade"],
            yaxis="y2",
            mode="lines+markers+text",
            name="Efetividade",

            line=dict(
                color="rgba(250,252,140,0.6)",
                width=4),

            marker=dict(
                size=12,
                color="#F5FFF5"),

            text=taxa["Efetividade_Formatada"],

            textfont=dict(
                size=16,
                color="#E5FF00"),

            textposition="top center",

            customdata=list(
                zip(
                    taxa["Mes_Hover"],
                    taxa["Cobrado_Formatado"],
                    taxa["Recebido_Formatado"],
                    taxa["Efetivo_Formatado"],
                    taxa["Efetividade_Formatada"])),


            hovertemplate=
                "<b>%{customdata[0]}</b><br><br>" +

                "💰 Cobrado no mês:<br>" +
                "<b>%{customdata[1]}</b><br><br>" +

                "✅ Recebido no mês:<br>" +
                "<b>%{customdata[2]}</b><br><br>" +

                "⚡ Recebido no mesmo mês da cobrança:<br>" +
                "<b>%{customdata[3]}</b><br><br>" +

                "📊 Efetividade:<br>" +
                "<b>%{customdata[4]}</b>" +

                "<extra></extra>")


        # =====================================
        # LAYOUT
        # =====================================

        fig.update_layout(
            paper_bgcolor="#000510",
            plot_bgcolor="#000510",
            font=dict(
                color="white"),
            xaxis_title="",
            yaxis_title="Valor (R$)",
            legend_title_text="",
            uniformtext_minsize=10,
            uniformtext_mode="hide",

            yaxis=dict(
                tickfont=dict(
                    size=16,
                    color="white")),

            yaxis2=dict(
                title="Efetividade (%)",
                overlaying="y",
                side="right",
                tickfont=dict(
                    size=15,
                    color="rgba(250,252,140,0.8)"),
                range=[0, 100]),
            hoverlabel=dict(
            font_size=16,
            font_family="Arial",
            bgcolor="#011627",
            bordercolor="#7DB7E8"))

        fig.update_xaxes(
            tickfont=dict(
                size=16,
                color="white"))

        st.plotly_chart(
            fig,
            width="stretch")

    # =====================================
    # Dinheiro parado
    # =====================================
    st.subheader(
        "❓ Há quantos dias os título não pagos estão sem pagar e qual o total deles? ")

    inadimplencia = (
        df_fra[
            df_fra["DT Baixa"].isna()
        ]
        .copy()
    )

    if not inadimplencia.empty:

        inadimplencia["Dias"] = (
            pd.Timestamp.today()
            - inadimplencia["DT Emissao"]
        ).dt.days

        inadimplencia["Faixa"] = pd.cut(
            inadimplencia["Dias"],
            bins=[
                0,
                30,
                60,
                90,
                180,
                99999
            ],
            labels=[
                "0-30",
                "31-60",
                "61-90",
                "91-180",
                "180+"
            ]
        )

        aging = (
            inadimplencia
            .groupby("Faixa")
            .agg(
                Valor_Total=("Vlr.Titulo", "sum"),
                Quantidade_Titulos=("Vlr.Titulo", "count")
            )
            .reset_index()
        )

        aging["Valor_Formatado"] = aging[
            "Valor_Total"
        ].apply(
            lambda x:
            formatar_brl(x, 2)
        )


        aging["Label"] = aging["Valor_Total"].apply(
            lambda x:
            formatar_brl(x, 0)
        )
        
        fig = px.bar(
            aging,
            y="Faixa",
            x="Valor_Total",
            orientation="h",
            text="Label"
        )

        fig.update_traces(
            texttemplate="%{text}",
            textposition="outside",
            textfont=dict(
                color="white",
                size=16),

            customdata=list(
                zip(
                    aging["Quantidade_Titulos"],
                    aging["Valor_Formatado"]
                )
            ),

            hovertemplate=
                "<b>%{y} dias</b><br>" +

                "📄 Quantidade de títulos: <b>%{customdata[0]}</b><br>" +
                "💰 Valor total: <b>%{customdata[1]}</b>"
                "<extra></extra>"
        )

        fig.update_layout(
            paper_bgcolor="#000510",
            plot_bgcolor="#000510",
            font=dict(color="white"),
            xaxis_title="",
            yaxis_title="",
            margin=dict(r=120),
            hoverlabel=dict(
                font_size=16,
                font_family="Arial",
                bgcolor="#011627",
                bordercolor="#7DB7E8"
            )
        )



        fig.update_yaxes(
            tickfont=dict(
                size=16,
                color="white"
            )
        )
        fig.update_xaxes(
            tickfont=dict(
                size=16,
                color="white"
            ),
            range=[0,aging["Valor_Total"].max() * 1.13]
        )


        st.plotly_chart(
            fig,
            width="stretch"
        )

    # =====================================
    # PARCEIROS CRÍTICOS
    # =====================================
    col1, espaco, col2 =st.columns([1, 0.05, 1])

    with col1:
        st.subheader("📉 Quem merecem atenção imediata?")

        if not df_fra.empty:
            criticos = (
                df_fra
                .groupby("Razao Social")
                .agg(
                    Total=("Vlr.Titulo", "sum"),
                    Pago=(
                        "Vlr.Titulo",
                        lambda x:
                        x[
                            df_fra.loc[
                                x.index,
                                "DT Baixa"
                            ].notna()
                        ].sum()
                    )
                )
                .reset_index()
            )

            criticos["Em Aberto"] = (
                criticos["Total"]
                - criticos["Pago"]
            )

            criticos = (
                criticos
                .sort_values(
                    "Em Aberto",
                    ascending=False
                )
                .head(10)
            )

            criticos["Total"] = criticos["Total"].apply(
                lambda x:
                formatar_brl(x, 0)
            )

            criticos["Pago"] = criticos["Pago"].apply(
                lambda x:
                formatar_brl(x, 0)
            )

            criticos["Em Aberto"] = criticos[
                "Em Aberto"
            ].apply(
                lambda x:
                formatar_brl(x, 0)
            )

            st.dataframe(
                criticos,
                width="stretch",
                hide_index=True,
                column_config={"Razao Social": st.column_config.TextColumn("Razão Social",width=200)}
            )

    with col2:   
        st.subheader("📈 Quem possui o melhor histórico de pagamento?")

        if not df_fra.empty:

            saudaveis = (
                df_fra
                .groupby("Razao Social")
                .agg(
                    Total=("Vlr.Titulo", "sum"),
                    Pago=(
                        "Vlr.Titulo",
                        lambda x:
                        x[
                            df_fra.loc[
                                x.index,
                                "DT Baixa"
                            ].notna()
                        ].sum()
                    )
                )
                .reset_index()
            )

            saudaveis["% Recebimento"] = (
                saudaveis["Pago"]
                /
                saudaveis["Total"]
                * 100
            )

            saudaveis = (
                saudaveis
                .sort_values(
                    "% Recebimento",
                    ascending=False
                )
                .head(10)
            )

            saudaveis["Total"] = saudaveis["Total"].apply(
                lambda x:
                formatar_brl(x, 0)
            )

            saudaveis["Pago"] = saudaveis["Pago"].apply(
                lambda x:
                formatar_brl(x, 0)
            )

            saudaveis["% Recebimento"] = (
                saudaveis["% Recebimento"]
                .round(1)
                .astype(str)
                + "%"
            )

            st.dataframe(
                saudaveis,
                width="stretch",
                hide_index=True,
                column_config={"Razao Social": st.column_config.TextColumn("Razão Social",width=200)}
            )

    st.divider()

    st.header("📄 Indicadores Operacionais")



        # =====================================
    # INDICADORES
    # =====================================

    total_parceiros = len(df)

    total_receitas = len(df_receitas)

    receita_total = (
        df_receitas["valor"]
        .fillna(0)
        .sum()
    )

    try:

        df_fs = carregar_full_service()

        df_fs["Data Histórico"] = pd.to_datetime(
            df_fs["Data Histórico"],
            dayfirst=True,
            errors="coerce"
        )

        mes_atual = pd.Timestamp.today().to_period("M")

        quantidade_full_service = len(
            df_fs[
                df_fs["Data Histórico"]
                .dt.to_period("M")
                == mes_atual
            ][
                ["Terminal", "Parceiro"]
            ].drop_duplicates()
        )

    except:

        quantidade_full_service = 0

    df["DATA ASSINATURA CONTRATO "] = pd.to_datetime(
        df["DATA ASSINATURA CONTRATO "],
        errors="coerce"
    )

    ultimo_contrato = df.loc[
        df["DATA ASSINATURA CONTRATO "]
        .idxmax()
    ]

    parceiro_mais_recente = (
        ultimo_contrato["PARCEIRO"]
    )

    data_mais_recente = (
        ultimo_contrato[
            "DATA ASSINATURA CONTRATO "
        ]
        .strftime("%d/%m/%Y")
    )

    primeiro_nome = (
        parceiro_mais_recente
        .split()[0]
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:

        st.metric(
            "Parceiros Cadastrados",
            total_parceiros
        )

    with col2:

        st.metric(
            "Receitas Cadastradas",
            total_receitas
        )

    with col3:

        st.metric(
            "Máquinas Full Service",
            quantidade_full_service
        )

    with col4:

        st.metric(
            "Receita Mensal",
            formatar_brl(receita_total, 2)
        )

    with col5:

        st.metric(
            "Último Contrato",
            primeiro_nome
        )

        st.caption(
            f"Assinado em {data_mais_recente}"
        )

    # =====================================
    # GRÁFICOS
    # =====================================

    col1, col2 = st.columns(2)

    with col1:

        st.subheader(
            "Como os parceiros estão distribuídos por classificação?"
        )

        classificacao = (
            df["CLASSIFICAÇÃO"]
            .fillna("")
            .replace("", "Sem Classificação")
            .astype(str)
            .str.strip()
        )

        classificacao = classificacao.replace(
            {
                "SEM CLASSIFICAÇÃO":
                "Sem Classificação",
                "Sem classificação":
                "Sem Classificação",
                "":
                "Sem Classificação"
            }
        )

        classificacao = (
            classificacao
            .value_counts()
            .reset_index()
        )

        classificacao.columns = [
            "Classificação",
            "Quantidade"
        ]

        fig = px.bar(
            classificacao,
            x="Classificação",
            y="Quantidade",
            text="Quantidade"
        )

        fig.update_traces(
            textposition="outside",
            textfont=dict(
                color="white",
                size=14
            )
        )

        fig.update_layout(
            paper_bgcolor="#000510",
            plot_bgcolor="#000510",
            font=dict(color="white"),
            xaxis_title="",
            yaxis_title="Quantidade",
            showlegend=False
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )

    with col2:

        st.subheader(
            "Como evoluiu a assinatura de contratos?"
        )

        data_inicio = (
            pd.Timestamp.today()
            - pd.DateOffset(months=12)
        )

        contratos_mes = (
            df[
                df[
                    "DATA ASSINATURA CONTRATO "
                ] >= data_inicio
            ]
            .copy()
        )

        contratos_mes["MesAno"] = (
            contratos_mes[
                "DATA ASSINATURA CONTRATO "
            ]
            .dt.to_period("M")
        )

        contratos_mes = (
            contratos_mes
            .groupby("MesAno")
            .size()
            .reset_index(
                name="Quantidade"
            )
        )

        nomes_meses = {
            1: "Janeiro",
            2: "Fevereiro",
            3: "Março",
            4: "Abril",
            5: "Maio",
            6: "Junho",
            7: "Julho",
            8: "Agosto",
            9: "Setembro",
            10: "Outubro",
            11: "Novembro",
            12: "Dezembro"
        }

        contratos_mes["Mês"] = (
            contratos_mes["MesAno"]
            .apply(
                lambda x:
                f"{nomes_meses[x.month]}/{x.year}"
            )
        )

        fig = px.line(
            contratos_mes,
            x="Mês",
            y="Quantidade",
            markers=True
        )

        fig.update_traces(
            line=dict(
                color="#7DB7E8",
                width=3
            ),
            marker=dict(
                size=10,
                color="#7DB7E8"
            )
        )

        fig.update_layout(
            paper_bgcolor="#000510",
            plot_bgcolor="#000510",
            font=dict(color="white"),
            xaxis_title="",
            yaxis_title="Quantidade",
            showlegend=False
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )

    st.divider()

    # =====================================
    # TOP PARCEIROS
    # =====================================

    st.subheader("❓ Quais parceiros possuem mais cobranças cadastradas?")

    top_parceiros = (
        df_receitas
        .groupby("parceiro")
        .agg(
            Quantidade=(
                "parceiro",
                "size"
            ),
            Valor_Mensal=(
                "valor",
                lambda x:
                x[
                    df_receitas.loc[
                        x.index,
                        "mensal"
                    ] == 1
                ].sum()
            )
        )
        .reset_index()
        .sort_values(
            "Quantidade",
            ascending=False
        )
        .head(10)
    )

    top_parceiros = top_parceiros.rename(
        columns={
            "parceiro":
            "Parceiro",
            "Valor_Mensal":
            "Valor Mensal"
        }
    )

    top_parceiros[
        "Valor Mensal"
    ] = (
        top_parceiros[
            "Valor Mensal"
        ]
        .fillna(0)
        .apply(
            lambda x:
            formatar_brl(x, 2)
        )
    )

    st.dataframe(
        top_parceiros,
        width="stretch",
        hide_index=True
    )


# ==========================
# TABELA PARCEIROS
# ==========================
if menu == "Tabela de Parceiros":
    df = carregar_dados()

    st.subheader("Tabela de Parceiros")

    resultado = df.copy()

    # =====================================
    # INDICADORES
    # =====================================

    try:

        df_ind = df.copy()

        df_ind["DATA ASSINATURA CONTRATO "] = pd.to_datetime(
            df_ind["DATA ASSINATURA CONTRATO "],
            errors="coerce"
        )

        
        df_ind["DATA ENCERRAMENTO CONTRATO "] = pd.to_datetime(
            df_ind["DATA ENCERRAMENTO CONTRATO "],
            errors="coerce"
        )

        ultimo_registro = df_ind.loc[
            df_ind["DATA ASSINATURA CONTRATO "].idxmax()
        ]

        parceiro_completo = str(
            ultimo_registro["PARCEIRO"]
        )

        primeiro_nome = parceiro_completo.split()[0]

        data_ultimo = ultimo_registro[
            "DATA ASSINATURA CONTRATO "
        ].strftime("%d/%m/%Y")

    except:

        primeiro_nome = "-"
        data_ultimo = "-"

    
    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Quantidade de Parceiros",
            len(resultado)
        )

    with col2:

        st.metric(
            "Último Parceiro",
            f"{primeiro_nome} - {data_ultimo}"
        )

    # =====================================
    # FORMATAÇÕES
    # =====================================

    resultado["CNPJ"] = resultado["CNPJ"].apply(formatar_cnpj)

    resultado["DATA ASSINATURA CONTRATO "] = (
        pd.to_datetime(
            resultado["DATA ASSINATURA CONTRATO "],
            errors="coerce"
        )
        .dt.strftime("%Y-%m-%d")
    )

    resultado["DATA ENCERRAMENTO CONTRATO "] = (
        pd.to_datetime(
            resultado["DATA ENCERRAMENTO CONTRATO "],
            errors="coerce"
        )
        .dt.strftime("%Y-%m-%d")
    )

    resultado = resultado.sort_values(
        "DATA ASSINATURA CONTRATO ",
        ascending=False
    )

    # =====================================
    # GRID
    # =====================================

    gb = GridOptionsBuilder.from_dataframe(
        resultado
    )

    gb.configure_default_column(
        editable=True,
        filter=True,
        sortable=True,
        resizable=True
    )

    gb.configure_column(
        "id",
        width=1,
        maxWidth=30,
        editable=False
    )

    gb.configure_column(
        "DATA ASSINATURA CONTRATO ",
        editable=True,
        cellEditor='agDateStringCellEditor'
    )

    gb.configure_column(
        "DATA ENCERRAMENTO CONTRATO ",
        editable=True,
        cellEditor='agDateStringCellEditor'
    )

    gb.configure_selection(
        selection_mode="single",
        use_checkbox=True
    )
    
    grid = AgGrid(
        resultado,
        gridOptions=gb.build(),
        height=500,
        fit_columns_on_grid_load=True
    )

    dados_editados = pd.DataFrame(
        grid["data"]
    )


    #dados_editados["DATA ASSINATURA CONTRATO "] = pd.to_datetime(
    #    dados_editados["DATA ASSINATURA CONTRATO "],
    #    errors="coerce"
    #).dt.strftime("%Y-%m-%d")

    #dados_editados["DATA ENCERRAMENTO CONTRATO "] = pd.to_datetime(
    #    dados_editados["DATA ENCERRAMENTO CONTRATO "],
    #    errors="coerce"
    #).dt.strftime("%Y-%m-%d")



    selecionados = pd.DataFrame(
        grid.get("selected_rows", [])
    )

    # =====================================
    # BOTÕES
    # =====================================

    col1, col2, col3 = st.columns(3)

    with col1:

        if st.button("Salvar Alterações"):

            dados_editados = pd.DataFrame(
                grid["data"]
            )

            dados_editados["DATA ASSINATURA CONTRATO "] = pd.to_datetime(
                dados_editados["DATA ASSINATURA CONTRATO "],
                errors="coerce"
            ).dt.strftime("%Y-%m-%d")

            dados_editados["DATA ENCERRAMENTO CONTRATO "] = pd.to_datetime(
                dados_editados["DATA ENCERRAMENTO CONTRATO "],
                errors="coerce"
            ).dt.strftime("%Y-%m-%d")

            for _, linha in dados_editados.iterrows():

                atualizar_linha(
                    linha["id"],
                    linha.to_dict()
                )

            st.cache_data.clear()
            st.success("Alterações salvas.")
            st.rerun()

    with col2:

        st.download_button(
            "Exportar Excel",
            gerar_excel(resultado),
            file_name="cadastro.xlsx"
        )

    with col3:

        if st.button("Excluir Parceiro Selecionado"):

            if selecionados.empty:

                st.warning(
                    "Selecione uma linha."
                )

            else:

                id_parceiro = int(
                    selecionados.iloc[0]["id"]
                )

                conn = conectar()

                conn.execute(
                    """
                    DELETE FROM cadastro
                    WHERE id = ?
                    """,
                    (id_parceiro,)
                )

                conn.commit()
                conn.close()

                st.cache_data.clear()
                st.success("Parceiro excluído.")

                st.rerun()


    with st.expander("➕ Novo Parceiro"):

        campos = {}

        colunas = [
            c for c in df.columns
            if c != "id"
        ]

        for coluna in colunas:

            nome_coluna = coluna.upper()

            if "DATA ASSINATURA" in nome_coluna:

                campos[coluna] = st.date_input(
                    coluna,
                    key=f"novo_{coluna}"
                )

            elif "DATA ENCERRAMENTO" in nome_coluna:

                campos[coluna] = st.date_input(
                    coluna,
                    value=None,
                    key=f"novo_{coluna}"
                )

            elif "CLASSIFICAÇÃO" in nome_coluna:

                campos[coluna] = st.selectbox(
                    coluna,
                    [
                        "ATIVOS",
                        "EM DISTRATO",
                        "LEGADO"
                    ],
                    key=f"novo_{coluna}"
                )

            else:

                campos[coluna] = st.text_input(
                    coluna,
                    key=f"novo_{coluna}"
                )

        if st.button("Salvar Novo Parceiro"):

            dados_salvar = campos.copy()

            for coluna in dados_salvar:

                if "DATA" in coluna.upper():

                    if dados_salvar[coluna]:

                        dados_salvar[coluna] = (
                            pd.to_datetime(
                                dados_salvar[coluna]
                            )
                            .strftime("%Y-%m-%d")
                        )

            if "CNPJ" in dados_salvar:

                dados_salvar["CNPJ"] = limpar_cnpj(
                    dados_salvar["CNPJ"]
                )

            conn = conectar()

            pd.DataFrame(
                [dados_salvar]
            ).to_sql(
                "cadastro",
                conn,
                if_exists="append",
                index=False
            )

            conn.close()
            st.cache_data.clear()
            st.success(
                "Parceiro cadastrado com sucesso."
            )

            st.rerun()



# ==========================
# TABELA RECEITAS
# ==========================
if menu == "Tabela de Receitas":

    st.subheader("Tabela de Receitas")

    try:

        df_receitas = carregar_receitas()

    except:

        st.warning("Nenhuma receita cadastrada.")
        st.stop()

    # =====================================
    # FILTROS
    # =====================================
    sidebar = st.sidebar.container()
    with sidebar:

        st.header("Filtros Receitas")
        parceiro_filtro = st.selectbox(
            "Parceiro",
            ["Todos"] + sorted(
                df_receitas["parceiro"]
                .dropna()
                .unique()
                .tolist()
            )
        )
        cobranca_filtro = st.selectbox(
            "Nome da Cobrança",
            ["Todos"] + sorted(
                df_receitas["nome_cobranca"]
                .dropna()
                .unique()
                .tolist()
            )
        )

    resultado = df_receitas.copy()

    if parceiro_filtro != "Todos":

        resultado = resultado[
            resultado["parceiro"] == parceiro_filtro
        ]

    if cobranca_filtro != "Todos":

        resultado = resultado[
            resultado["nome_cobranca"] == cobranca_filtro
        ]

    # =====================================
    # INDICADORES
    # =====================================

    qtd_cobrancas = len(resultado)

    valor_total = resultado["valor"].fillna(0).sum()

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Quantidade de Cobranças Cadastradas",
            qtd_cobrancas
        )


    with col2:

        st.metric(
            "Valor Total",
            formatar_brl(valor_total, 2)
        )

    # =====================================
    # FORMATAÇÃO
    # =====================================

    resultado["mensal"] = resultado["mensal"].map({
        1: "Sim",
        0: "Não"
    })

    resultado = resultado.rename(
        columns={
            "id": "ID",
            "parceiro": "Parceiro",
            "cnpj": "CNPJ",
            "nome_cobranca": "Nome da Cobrança",
            "valor": "Valor",
            "mensal": "Mensal"
        }
    )


    # =====================================
    # GRID
    # =====================================

    gb = GridOptionsBuilder.from_dataframe(resultado)

    gb.configure_default_column(
        editable=True,
        filter=True,
        sortable=True,
        resizable=True
    )

    gb.configure_column(
        "ID",
        width=1,
        maxWidth=30,
        editable=False
    )

    gb.configure_selection(
        selection_mode="single",
        use_checkbox=True
    )

    grid = AgGrid(
        resultado,
        gridOptions=gb.build(),
        fit_columns_on_grid_load=True,
        height=500
    )

    dados_editados = pd.DataFrame(grid["data"])

    # Captura linha selecionada
    selecionados = pd.DataFrame(
        grid.get("selected_rows", [])
    )

    # =====================================
    # BOTÕES
    # =====================================

    col1, col2, col3 = st.columns(3)

    with col1:

        if st.button("Salvar Alterações"):

            # Validação: todos os campos obrigatórios (Valor pode ser 0)
            def vazio(v):
                return v is None or pd.isna(v) or str(v).strip() == ""

            invalidas = []

            for _, linha in dados_editados.iterrows():

                faltando = [
                    c for c in ["Parceiro", "CNPJ", "Nome da Cobrança", "Mensal"]
                    if vazio(linha[c])
                ]

                if vazio(linha["Valor"]) or pd.isna(pd.to_numeric(linha["Valor"], errors="coerce")):
                    faltando.append("Valor")

                if faltando:
                    invalidas.append(f"ID {linha['ID']}: {', '.join(faltando)}")

            if invalidas:
                st.error(
                    "Preencha todos os campos antes de salvar (Valor pode ser 0):\n\n- "
                    + "\n- ".join(invalidas)
                )
            else:

                conn = conectar()
                cursor = conn.cursor()

                for _, linha in dados_editados.iterrows():

                    cursor.execute("""
                        UPDATE receitas
                        SET parceiro=?,
                            cnpj=?,
                            nome_cobranca=?,
                            valor=?,
                            mensal=?
                        WHERE id=?
                    """,
                    (
                        linha["Parceiro"],
                        linha["CNPJ"],
                        linha["Nome da Cobrança"].upper().strip(),
                        linha["Valor"],
                        1 if linha["Mensal"] == "Sim" else 0,
                        linha["ID"]
                    ))

                conn.commit()
                conn.close()

                st.cache_data.clear()
                st.success("Receitas atualizadas.")

                st.rerun()

    with col2:

        st.download_button(
            "Exportar Excel",
            gerar_excel(resultado),
            file_name="Receitas.xlsx"
        )

    with col3:

        if st.button("Excluir Receita Selecionada"):

            if selecionados.empty:

                st.warning(
                    "Selecione uma linha na tabela."
                )

            else:

                id_receita = int(
                    selecionados.iloc[0]["ID"]
                )

                conn = conectar()

                conn.execute(
                    """
                    DELETE FROM receitas
                    WHERE id = ?
                    """,
                    (id_receita,)
                )

                conn.commit()
                conn.close()

                st.cache_data.clear()
                st.success("Receita excluída.")

                st.rerun()


    with st.expander("➕ Nova Receita"):

        parceiros = carregar_dados()
        parceiro_selecionado = st.selectbox(
            "Parceiro",
            parceiros["PARCEIRO"].sort_values().tolist(),
            key="nova_receita_parceiro"
        )

        dados_parceiro = parceiros[
            parceiros["PARCEIRO"] == parceiro_selecionado
        ].iloc[0]

        cnpj = formatar_cnpj(dados_parceiro["CNPJ"])

        st.text_input(
            "CNPJ",
            value=cnpj,
            disabled=True,
            key="nova_receita_cnpj"
        )

        receitas_existentes = sorted(
            carregar_receitas()["nome_cobranca"]
            .dropna()
            .str.upper()
            .unique()
            .tolist()
        )

        nome_cobranca = st.selectbox(
            "Nome da Cobrança",
            options=receitas_existentes,
            index=None,
            placeholder="Digite ou selecione uma cobrança...",
            accept_new_options=True,
            key="nova_receita_nome"
        )

        valor = st.number_input(
            "Valor",
            min_value=0.00,
            step=0.01,
            format="%.2f",
            key="nova_receita_valor"
        )

        mensal = st.selectbox(
            "Mensal",
            ["Sim", "Não"],
            key="nova_receita_mensal"
        )

        if st.button(
            "Salvar Nova Receita",
            key="salvar_nova_receita"
        ):

            # Validação: todos os campos obrigatórios (Valor pode ser 0)
            if not nome_cobranca or not str(nome_cobranca).strip():
                st.error("Informe o Nome da Cobrança.")

            elif not parceiro_selecionado or not cnpj:
                st.error("Parceiro sem CNPJ cadastrado. Ajuste o cadastro do parceiro antes.")

            else:
                conn = conectar()

                conn.execute(
                    """
                    INSERT INTO receitas
                    (
                        parceiro,
                        cnpj,
                        nome_cobranca,
                        valor,
                        mensal
                    )
                    VALUES (?,?,?,?,?)
                    """,
                    (
                        parceiro_selecionado,
                        cnpj,
                        nome_cobranca.upper().strip(),
                        valor,
                        1 if mensal == "Sim" else 0
                    )
                )

                conn.commit()
                conn.close()

                st.cache_data.clear()
                st.success("Receita cadastrada.")

                st.rerun()



# ==========================
# FULL SERVICE
# ==========================
if menu == "Full Service":
    st.subheader("Full Service")


    #Carrega os dados
    try:
        df_fs = carregar_full_service()
    except PermissionError:
        st.warning("⚠️ Um usuário está atualizando ou utilizando o arquivo base. Aguarde e tente novamente.")
        st.stop()
    except Exception:
        st.warning("⚠️ Não foi possível acessar o arquivo base neste momento.")
        st.stop()

    # DATAS
    df_fs["Data Histórico"] = pd.to_datetime(
        df_fs["Data Histórico"],
        dayfirst=True,
        errors="coerce")
    df_fs["Data Entrega"] = pd.to_datetime(
        df_fs["Data Entrega"],
        dayfirst=True,
        errors="coerce")

    # =====================================
    # FILTROS
    # =====================================

    meses = sorted(
        df_fs["Data Histórico"]
        .dt.to_period("M")
        .astype(str)
        .dropna()
        .unique(),
        reverse=True
    )

    mes_atual = pd.Timestamp.today().strftime("%Y-%m")
    
    sidebar = st.sidebar.container()
    with sidebar:

        st.header("Filtros Full Service")

        parceiro_filtro = st.selectbox(
            "Parceiro",
            ["Todos"]
            +
            sorted(
                df_fs["Parceiro"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        )

        mes_selecionado = st.selectbox(
            "Mês Histórico",
            meses,
            index=meses.index(mes_atual)
            if mes_atual in meses
            else 0
        )


    # =====================================
    # FILTRO MÊS
    # =====================================

    resultado = df_fs[
        df_fs["Data Histórico"]
        .dt.to_period("M")
        .astype(str)
        == mes_selecionado
    ].copy()

    # =====================================
    # FILTRO PARCEIRO
    # =====================================

    if parceiro_filtro != "Todos":

        resultado = resultado[
            resultado["Parceiro"]
            == parceiro_filtro
        ]

    # =====================================
    # REMOVE DUPLICIDADE
    # =====================================

    resultado = resultado.sort_values(
        "Data Entrega",
        ascending=False
    )

    resultado = resultado.drop_duplicates(
        subset=[
            "Terminal",
            "Parceiro"
        ],
        keep="first"
    )

    # =====================================
    # BUSCA VALOR FULL SERVICE
    # =====================================

    df_parceiros = carregar_dados()
    df_receitas = carregar_receitas()
    df_tpv = carregar_tpv()

    ano_mes = mes_selecionado.replace("-", "")

    df_tpv = df_tpv[
        df_tpv["ANO_MES"]
        .astype(str)
        .eq(ano_mes)
    ].copy()


    df_receitas = df_receitas[
        df_receitas["nome_cobranca"]
        .astype(str)
        .str.upper()
        .eq("FULL SERVICE")
    ].copy()

    mapa_parceiros = df_parceiros[
        [
            "PARCEIRO",
            "NOME FANTASIA"
        ]
    ].copy()

    resultado = resultado.merge(
        mapa_parceiros,
        left_on="Parceiro",
        right_on="NOME FANTASIA",
        how="left"
    )

    resultado = resultado.merge(
        df_receitas[
            [
                "parceiro",
                "valor"
            ]
        ],
        left_on="PARCEIRO",
        right_on="parceiro",
        how="left"
    )

    resultado = resultado.rename(
        columns={
            "valor": "Valor Full Service"
        }
    )



    # =====================================
    # BUSCA TPV
    # =====================================

    ano_mes = mes_selecionado.replace("-", "")

    df_tpv["Terminal"] = (
        df_tpv["Terminal"]
        .astype(str)
        .str.strip()
    )

    df_tpv["Parceiro"] = (
        df_tpv["Parceiro"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df_tpv["ANO_MES"] = (
        df_tpv["ANO_MES"]
        .astype(str)
        .str.strip()
    )

    resultado["Terminal"] = (
        resultado["Terminal"]
        .astype(str)
        .str.strip()
    )

    resultado["Parceiro"] = (
        resultado["Parceiro"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    resultado = resultado.merge(
        df_tpv[
            [
                "Terminal",
                "Parceiro",
                "TPV"
            ]
        ],
        on=[
            "Terminal",
            "Parceiro"
        ],
        how="left"
    )


    # =====================================
    # INDICADORES
    # =====================================

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Terminais",
            len(resultado)
        )

    with col2:

        st.metric(
            "Parceiros",
            resultado["Parceiro"].nunique()
        )

    with col3:

        st.metric(
            "Receita Total",
            formatar_brl(resultado['Valor Full Service'].fillna(0).sum(), 2)
        )

    # =====================================
    # FORMATAÇÕES
    # =====================================

    resultado["Data Entrega"] = (
        resultado["Data Entrega"]
        .dt.strftime("%d/%m/%Y")
    )

    resultado["Valor Full Service"] = (
        resultado["Valor Full Service"]
        .apply(
            lambda x:
            formatar_brl(x, 2)
            if pd.notnull(x)
            else ""
        )
    )

    resultado["TPV"] = (
        pd.to_numeric(
            resultado["TPV"],
            errors="coerce"
        )
    )

    resultado["TPV"] = (
        resultado["TPV"]
        .apply(
            lambda x:
            formatar_brl(x, 2)
            if pd.notnull(x)
            else ""
        )
)


    # =====================================
    # COLUNAS FINAIS
    # =====================================

    resultado = resultado[
        [
            "Terminal",
            "Modelo",
            "Parceiro",
            "TIPO_ATIVO",
            "Data Entrega",
            "Valor Full Service",
            "TPV"
        ]
    ]

    resultado = resultado.rename(
        columns={
            "TIPO_ATIVO": "Tipo Ativo"
        }
    )

    # =====================================
    # TABELA
    # =====================================

    st.dataframe(
        resultado,
        width="stretch",
        hide_index=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            "Exportar Excel",
            gerar_excel(resultado),
            file_name=f"Full Service {mes_selecionado}.xlsx",
        )




# ==========================
# FECHAMENTO
# ==========================
if menu == "Fechamento":


    st.subheader("Fechamento")


    # =====================================
    # LEITURA
    # =====================================

    resultado = carregar_fechamento_no_dw()


    # =====================================
    # FILTROS
    # =====================================

    sidebar = st.sidebar.container()
    with sidebar:

        st.header("Filtros Fechamento")
        parceiro_filtro = st.selectbox(
            "Razão Social",
            ["Todos"] +
            sorted(
                resultado["Razao Social"]
                .fillna("Sem Parceiro")
                .astype(str)
                .unique()
                .tolist()))



        resultado["DT Emissao"] = pd.to_datetime(
            resultado["DT Emissao"],
            errors="coerce")
        meses_emissao = sorted(
            resultado["DT Emissao"]
            .dt.to_period("M")
            .dropna()
            .astype(str)
            .unique()
            .tolist(),
            reverse=True)
        mes_emissao_filtro = st.selectbox(
            "Mês/Ano Emissão",
            ["Todos"] + meses_emissao)



        resultado["DT Baixa"] = pd.to_datetime(
            resultado["DT Baixa"],
            errors="coerce")
        meses_baixa = sorted(
            resultado["DT Baixa"]
            .dt.to_period("M")
            .dropna()
            .astype(str)
            .unique()
            .tolist(),
            reverse=True)
        mes_baixa_filtro = st.selectbox(
            "Mês/Ano Baixa",
            ["Todos", "Não Pago"] + meses_baixa)



        produto_filtro = st.selectbox(
            "Produto",
            ["Todos"] +
            sorted(
                resultado["Prefixo"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()))



        tipo_filtro = st.selectbox(
            "Tipo",
            ["Todos"] +
            sorted(
                resultado["Tipo"]
                .fillna("Sem Tipo")
                .astype(str)
                .unique()
                .tolist()))

        motivo_filtro = st.selectbox(
            "Motivo",
            ["Todos"] +
            sorted(
                resultado["Motivo"]
                .fillna("Sem Motivo")
                .astype(str)
                .unique()
                .tolist()))

    # =====================================
    # APLICA FILTROS
    # =====================================

    if parceiro_filtro != "Todos":
        if parceiro_filtro == "Sem Parceiro":
            resultado = resultado[resultado["Razao Social"].isna()]
        else:
            resultado = resultado[resultado["Razao Social"].astype(str).str.strip()== parceiro_filtro]

    if mes_emissao_filtro != "Todos":

        resultado = resultado[
            resultado["DT Emissao"]
            .dt.to_period("M")
            .astype(str)
            == mes_emissao_filtro
        ]

    if mes_baixa_filtro == "Não Pago":

        resultado = resultado[
            resultado["DT Baixa"].isna()
        ]

    elif mes_baixa_filtro != "Todos":

        resultado = resultado[
            resultado["DT Baixa"]
            .dt.to_period("M")
            .astype(str)
            == mes_baixa_filtro
        ]

    if produto_filtro != "Todos":

        resultado = resultado[
            resultado["Prefixo"]
            .astype(str)
            .str.strip()
            == produto_filtro
        ]



    if tipo_filtro != "Todos":
        if tipo_filtro == "Sem Tipo":
            resultado = resultado[resultado["Tipo"].isna()]
        else:
            resultado = resultado[resultado["Tipo"].astype(str).str.strip()== tipo_filtro]
    
    if motivo_filtro != "Todos":
        if motivo_filtro == "Sem Motivo":
            resultado = resultado[resultado["Motivo"].isna()]
        else:
            resultado = resultado[resultado["Motivo"].astype(str).str.strip()== motivo_filtro]

    # =====================================
    # INDICADORES
    # =====================================
    
    titulos_pagos = resultado.loc[
        resultado["DT Baixa"].notna(),
        "Vlr.Titulo"
    ].fillna(0).sum()

    nao_recebido = resultado.loc[
        resultado["DT Baixa"].isna(),
        "Vlr.Titulo"
    ].fillna(0).sum()

    carteira_total = (
        resultado["Vlr.Titulo"]
        .fillna(0)
        .sum())

    # =====================================
    # EFETIVIDADE
    # =====================================

    efetividade_df = resultado.copy()

    efetividade_df = efetividade_df[
        efetividade_df["DT Emissao"].notna()]

    efetividade_df["Mes_Emissao"] = (
        efetividade_df["DT Emissao"]
        .dt.to_period("M"))

    efetividade_df["Mes_Baixa"] = (
        efetividade_df["DT Baixa"]
        .dt.to_period("M"))

    valor_efetivo = (
        efetividade_df[
            efetividade_df["Mes_Emissao"]
            ==
            efetividade_df["Mes_Baixa"]
        ]["Vlr.Titulo"]
        .fillna(0)
        .sum())

    efetividade = (
        valor_efetivo
        /
        carteira_total
        * 100) if carteira_total > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Quantidade de Títulos",
            len(resultado))

    with col2:
        st.metric(
            "Carteira Total",
            formatar_brl(carteira_total, 0))

    with col3:
        st.metric(
            "Títulos Pagos",
            formatar_brl(titulos_pagos, 0))

    with col4:
        st.metric(
            "Não Recebido",
            formatar_brl(nao_recebido, 0))

    with col5:
        st.metric(
            "Efetividade",
            f"{efetividade:.1f}%")


    # =====================================
    # RESUMO POR PARCEIRO
    # =====================================

    resumo = resultado.copy()

    resumo["Pago"] = resumo.apply(
        lambda x:
        x["Vlr.Titulo"]
        if pd.notnull(x["DT Baixa"])
        else 0,
        axis=1)

    resumo["Nao Recebido"] = resumo.apply(
        lambda x:
        x["Vlr.Titulo"]
        if pd.isnull(x["DT Baixa"])
        else 0,
        axis=1)

    resumo = (
        resumo
        .groupby("Razao Social")
        .agg(
            Valor_Total=("Vlr.Titulo", "sum"),
            Titulos_Pagos=("Pago", "sum"),
            Nao_Recebido=("Nao Recebido", "sum"))
        .reset_index())

    resumo["Resultado"] = (
        resumo["Titulos_Pagos"]
        - resumo["Valor_Total"])

    resumo["Situação"] = resumo["Resultado"].apply(
        lambda x:
        "Pagou a Mais"
        if x > 0
        else (
            "Quitado"
            if x == 0
            else "Em aberto"))

    for coluna in [
        "Valor_Total",
        "Titulos_Pagos",
        "Nao_Recebido",
        "Resultado"]:

        resumo[coluna] = resumo[coluna].apply(
            lambda x:
            formatar_brl(x, 0))

    resumo = resumo.rename(
        columns={
            "Razao Social": "Parceiro",
            "Valor_Total": "Valor Total",
            "Titulos_Pagos": "Títulos Pagos",
            "Nao_Recebido": "Não Recebido"})

    st.subheader("Resumo por Parceiro")

    st.dataframe(
        resumo,
        width="stretch",
        hide_index=True)

    st.divider()

    st.subheader("Detalhamento")
    # =====================================
    # FORMATAÇÕES
    # =====================================


    for coluna in [
        "DT Emissao",
        "DT Baixa"]:

        if coluna in resultado.columns:

            resultado[coluna] = pd.to_datetime(
                resultado[coluna],
                errors="coerce"
            ).dt.strftime("%d/%m/%Y")

    if "CNPJ/CPJ" in resultado.columns:

        resultado["CNPJ/CPJ"] = (
            resultado["CNPJ/CPJ"]
            .fillna("")
            .astype(str)
            .str.zfill(14)
            .str.replace(
                r"(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})",
                r"\1.\2.\3/\4-\5",
                regex=True))

    # =====================================
    # GRID
    # =====================================

    gb = GridOptionsBuilder.from_dataframe(resultado)

    gb.configure_column(
        "Vlr.Titulo",
        type=["numericColumn"],
        valueFormatter="""
        x.toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        })
        """)

    gb.configure_column(
        "Saldo",
        type=["numericColumn"],
        valueFormatter="""
        x.toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        })
        """)

    gb.configure_column(
        "Vlr.Liq Baix",
        type=["numericColumn"],
        valueFormatter="""
        x.toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        })
        """)

    gb.configure_default_column(
        editable=False,
        sortable=True,
        filter=True,
       sizable=True)

    # Datas vêm do DW: somente leitura (edição não era salva)
    gb.configure_column(
        "DT Emissao",
        editable=False)

    gb.configure_column(
        "DT Baixa",
        editable=False)

    resultado["DT Emissao"] = (
        resultado["DT Emissao"]
        .astype(str)
        .str[:10])

    resultado["DT Baixa"] = (
        resultado["DT Baixa"]
        .astype(str)
        .str[:10])

    gb.configure_grid_options(
        suppressRowClickSelection=True,
        suppressCellFocus=True
    )

    grid = AgGrid(
        resultado,
        gridOptions=gb.build(),
        update_on=["cellValueChanged"],
        height=500,
        fit_columns_on_grid_load=False)

    # =====================================
    # BOTÕES
    # =====================================

    col1, col2 = st.columns(2)

    with col1:

        if st.button("Atualizar dados"):
            st.cache_data.clear()
            st.rerun()

    with col2:

        st.download_button(
            "Exportar Excel",
            gerar_excel(resultado),
            file_name="fra.xlsx"
        )
    #with st.expander("📤 Importar Fechamento"):
#
#        arquivo = st.file_uploader(
#            "Selecione o arquivo Excel",
#            type=["xlsx"]
#        )

        #if arquivo is not None:

         #   if st.button("Importar Dados"):
 #               try:
 #                   df_import = pd.read_excel(arquivo)

    #                conn = conectar()
     #               df_import = df_import.reindex(
      #                  columns=["Prefixo","No. Titulo","Tipo","Razao Social","DT Emissao","DT Baixa","Vlr.Titulo","Saldo","Vlr.Liq Baix","Parcela","Motivo"])
#                    df_import.to_sql("FRA",conn,if_exists="replace",index=False)

                   # conn.close()

                    #st.cache_data.clear()

                    #st.success(f"{len(df_import)} registros importados.")

#                    st.rerun()

 #               except Exception as e:
#                    st.error(f"Erro: {e}")
# ==========================
# FOOTER
# ==========================
st.markdown("""
<style>
.footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: #000510;
    border-top: 1px solid #1E5AA8;
    padding: 1px 15px;
    z-index: 999999;}
.footer-content {
    display: flex;
    justify-content: space-between;
    align-items: center;}
.footer-text {
    color: #8892B0;
    font-size: 12px;}
.footer-link {
    color: #7DB7E8 !important;
    text-decoration: none !important;
    font-size: 16px;
    font-weight: bold;}
.footer-link:hover {color: white !important;}
</style>
<div class="footer">
    Criado por Dylan Richards
    <a class="footer-link"
        href="http://192.168.16.65:10"
        target="_self">
        🔗 Ver outros sistemas
    </a>
""", unsafe_allow_html=True)