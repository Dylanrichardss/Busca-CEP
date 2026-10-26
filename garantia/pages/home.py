# Página: Home
import pandas as pd
import streamlit as st

from comum import (
    formatar_brl,
    carregar_dados,
    carregar_receitas,
    carregar_full_service,
    carregar_fechamento_no_dw,
)


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
