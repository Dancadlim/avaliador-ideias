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
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
    else:
        st.warning("⚠️ Configure a chave [google] nos Secrets.")
        llm = None
except Exception as e:
    st.error(f"Erro ao configurar IA: {e}")
    llm = None

# --- ESTADO DA SESSÃO ---
if "user" not in st.session_state:
    st.session_state.user = None
if "active_project" not in st.session_state:
    st.session_state.active_project = None

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
        
        # Campos gerais
        "chat_history": [],
        
        # Campos Específicos de História
        "macro_context_text": "",  # O texto resumo do mundo
        "macro_chat_history": [],  # Chat do Arquiteto
        "micro_chat_history": [],  # Chat do Escritor
        "micro_content_text": ""   # O rascunho do capítulo
    })
    st.toast(f"Ideia '{titulo}' criada!", icon="✅")
    st.rerun()

def atualizar_campo_firebase(projeto_id, campo, valor):
    """Atualiza qualquer campo no documento do projeto"""
    db.collection("ideas").document(projeto_id).update({
        campo: valor
    })

def salvar_historico_chat(projeto_id, campo_banco, historico_langchain):
    """Salva o histórico de chat específico (Macro ou Micro) no Firebase"""
    historico_json = []
    for msg in historico_langchain:
        role = "user" if isinstance(msg, HumanMessage) else "ai"
        historico_json.append({"role": role, "content": msg.content})
    
    atualizar_campo_firebase(projeto_id, campo_banco, historico_json)

