# Página: Fechamento
import pandas as pd
import streamlit as st

from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode
)

from comum import (
    formatar_brl,
    gerar_excel,
    conectar,
    carregar_fechamento_no_dw,
)



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
