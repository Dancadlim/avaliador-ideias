import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

st.set_page_config(page_title="Avaliador de Ideias", layout="wide")
st.title("🚀 Avaliador de Ideias - Teste de Conexão")

# --- Lógica de Conexão Blindada ---
try:
    if "firebase" in st.secrets:
        # Lógica inteligente:
        # Se for o formato antigo (JSON string), converte.
        # Se for o formato novo (TOML nativo), usa direto.
        if "text_key" in st.secrets["firebase"]:
            key_dict = json.loads(st.secrets["firebase"]["text_key"])
        else:
            # Transforma o objeto de segredos do Streamlit em um dicionário Python padrão
            key_dict = dict(st.secrets["firebase"])

        # Cria a credencial
        creds = credentials.Certificate(key_dict)

        # Inicializa o app (evita erro se já estiver rodando)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(creds)

        st.success("✅ Conexão com o Banco de Dados: SUCESSO!")
        st.info(f"Projeto ID: {key_dict.get('project_id')}")
        
        # Teste real de leitura do banco
        db = firestore.client()
        docs = db.collection("test_connection").stream()
        st.write("Teste de leitura do banco: OK")

    else:
        st.warning("⚠️ Chave 'firebase' não encontrada nos Secrets.")

except Exception as e:
    st.error(f"❌ Erro na conexão: {e}")
    st.code(str(e)) # Mostra o erro técnico se houver
