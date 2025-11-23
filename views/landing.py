import streamlit as st
from services import auth

def render_landing_page():
    # CSS para centralizar e deixar bonito
    st.markdown("""
    <style>
        .main-header {text-align: center; font-size: 3rem; font-weight: bold; margin-bottom: 0;}
        .sub-header {text-align: center; font-size: 1.5rem; color: #666; margin-bottom: 2rem;}
        .feature-card {padding: 1.5rem; border-radius: 10px; background-color: #f0f2f6; text-align: center; height: 100%;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 class='main-header'>🚀 Estúdio Criativo IA</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Do Rascunho à Realidade: Valide suas ideias com Agentes Autônomos</p>", unsafe_allow_html=True)

    st.divider()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class='feature-card'>
            <h3>📖 Histórias</h3>
            <p>Escreva livros com um Arquiteto de Mundos e um Editor Crítico.</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class='feature-card'>
            <h3>💻 Startups</h3>
            <p>Valide seu SaaS com um CFO, um Gerente de Produto e um Hater.</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class='feature-card'>
            <h3>🏗️ Empreendimentos</h3>
            <p>Analise viabilidade de obras com Incorporadores e Engenheiros.</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Área de Login Centralizada
    col_login1, col_login2, col_login3 = st.columns([1, 2, 1])
    with col_login2:
        st.write("### Comece agora")
        if st.button("Entrar com Google (Simulado)", type="primary", use_container_width=True):
            auth.login_simulado()
        
        with st.expander("Termos de Uso e Privacidade"):
            st.caption("""
            1. Seus dados (ideias) são armazenados no Firebase de forma privada.
            2. A IA (Gemini) processa os dados para gerar relatórios, mas não os retém para treinamento (conforme API Enterprise).
            3. Este é um projeto MVP em fase de testes.
            """)
