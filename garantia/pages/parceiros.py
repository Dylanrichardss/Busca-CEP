# Página: Tabela de Parceiros
import pandas as pd
import streamlit as st

from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode
)

from comum import (
    limpar_cnpj,
    formatar_cnpj,
    gerar_excel,
    conectar,
    carregar_dados,
    atualizar_linha,
)

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