# --- COMPONENTE DE CHAT GENÉRICO (AGORA MAIS INTELIGENTE) ---
def renderizar_chat_componente(projeto, campo_banco, system_prompt, key_suffix):
    """
    Cria uma instância de chat independente.
    key_suffix: Importante para o Streamlit não confundir os chats das abas diferentes.
    """
    st.subheader(f"💬 Assistente ({key_suffix.capitalize()})")
    
    # Nome da variável de sessão única para este chat
    session_key = f"chat_memory_{projeto['id']}_{key_suffix}"

    # 1. Carregar histórico do Firebase se não estiver na sessão
    if session_key not in st.session_state:
        st.session_state[session_key] = []
        # Tenta pegar do banco, se não existir (projetos antigos), usa lista vazia
        historico_salvo = projeto.get(campo_banco, [])
        for msg in historico_salvo:
            if msg["role"] == "user":
                st.session_state[session_key].append(HumanMessage(content=msg["content"]))
            else:
                st.session_state[session_key].append(AIMessage(content=msg["content"]))

    # 2. Mostrar mensagens
    container_chat = st.container(height=400) # Scrollable container
    with container_chat:
        for msg in st.session_state[session_key]:
            role = "user" if isinstance(msg, HumanMessage) else "ai"
            avatar = "👤" if role == "user" else "🤖"
            with st.chat_message(role, avatar=avatar):
                st.write(msg.content)

    # 3. Input
    if prompt := st.chat_input(f"Fale com o {key_suffix}...", key=f"input_{key_suffix}"):
        if not llm:
            st.error("IA não configurada.")
            return

        # A. Mostrar mensagem user
        with container_chat:
            st.chat_message("user", avatar="👤").write(prompt)
        st.session_state[session_key].append(HumanMessage(content=prompt))

        # B. Gerar resposta IA
        with container_chat:
            with st.chat_message("ai", avatar="🤖"):
                with st.spinner("Pensando..."):
                    messages = [HumanMessage(content=system_prompt)] + st.session_state[session_key]
                    response = llm.invoke(messages)
                    st.write(response.content)
        
        # C. Salvar
        st.session_state[session_key].append(AIMessage(content=response.content))
        salvar_historico_chat(projeto["id"], campo_banco, st.session_state[session_key])


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
                # Limpa sessões de chat ao sair para economizar memória
                keys_to_del = [k for k in st.session_state.keys() if "chat_memory" in k]
                for k in keys_to_del: del st.session_state[k]
                fechar_projeto()
            st.divider()
            st.info(f"Editando: **{st.session_state.active_project['title']}**")
        else:
            st.write(f"Olá, **{st.session_state.user['name']}**")
            page = st.radio("Ir para:", ["🏠 Home", "🏗️ Empreendimentos", "💻 Projetos Digitais", "📖 Histórias"])
            st.divider()
            if st.button("Sair"):
                logout()

    # --- NAVEGAÇÃO PRINCIPAL ---
    if not st.session_state.active_project:
        if page == "🏠 Home":
            st.title("Bem-vindo ao Estúdio")
            st.markdown("Selecione uma categoria no menu lateral.")
        else:
            cat_map = {"🏗️ Empreendimentos": "empreendimento", "💻 Projetos Digitais": "projeto", "📖 Histórias": "historia"}
            categoria_tecnica = cat_map.get(page, "projeto")

            c1, c2 = st.columns([3, 1])
            c1.title(page)
            
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

    # --- SALA DE GUERRA (WORKSPACE) ---
    else:
        proj = st.session_state.active_project
        st.title(f"📂 {proj['title']}")
        
        # ==========================================
        # LÓGICA ESPECÍFICA PARA HISTÓRIAS
        # ==========================================
        if proj['category'] == 'historia':
            tab_macro, tab_micro = st.tabs(["🌍 Universo (Macro)", "✍️ Manuscrito (Micro)"])
            
            # --- ABA MACRO (O ARQUITETO) ---
            with tab_macro:
                col_m1, col_m2 = st.columns([1, 1])
                
                with col_m1:
                    st.subheader("Definições do Mundo")
                    st.markdown("Escreva aqui as regras, resumo do enredo e verdades do universo.")
                    
                    # Campo de texto que salva automaticamente quando muda (on_change é complexo, vamos usar key unique e salvar no blur ou botao)
                    macro_text = st.text_area("Resumo Oficial do Mundo (Contexto para o Micro)", 
                                            value=proj.get("macro_context_text", ""), 
                                            height=300,
                                            key="txt_macro")
                    
                    if st.button("Salvar Definições Macro"):
                        atualizar_campo_firebase(proj["id"], "macro_context_text", macro_text)
                        st.toast("Contexto Macro salvo!", icon="🌍")
                        # Atualiza o estado local para refletir na outra aba sem precisar recarregar
                        proj["macro_context_text"] = macro_text 

                    st.divider()
                    st.button("✨ Validar Lógica do Mundo (CrewAI Macro)", type="primary")

                with col_m2:
                    # PROMPT DO ARQUITETO
                    prompt_macro = f"""
                    Você é um Arquiteto de Mundos e Estrategista Narrativo especialista.
                    Ajude a definir as regras do universo, sistemas de magia, política e arcos de personagens.
                    Seja questionador. Encontre furos na lógica do mundo.
                    Projeto: {proj['title']}
                    """
                    renderizar_chat_componente(proj, "macro_chat_history", prompt_macro, "macro")

            # --- ABA MICRO (O ESCRITOR) ---
            with tab_micro:
                col_u1, col_u2 = st.columns([1, 1])
                
                with col_u1:
                    st.subheader("Área de Escrita")
                    micro_text = st.text_area("Capítulo Atual", 
                                            value=proj.get("micro_content_text", ""),
                                            height=500,
                                            key="txt_micro")
                    
                    if st.button("Salvar Capítulo"):
                        atualizar_campo_firebase(proj["id"], "micro_content_text", micro_text)
                        st.toast("Capítulo salvo!", icon="💾")

                    st.divider()
                    st.button("✨ Validar Escrita e Cena (CrewAI Micro)", type="primary")

                with col_u2:
                    # PROMPT DO ESCRITOR (COM INJEÇÃO DE CONTEXTO)
                    # Aqui pegamos o texto da aba Macro e injetamos no cérebro deste assistente
                    contexto_do_mundo = proj.get("macro_context_text", "Nenhum contexto de mundo definido ainda.")
                    
                    prompt_micro = f"""
                    Você é um Editor Literário e Assistente de Escrita Criativa.
                    Ajude a escrever cenas, diálogos e descrições. Melhore a prosa.
                    
                    CONTEXTO OBRIGATÓRIO DO MUNDO (Respeite estas regras):
                    {contexto_do_mundo}
                    
                    Projeto: {proj['title']}
                    """
                    
                    # Renderiza o chat com o prompt "turbinado"
                    renderizar_chat_componente(proj, "micro_chat_history", prompt_micro, "micro")

        # ==========================================
        # LÓGICA PARA PROJETOS/EMPREENDIMENTOS (Padrão)
        # ==========================================
        else:
            tab_chat, tab_docs = st.tabs(["💬 Assistente Geral", "📝 Documentação"])
            
            with tab_chat:
                prompt_geral = f"Você é um consultor especialista em {proj['category']}. Ajude a refinar a ideia: {proj['title']}"
                renderizar_chat_componente(proj, "chat_history", prompt_geral, "geral")
            
            with tab_docs:
                st.text_area("Rascunho do Projeto", height=400)
                st.button("Validar Ideia (CrewAI)")
