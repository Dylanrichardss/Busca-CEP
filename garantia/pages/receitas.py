# Página: Tabela de Receitas
import pandas as pd
import streamlit as st

from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode
)

from comum import (
    formatar_brl,
    formatar_cnpj,
    gerar_excel,
    conectar,
    carregar_dados,
    carregar_receitas,
)


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
