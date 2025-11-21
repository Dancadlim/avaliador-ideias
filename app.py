import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import json

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Avaliador de Ideias", page_icon="🚀", layout="wide")

# --- CONEXÃO COM FIREBASE (BLINDADA) ---
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
        st.error(f"Erro de conexão: {e}")
        st.stop()

db = firestore.client()

# --- ESTADO DA SESSÃO (MEMÓRIA TEMPORÁRIA) ---
# Isso mantem o usuário logado e sabe em qual aba ele está
if "user" not in st.session_state:
    st.session_state.user = None
if "current_view" not in st.session_state:
    st.session_state.current_view = "home"

# --- FUNÇÕES AUXILIARES ---
def login():
    # Simulação de Login para o MVP (Depois colocamos Google Auth real se precisar)
    st.session_state.user = {"email": "usuario_teste@gmail.com", "name": "Chefe"}
    st.rerun()

def logout():
    st.session_state.user = None
    st.rerun()

def criar_nova_ideia(titulo, descricao, categoria):
    # Salva no Firebase
    doc_ref = db.collection("ideas").document()
    doc_ref.set({
        "user_email": st.session_state.user["email"],
        "title": titulo,
        "description": descricao,
        "category": categoria,
        "status": "rascunho",
        "created_at": datetime.datetime.now(),
        "updated_at": datetime.datetime.now(),
        "chat_history": [],
        "summary": ""
    })
    st.toast(f"Ideia '{titulo}' criada com sucesso!", icon="✅")
    st.rerun()

# --- DIALOG (JANELA MODAL) PARA NOVA IDEIA ---
@st.dialog("💡 Nova Ideia")
def dialog_nova_ideia(categoria_atual):
    st.write(f"Adicionar novo projeto em: **{categoria_atual.capitalize()}**")
    titulo = st.text_input("Nome Provisório")
    descricao = st.text_area("Descrição Rápida")
    
    if st.button("Criar Projeto"):
        if titulo:
            criar_nova_ideia(titulo, descricao, categoria_atual)
        else:
            st.warning("O título é obrigatório.")

# ==================================================
# 🖥️ INTERFACE DO USUÁRIO (UI)
# ==================================================

# --- 1. TELA DE LOGIN ---
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Acesso ao Estúdio Criativo")
        st.write("Faça login para acessar seu cofre de ideias.")
        
        # Botão simples para entrar agora (mapeado para seu email)
        if st.button("Entrar com Google (Simulado)", type="primary", use_container_width=True):
            login()
            
        st.info("ℹ️ Neste MVP, o login é automático para testes.")

# --- 2. TELA PRINCIPAL (DASHBOARD) ---
else:
    # --- SIDEBAR (NAVEGAÇÃO) ---
    with st.sidebar:
        st.title("🚀 Menu")
        st.write(f"Olá, **{st.session_state.user['name']}**")
        
        # Navegação
        page = st.radio(
            "Ir para:",
            ["🏠 Home", "🏗️ Empreendimentos", "💻 Projetos Digitais", "📖 Histórias & Livros"]
        )
        
        st.divider()
        if st.button("Sair"):
            logout()

    # --- CONTEÚDO DAS PÁGINAS ---
    
    # A. PÁGINA HOME
    if page == "🏠 Home":
        st.title("Bem-vindo ao seu Estúdio de Ideias")
        st.markdown("""
        Aqui você pode gerenciar, validar e refinar seus projetos usando Inteligência Artificial.
        Selecione uma categoria no menu lateral para começar.
        """)
        
        # Métricas Rápidas (Busca no banco)
        # (Futuramente faremos queries reais aqui)
        c1, c2, c3 = st.columns(3)
        c1.metric("Empreendimentos", "0")
        c2.metric("Projetos Digitais", "0")
        c3.metric("Histórias", "0")

    # B. PÁGINAS DE CATEGORIA (A Lógica é a mesma para as 3)
    else:
        # Define a categoria técnica baseada no nome do menu
        cat_map = {
            "🏗️ Empreendimentos": "empreendimento",
            "💻 Projetos Digitais": "projeto",
            "📖 Histórias & Livros": "historia"
        }
        categoria_tecnica = cat_map[page]
        
        # Cabeçalho
        c_top1, c_top2 = st.columns([3, 1])
        with c_top1:
            st.title(page)
        with c_top2:
            if st.button("➕ Nova Ideia", type="primary"):
                dialog_nova_ideia(categoria_tecnica)
        
        # Barra de Pesquisa
        busca = st.text_input(f"Buscar em {page}...", placeholder="Digite o nome do projeto...")
        
        st.divider()
        
        # --- LISTAGEM DE IDEIAS (CONECTADO AO FIREBASE) ---
        # Busca apenas ideias do usuário atual e da categoria atual
        docs = db.collection("ideas")\
            .where("user_email", "==", st.session_state.user["email"])\
            .where("category", "==", categoria_tecnica)\
            .stream()
            
        lista_ideias = list(docs)
        
        if not lista_ideias:
            st.info("Nenhuma ideia encontrada nesta categoria. Crie a primeira acima! 👆")
        
        # Renderiza os cartões
        for doc in lista_ideias:
            data = doc.to_dict()
            
            # Filtro de busca visual
            if busca and busca.lower() not in data['title'].lower():
                continue
                
            # Design do Cartão
            with st.container(border=True):
                c1, c2, c3 = st.columns([4, 2, 2])
                with c1:
                    st.subheader(data['title'])
                    st.caption(data.get('description', 'Sem descrição'))
                with c2:
                    st.write(f"**Status:** {data.get('status', 'Rascunho')}")
                    st.caption(f"Criado em: {data.get('created_at', datetime.datetime.now()).strftime('%d/%m/%Y')}")
                with c3:
                    if st.button("Abrir Chat 💬", key=f"btn_{doc.id}"):
                        st.toast("Funcionalidade de chat será implementada na próxima etapa!")
