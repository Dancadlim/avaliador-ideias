import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Avaliador de Ideias", page_icon="🚀", layout="wide")

# --- 1. CONEXÃO COM FIREBASE (BLINDADA) ---
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

db = firestore.client()

# --- 2. CONFIGURAÇÃO DA IA (GEMINI) ---
try:
    if "google" in st.secrets:
        api_key = st.secrets["google"]["api_key"]
        # Modelo Flash é mais rápido e barato para chat
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
    else:
        st.warning("⚠️ Configure a chave [google] nos Secrets para ativar a IA.")
        llm = None
except Exception as e:
    st.error(f"Erro ao configurar IA: {e}")
    llm = None

# --- ESTADO DA SESSÃO ---
if "user" not in st.session_state:
    st.session_state.user = None
if "active_project" not in st.session_state:
    st.session_state.active_project = None

# --- FUNÇÕES AUXILIARES (BANCO E LOGICA) ---
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
        "chat_history": [], # Histórico começa vazio
        "macro_context": {},
        "micro_contents": []
    })
    st.toast(f"Ideia '{titulo}' criada!", icon="✅")
    st.rerun()

def atualizar_historico_firebase(projeto_id, novo_historico):
    # Converte mensagens do LangChain para formato JSON puro pro Firebase
    historico_json = []
    for msg in novo_historico:
        role = "user" if isinstance(msg, HumanMessage) else "ai"
        historico_json.append({"role": role, "content": msg.content})
    
    db.collection("ideas").document(projeto_id).update({
        "chat_history": historico_json
    })

# --- COMPONENTE DE CHAT (O CÉREBRO) ---
def renderizar_chat(projeto, contexto_extra=""):
    st.subheader("💬 Parceiro de Pensamento")
    
    # 1. Carregar histórico do Firebase (se existir)
    if "chat_memory" not in st.session_state:
        st.session_state.chat_memory = []
        if projeto.get("chat_history"):
            for msg in projeto["chat_history"]:
                if msg["role"] == "user":
                    st.session_state.chat_memory.append(HumanMessage(content=msg["content"]))
                else:
                    st.session_state.chat_memory.append(AIMessage(content=msg["content"]))

    # 2. Mostrar mensagens na tela
    for msg in st.session_state.chat_memory:
        role = "user" if isinstance(msg, HumanMessage) else "ai"
        avatar = "👤" if role == "user" else "🤖"
        with st.chat_message(role, avatar=avatar):
            st.write(msg.content)

    # 3. Campo de Input do Usuário
    if prompt := st.chat_input("Converse com o assistente sobre esta ideia..."):
        if not llm:
            st.error("IA não configurada.")
            return

        # A. Mostrar mensagem do usuário
        st.chat_message("user", avatar="👤").write(prompt)
        st.session_state.chat_memory.append(HumanMessage(content=prompt))

        # B. Gerar resposta da IA
        with st.chat_message("ai", avatar="🤖"):
            with st.spinner("Pensando..."):
                # Monta o prompt com contexto
                system_msg = f"""
                Você é um especialista em {projeto['category']}. 
                O projeto é: {projeto['title']}.
                Descrição: {projeto.get('description', '')}.
                Contexto Atual: {contexto_extra}
                Seja socrático, faça perguntas para ajudar a refinar a ideia, mas dê sugestões quando pedido.
                """
                
                messages = [HumanMessage(content=system_msg)] + st.session_state.chat_memory
                response = llm.invoke(messages)
                st.write(response.content)
        
        # C. Salvar resposta na memória
        st.session_state.chat_memory.append(AIMessage(content=response.content))
        
        # D. Persistir no Firebase (Salvar no Cofre)
        atualizar_historico_firebase(projeto["id"], st.session_state.chat_memory)


# ==================================================
# 🖥️ UI - INTERFACE DO USUÁRIO
# ==================================================

if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Estúdio Criativo")
        if st.button("Entrar (Simulado)", type="primary", use_container_width=True):
            login()
