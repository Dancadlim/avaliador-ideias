import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
# --- IMPORTAÇÃO NOVA ---
import teams 

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Avaliador de Ideias", page_icon="🚀", layout="wide")

# --- 1. CONEXÃO COM FIREBASE ---
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
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)
    else:
        # st.warning("⚠️ Configure a chave [google] nos Secrets.") # Comentado para limpar a tela
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
        "chat_history": [],
        "macro_context_text": "", 
        "macro_chat_history": [],
        "micro_chat_history": [],
        "micro_content_text": "",
        # Novos campos para guardar os relatórios da CrewAI
        "reports_macro": [],
        "reports_micro": []
    })
    st.toast(f"Ideia '{titulo}' criada!", icon="✅")
    st.rerun()

def atualizar_campo_firebase(projeto_id, campo, valor):
    db.collection("ideas").document(projeto_id).update({campo: valor})

def salvar_relatorio_crew(projeto_id, campo_array, relatorio_texto):
    """Adiciona um novo relatório à lista no Firebase"""
    novo_relatorio = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "content": str(relatorio_texto) # Garante que é string
    }
    # Firestore arrayUnion adiciona à lista existente
    db.collection("ideas").document(projeto_id).update({
        campo_array: firestore.ArrayUnion([novo_relatorio])
    })

def salvar_historico_chat(projeto_id, campo_banco, historico_langchain):
    historico_json = []
    for msg in historico_langchain:
        role = "user" if isinstance(msg, HumanMessage) else "ai"
        historico_json.append({"role": role, "content": msg.content})
    atualizar_campo_firebase(projeto_id, campo_banco, historico_json)

