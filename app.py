import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

st.set_page_config(page_title="Avaliador de Ideias", layout="wide")
st.title("🚀 Avaliador de Ideias - Teste de Conexão")

# Tentar ler a senha do cofre (Secrets)
try:
    # Verifica se a chave existe nos segredos
    if "firebase" in st.secrets:
        key_dict = json.loads(st.secrets["firebase"]["text_key"])
        
        # Cria a credencial
        creds = credentials.Certificate(key_dict)

        # Conecta no Firebase (evita erro de re-inicialização)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(creds)

        st.success("✅ Conexão com o Banco de Dados: SUCESSO!")
        st.info(f"Projeto ID: {key_dict.get('project_id')}")
    else:
        st.warning("⚠️ Chave não encontrada. Configure os Secrets no Streamlit.")

except Exception as e:
    st.error(f"❌ Erro na conexão: {e}")
