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

# --- ESTADO DA SESSÃO ---
if "user" not in st.session_state:
    st.session_state.user = None
if "active_project" not in st.session_state:
    st.session_state.active_project = None  # Guarda o ID do projeto aberto

# --- FUNÇÕES AUXILIARES ---
def login():
    st.session_state.user = {"email": "usuario_teste@gmail.com", "name": "Chefe"}
    st.rerun()

def logout():
    st.session_state.user = None
    st.session_state.active_project = None
    st.rerun()

def abrir_projeto(projeto_dict, projeto_id):
    st.session_state.active_project = {**projeto_dict, "id": projeto_id}
    st.rerun()

def fechar_projeto():
    st.session_state.active_project = None
    st.rerun()

def criar_nova_ideia(titulo, descricao, categoria):
    doc_ref = db.collection("ideas").document()
    doc_ref.set({
        "user_email": st.session_state.user["email"],
        "title": titulo,
        "description": descricao,
        "category": categoria,
        "status": "rascunho",
        "created_at": datetime.datetime.now(),
        # Novos campos preparados para o futuro:
        "macro_context": {}, 
        "micro_contents": [],
        "parent_id": None 
    })
    st.toast(f"Ideia '{titulo}' criada!", icon="✅")
    st.rerun()

# --- DIALOG NOVA IDEIA ---
@st.dialog("💡 Nova Ideia")
def dialog_nova_ideia(categoria_atual):
    st.write(f"Adicionar em: **{categoria_atual.capitalize()}**")
    titulo = st.text_input("Nome Provisório")
    descricao = st.text_area("Descrição Rápida")
    if st.button("Criar Projeto"):
        if titulo:
            criar_nova_ideia(titulo, descricao, categoria_atual)
        else:
            st.warning("Título obrigatório.")

# ==================================================
# 🖥️ UI - INTERFACE DO USUÁRIO
# ==================================================

if not st.session_state.user:
    # --- TELA DE LOGIN ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Estúdio Criativo")
        if st.button("Entrar (Simulado)", type="primary", use_container_width=True):
            login()
else:
    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🚀 Menu")
        
        # Se tiver projeto aberto, mostra botão de voltar
        if st.session_state.active_project:
            if st.button("⬅️ Voltar para Lista"):
                fechar_projeto()
            st.divider()
            st.info(f"Editando: **{st.session_state.active_project['title']}**")
        else:
            # Navegação padrão
            st.write(f"Olá, **{st.session_state.user['name']}**")
            page = st.radio("Ir para:", ["🏠 Home", "🏗️ Empreendimentos", "💻 Projetos Digitais", "📖 Histórias"])
            st.divider()
            if st.button("Sair"):
                logout()

    # --- LÓGICA DE NAVEGAÇÃO PRINCIPAL ---
    
    # CENÁRIO A: NENHUM PROJETO ABERTO (MOSTRAR LISTAS)
    if not st.session_state.active_project:
        
        if page == "🏠 Home":
            st.title("Bem-vindo ao Estúdio")
            st.markdown("Selecione uma categoria no menu lateral.")
            
        else:
            # Mapeamento de categorias
            cat_map = {
                "🏗️ Empreendimentos": "empreendimento",
                "💻 Projetos Digitais": "projeto",
                "📖 Histórias": "historia"
            }
            categoria_tecnica = cat_map.get(page, "projeto")

            # Cabeçalho da Categoria
            c1, c2 = st.columns([3, 1])
            c1.title(page)
            if c2.button("➕ Nova Ideia", type="primary"):
                dialog_nova_ideia(categoria_tecnica)
            
            # Busca no Firebase
            docs = db.collection("ideas")\
                .where("user_email", "==", st.session_state.user["email"])\
                .where("category", "==", categoria_tecnica)\
                .stream()
            
            # Renderiza Cartões
            ideias = list(docs)
            if not ideias:
                st.info("Nenhum projeto aqui ainda.")
            
            for doc in ideias:
                data = doc.to_dict()
                with st.container(border=True):
                    col_a, col_b, col_c = st.columns([4, 2, 2])
                    col_a.subheader(data['title'])
                    col_a.caption(data.get('description', ''))
                    col_b.write(f"Status: **{data.get('status', 'Rascunho')}**")
                    
                    # O GRANDE TRUQUE: Botão que abre o projeto
                    if col_c.button("Abrir Sala de Guerra ⚔️", key=doc.id):
                        abrir_projeto(data, doc.id)

    # CENÁRIO B: PROJETO ABERTO (MOSTRAR DETALHES/WORKSPACE)
    else:
        proj = st.session_state.active_project
        st.title(f"📂 {proj['title']}")
        st.caption(f"Categoria: {proj['category']} | Status: {proj.get('status', 'Rascunho')}")
        
        # --- AQUI ENTRA A SUA IDEIA DAS ABAS INTERNAS ---
        
        # 1. Se for HISTÓRIA, mostra Macro/Micro
        if proj['category'] == 'historia':
            tab_macro, tab_micro, tab_derivados = st.tabs(["🌍 Universo (Macro)", "✍️ Manuscrito (Micro)", "📚 Derivações"])
            
            with tab_macro:
                st.header("Bíblia da História")
                st.markdown("*Aqui você define regras de magia, fichas de personagens e plot geral.*")
                st.text_area("Resumo do Universo", height=200, placeholder="Escreva sobre o mundo...")
                st.button("Validar Universo (CrewAI)", key="btn_macro")

            with tab_micro:
                st.header("Capítulos e Cenas")
                st.markdown("*Aqui é a escrita passo a passo.*")
                st.text_area("Escreva o capítulo atual...", height=300)
                st.button("Validar Capítulo (CrewAI)", key="btn_micro")
                
            with tab_derivados:
                st.info("Funcionalidade futura: Criar continuação ou Spin-off.")

        # 2. Se for PROJETO ou EMPREENDIMENTO (Ciclo Infinito)
        else:
            tab_geral, tab_validacao = st.tabs(["💡 Desenvolvimento", "✅ Validação Técnica"])
            
            with tab_geral:
                st.subheader("Evolução do Projeto")
                st.markdown("*Ciclo de melhoria contínua (Versão 1.0 -> 1.1)*")
                st.text_area("Notas de evolução", height=200)
                
                # Botão de Finalizar/Reabrir
                if proj.get('status') == 'concluido':
                    st.button("🔄 Reabrir para V2.0 (Melhoria)")
                else:
                    st.button("🏁 Marcar como Concluído (V1.0)")
            
            with tab_validacao:
                st.write("Área para relatórios técnicos de viabilidade e riscos.")
                st.button("Chamar Especialistas (CrewAI)", key="btn_proj")