else:
    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🚀 Menu")
        if st.session_state.active_project:
            if st.button("⬅️ Voltar para Lista"):
                # Limpa memória do chat ao sair para não misturar projetos
                if "chat_memory" in st.session_state:
                    del st.session_state["chat_memory"]
                fechar_projeto()
            st.divider()
            st.info(f"Editando: **{st.session_state.active_project['title']}**")
        else:
            st.write(f"Olá, **{st.session_state.user['name']}**")
            page = st.radio("Ir para:", ["🏠 Home", "🏗️ Empreendimentos", "💻 Projetos Digitais", "📖 Histórias"])
            st.divider()
            if st.button("Sair"):
                logout()

    # --- NAVEGAÇÃO ---
    if not st.session_state.active_project:
        # (CÓDIGO DA LISTA MANTIDO IGUAL AO ANTERIOR)
        if page == "🏠 Home":
            st.title("Bem-vindo ao Estúdio")
            st.markdown("Selecione uma categoria no menu lateral.")
        else:
            cat_map = {"🏗️ Empreendimentos": "empreendimento", "💻 Projetos Digitais": "projeto", "📖 Histórias": "historia"}
            categoria_tecnica = cat_map.get(page, "projeto")

            c1, c2 = st.columns([3, 1])
            c1.title(page)
            
            # DIALOG DE CRIAÇÃO
            @st.dialog("💡 Nova Ideia")
            def dialog_nova_ideia(cat):
                titulo = st.text_input("Nome Provisório")
                descricao = st.text_area("Descrição Rápida")
                if st.button("Criar"):
                    if titulo: criar_nova_ideia(titulo, descricao, cat)
            
            if c2.button("➕ Nova Ideia", type="primary"):
                dialog_nova_ideia(categoria_tecnica)
            
            docs = db.collection("ideas").where("user_email", "==", st.session_state.user["email"]).where("category", "==", categoria_tecnica).stream()
            ideias = list(docs)
            if not ideias: st.info("Nenhum projeto aqui ainda.")
            
            for doc in ideias:
                data = doc.to_dict()
                with st.container(border=True):
                    col_a, col_b, col_c = st.columns([4, 2, 2])
                    col_a.subheader(data['title'])
                    col_a.caption(data.get('description', ''))
                    col_b.write(f"Status: **{data.get('status', 'Rascunho')}**")
                    if col_c.button("Abrir Sala de Guerra ⚔️", key=doc.id):
                        abrir_projeto(data, doc.id)

    # --- SALA DE GUERRA (COM CHAT) ---
    else:
        proj = st.session_state.active_project
        st.title(f"📂 {proj['title']}")
        
        # Adicionei uma aba nova: "💬 Assistente"
        if proj['category'] == 'historia':
            tab_assistente, tab_macro, tab_micro = st.tabs(["💬 Assistente Geral", "🌍 Universo (Macro)", "✍️ Manuscrito (Micro)"])
            
            with tab_assistente:
                renderizar_chat(proj, contexto_extra="Foco: Discussão geral sobre a história.")
            
            with tab_macro:
                st.header("Bíblia da História")
                st.text_area("Resumo do Universo", height=200)
                st.button("Validar Universo (CrewAI)", key="btn_macro")

            with tab_micro:
                st.header("Capítulos e Cenas")
                st.text_area("Escreva o capítulo atual...", height=300)
                st.button("Validar Capítulo (CrewAI)", key="btn_micro")

        else:
            tab_assistente, tab_geral, tab_validacao = st.tabs(["💬 Assistente Geral", "💡 Desenvolvimento", "✅ Validação Técnica"])
            
            with tab_assistente:
                renderizar_chat(proj, contexto_extra="Foco: Brainstorming de negócio e produto.")

            with tab_geral:
                st.subheader("Evolução do Projeto")
                st.text_area("Notas de evolução", height=200)
            
            with tab_validacao:
                st.write("Área para relatórios técnicos.")
                st.button("Chamar Especialistas (CrewAI)", key="btn_proj")
