# Ponto de entrada do sistema: streamlit run app.py
import streamlit as st

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
# PÁGINAS
# ==========================

paginas = [
    st.Page("pages/home.py", title="Home", default=True),
    st.Page("pages/parceiros.py", title="Tabela de Parceiros"),
    st.Page("pages/receitas.py", title="Tabela de Receitas"),
    st.Page("pages/full_service.py", title="Full Service"),
    st.Page("pages/fechamento.py", title="Fechamento"),
]

# Menu padrão do Streamlit escondido: o menu é desenhado abaixo, na mesma posição de antes
pg = st.navigation(paginas, position="hidden")

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

for pagina in paginas:
    st.sidebar.page_link(pagina)

pg.run()

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
