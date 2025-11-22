import streamlit as st
from services import auth
from views import dashboard, workspace

# --- CONFIGURAÇÃO GERAL ---
st.set_page_config(page_title="Avaliador de Ideias", page_icon="🚀", layout="wide")

# --- INICIALIZAÇÃO DA SESSÃO ---
if "user" not in st.session_state:
    st.session_state.user = None
if "active_project" not in st.session_state:
    st.session_state.active_project = None

# --- ROTEAMENTO (ROUTER) ---
# Decide qual tela mostrar

# 1. Se não tiver usuário -> Tela de Login
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Estúdio Criativo")
        st.write("Faça login para acessar seu cofre.")
        if st.button("Entrar (Simulado)", type="primary", use_container_width=True):
            auth.login_simulado()

# 2. Se tiver usuário...
else:
    # A. Se tiver projeto ativo -> Mostra Workspace (Sala de Guerra)
    if st.session_state.active_project:
        workspace.render_workspace()
        
    # B. Se não tiver projeto ativo -> Mostra Dashboard (Listas)
    else:
        dashboard.render_dashboard()
