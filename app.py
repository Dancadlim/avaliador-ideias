import streamlit as st
from services import auth
from views import dashboard, workspace, landing # <--- Importação Nova

# --- CONFIGURAÇÃO GERAL ---
st.set_page_config(page_title="Avaliador de Ideias", page_icon="🚀", layout="wide")

# --- INICIALIZAÇÃO DA SESSÃO ---
if "user" not in st.session_state: st.session_state.user = None
if "active_project" not in st.session_state: st.session_state.active_project = None

# --- ROTEAMENTO (ROUTER) ---

# 1. Se não tiver usuário -> LANDING PAGE
if not st.session_state.user:
    landing.render_landing_page()

# 2. Se tiver usuário...
else:
    # A. Se tiver projeto ativo -> WORKSPACE
    if st.session_state.active_project:
        workspace.render_workspace()
        
    # B. Se não tiver projeto ativo -> DASHBOARD
    else:
        dashboard.render_dashboard()
