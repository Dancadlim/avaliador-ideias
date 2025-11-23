import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import datetime

# --- CONEXÃO (Singleton) ---
def initialize_firebase():
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets:
                if "text_key" in st.secrets["firebase"]:
                    key_dict = json.loads(st.secrets["firebase"]["text_key"])
                else:
                    key_dict = dict(st.secrets["firebase"])
                
                creds = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(creds)
        except Exception as e:
            st.error(f"Erro de conexão com Firebase: {e}")
            st.stop()
    return firestore.client()

# Instância do banco para ser usada nos outros arquivos
db = initialize_firebase()

# --- FUNÇÕES DE ESCRITA/LEITURA ---

def criar_nova_ideia(user_email, titulo, descricao, categoria):
    doc_ref = db.collection("ideas").document()
    doc_ref.set({
        "user_email": user_email,
        "title": titulo,
        "description": descricao,
        "category": categoria,
        "status": "rascunho",
        "created_at": datetime.datetime.now(),
        "chat_history": [],
        "macro_context_text": "", 
        "macro_chat_history": [],
        "micro_chat_history": [],
        "micro_content_text": "",
        "reports_macro": [],
        "reports_micro": []
    })
    return True

def listar_ideias(user_email, categoria):
    return db.collection("ideas")\
        .where("user_email", "==", user_email)\
        .where("category", "==", categoria)\
        .stream()

def atualizar_campo(projeto_id, campo, valor):
    db.collection("ideas").document(projeto_id).update({campo: valor})

def salvar_relatorio(projeto_id, campo_array, relatorio_texto):
    texto_final = str(relatorio_texto)
    novo_relatorio = {
        "date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "content": texto_final
    }
    db.collection("ideas").document(projeto_id).update({
        campo_array: firestore.ArrayUnion([novo_relatorio])
    })
    return novo_relatorio

def salvar_chat_historico(projeto_id, campo_banco, historico_json):
    db.collection("ideas").document(projeto_id).update({
        campo_banco: historico_json
    })

def deletar_ideia(projeto_id):
    try:
        db.collection("ideas").document(projeto_id).delete()
        return True
    except Exception as e:
        st.error(f"Erro ao deletar: {e}")
        return False
