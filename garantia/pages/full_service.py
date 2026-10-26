# Página: Full Service
import pandas as pd
import streamlit as st

from comum import (
    formatar_brl,
    gerar_excel,
    carregar_dados,
    carregar_receitas,
    carregar_full_service,
    carregar_tpv,
)

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
