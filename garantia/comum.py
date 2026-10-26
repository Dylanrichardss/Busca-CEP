# Funções e cargas de dados compartilhadas por todas as páginas
import sqlite3
import pandas as pd
import streamlit as st
import mysql.connector

from io import BytesIO

import warnings
warnings.filterwarnings("ignore",message="pandas only supports SQLAlchemy")

DB = "garantia_receita.db"

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
        host="",       # servidor
        user="",         # usuário
        password="",       # senha
        database=""    # banco de dados
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