# --- COMPONENTE DE CHAT ---
def renderizar_chat_componente(projeto, campo_banco, system_prompt, key_suffix):
    st.subheader(f"💬 Assistente ({key_suffix.capitalize()})")
    session_key = f"chat_memory_{projeto['id']}_{key_suffix}"

    if session_key not in st.session_state:
        st.session_state[session_key] = []
        historico_salvo = projeto.get(campo_banco, [])
        for msg in historico_salvo:
            if msg["role"] == "user":
                st.session_state[session_key].append(HumanMessage(content=msg["content"]))
            else:
                st.session_state[session_key].append(AIMessage(content=msg["content"]))

    container_chat = st.container(height=400)
    with container_chat:
        for msg in st.session_state[session_key]:
            role = "user" if isinstance(msg, HumanMessage) else "ai"
            avatar = "👤" if role == "user" else "🤖"
            with st.chat_message(role, avatar=avatar):
                st.write(msg.content)

    if prompt := st.chat_input(f"Fale com o {key_suffix}...", key=f"input_{key_suffix}"):
        if not llm:
            st.error("IA não configurada.")
            return

        with container_chat:
            st.chat_message("user", avatar="👤").write(prompt)
        st.session_state[session_key].append(HumanMessage(content=prompt))

        with container_chat:
            with st.chat_message("ai", avatar="🤖"):
                with st.spinner("Pensando..."):
                    messages = [HumanMessage(content=system_prompt)] + st.session_state[session_key]
                    response = llm.invoke(messages)
                    st.write(response.content)
        
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
    with st.sidebar:
        st.title("🚀 Menu")
        if st.session_state.active_project:
            if st.button("⬅️ Voltar para Lista"):
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

    # --- SALA DE GUERRA ---
    else:
        proj = st.session_state.active_project
        st.title(f"📂 {proj['title']}")
        
        if proj['category'] == 'historia':
            tab_macro, tab_micro = st.tabs(["🌍 Universo (Macro)", "✍️ Manuscrito (Micro)"])
            
            # --- ABA MACRO ---
            with tab_macro:
                col_m1, col_m2 = st.columns([1, 1])
                with col_m1:
                    st.subheader("Definições do Mundo")
                    macro_text = st.text_area("Resumo Oficial do Mundo", value=proj.get("macro_context_text", ""), height=300, key="txt_macro")
                    
                    if st.button("Salvar Definições Macro"):
                        atualizar_campo_firebase(proj["id"], "macro_context_text", macro_text)
                        st.toast("Contexto salvo!", icon="🌍")
                        proj["macro_context_text"] = macro_text 

                    st.divider()
                    
                    # BOTÃO MÁGICO DO CREWAI MACRO
                    if st.button("✨ Validar Lógica do Mundo (CrewAI)", type="primary", key="btn_crew_macro"):
                        if not macro_text:
                            st.error("Escreva algo no resumo primeiro!")
                        else:
                            with st.status("🤖 A Equipe Macro está trabalhando...", expanded=True) as status:
                                st.write("🧠 Arquiteto de Lore analisando consistência...")
                                st.write("📚 Analista Literário verificando mercado...")
                                
                                # CHAMA A FUNÇÃO DO NOVO ARQUIVO TEAMS.PY
                                resultado = teams.rodar_equipe_macro(macro_text, proj['title'])
                                
                                salvar_relatorio_crew(proj['id'], "reports_macro", resultado)
                                status.update(label="✅ Análise Completa!", state="complete", expanded=False)
                                st.rerun() # Recarrega para mostrar o relatório embaixo

                    # Exibir Relatórios Anteriores
                    if proj.get("reports_macro"):
                        with st.expander("📜 Ver Relatórios de Validação Anteriores"):
                            for rep in reversed(proj["reports_macro"]):
                                st.caption(f"Gerado em: {rep['date']}")
                                st.markdown(rep['content'])
                                st.divider()

                with col_m2:
                    prompt_macro = f"Você é um Arquiteto de Mundos. Ajude a definir regras. Projeto: {proj['title']}"
                    renderizar_chat_componente(proj, "macro_chat_history", prompt_macro, "macro")

            # --- ABA MICRO ---
            with tab_micro:
                col_u1, col_u2 = st.columns([1, 1])
                with col_u1:
                    st.subheader("Área de Escrita")
                    micro_text = st.text_area("Capítulo Atual", value=proj.get("micro_content_text", ""), height=500, key="txt_micro")
                    
                    if st.button("Salvar Capítulo"):
                        atualizar_campo_firebase(proj["id"], "micro_content_text", micro_text)
                        st.toast("Capítulo salvo!", icon="💾")

                    st.divider()
                    
                    # BOTÃO MÁGICO DO CREWAI MICRO
                    if st.button("✨ Validar Escrita e Cena (CrewAI)", type="primary", key="btn_crew_micro"):
                        if not micro_text:
                            st.error("Escreva algo no capítulo primeiro!")
                        else:
                            with st.status("🤖 A Equipe Micro está lendo...", expanded=True) as status:
                                st.write("🔍 Fiscal de Continuidade checando regras...")
                                st.write("✒️ Crítico de Estilo analisando prosa...")
                                
                                contexto = proj.get("macro_context_text", "Sem contexto definido.")
                                
                                # CHAMA A FUNÇÃO DO NOVO ARQUIVO TEAMS.PY
                                resultado = teams.rodar_equipe_micro(micro_text, contexto)
                                
                                salvar_relatorio_crew(proj['id'], "reports_micro", resultado)
                                status.update(label="✅ Análise Completa!", state="complete", expanded=False)
                                st.rerun()

                    # Exibir Relatórios Anteriores
                    if proj.get("reports_micro"):
                        with st.expander("📜 Ver Críticas de Estilo Anteriores"):
                            for rep in reversed(proj["reports_micro"]):
                                st.caption(f"Gerado em: {rep['date']}")
                                st.markdown(rep['content'])
                                st.divider()

                with col_u2:
                    contexto_do_mundo = proj.get("macro_context_text", "Nenhum contexto.")
                    prompt_micro = f"Você é um Editor. Contexto Obrigatório: {contexto_do_mundo}. Projeto: {proj['title']}"
                    renderizar_chat_componente(proj, "micro_chat_history", prompt_micro, "micro")

        else:
            tab_chat, tab_docs = st.tabs(["💬 Assistente Geral", "📝 Documentação"])
            with tab_chat:
                prompt_geral = f"Você é um consultor especialista em {proj['category']}. Ajude a refinar: {proj['title']}"
                renderizar_chat_componente(proj, "chat_history", prompt_geral, "geral")
            with tab_docs:
                st.text_area("Rascunho do Projeto", height=400)
                st.info("Em breve: Validação de Projetos e Empreendimentos via CrewAI.")
