import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
import teams  # Importa nosso arquivo de motor de equipes

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
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)
    else:
        llm = None
except Exception as e:
    st.error(f"Erro ao configurar IA: {e}")
    llm = None

# --- ESTADO DA SESSÃO ---
if "user" not in st.session_state: st.session_state.user = None
if "active_project" not in st.session_state: st.session_state.active_project = None

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
        
        # Campos Universais (Para Histórias E Projetos)
        "chat_history": [],
        "macro_context_text": "", 
        "macro_chat_history": [],
        "micro_chat_history": [],
        "micro_content_text": "",
        
        # Relatórios CrewAI
        "reports_macro": [],
        "reports_micro": []
    })
    st.toast(f"Ideia '{titulo}' criada!", icon="✅")
    st.rerun()

def atualizar_campo_firebase(projeto_id, campo, valor):
    db.collection("ideas").document(projeto_id).update({campo: valor})

def salvar_relatorio_crew(projeto_id, campo_array, relatorio_texto):
    """Adiciona relatório ao Banco E atualiza a Tela imediatamente"""
    texto_final = str(relatorio_texto)
    
    novo_relatorio = {
        "date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "content": texto_final
    }
    
    # Salva no Banco
    db.collection("ideas").document(projeto_id).update({
        campo_array: firestore.ArrayUnion([novo_relatorio])
    })
    
    # Atualiza a Sessão Local
    if st.session_state.active_project:
        if campo_array not in st.session_state.active_project:
            st.session_state.active_project[campo_array] = []
        st.session_state.active_project[campo_array].append(novo_relatorio)

def salvar_historico_chat(projeto_id, campo_banco, historico_langchain):
    historico_json = []
    for msg in historico_langchain:
        role = "user" if isinstance(msg, HumanMessage) else "ai"
        historico_json.append({"role": role, "content": msg.content})
    atualizar_campo_firebase(projeto_id, campo_banco, historico_json)

def gerar_resumo_ia(historico_chat, tipo_resumo):
    """Usa a IA para transformar o chat bagunçado em texto limpo"""
    if not llm or not historico_chat: return None

    texto_conversa = ""
    for msg in historico_chat:
        role = msg.get("role") if isinstance(msg, dict) else ("user" if isinstance(msg, HumanMessage) else "ai")
        content = msg.get("content") if isinstance(msg, dict) else msg.content
        texto_conversa += f"{role}: {content}\n"
    
    prompt = f"""
    Analise a conversa a seguir. Ignore cumprimentos e papo furado.
    O objetivo é criar um documento oficial ({tipo_resumo}) organizado.
    Extraia as melhores ideias e formate como um texto profissional.
    
    CONVERSA:
    {texto_conversa}
    """
    
    with st.spinner("🪄 A IA está organizando suas ideias..."):
        try:
            resposta = llm.invoke(prompt)
            return resposta.content
        except Exception as e:
            st.error(f"Erro ao gerar resumo: {e}")
            return None

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
        if not llm: return

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
# UI - INTERFACE DO USUÁRIO
# ==================================================

if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Estúdio Criativo")
        if st.button("Entrar (Simulado)", type="primary", use_container_width=True): login()
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
            if st.button("Sair"): logout()

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
        
        # LÓGICA UNIFICADA PARA TABS (AGORA SERVE PARA TODOS)
        # Se for história, usamos termos literários. Se for projeto, termos de negócio.
        is_historia = proj['category'] == 'historia'
        
        label_macro = "🌍 Universo (Macro)" if is_historia else "1️⃣ Estratégia (Macro)"
        label_micro = "✍️ Manuscrito (Micro)" if is_historia else "2️⃣ Execução (Micro)"
        
        prompt_sys_macro = "Arquiteto de Mundos" if is_historia else "Estrategista de Negócios"
        prompt_sys_micro = "Editor Literário" if is_historia else "Gerente de Projeto e Legal"
        
        label_txt_macro = "Resumo Oficial do Mundo" if is_historia else "Canvas de Negócio e Estratégia"
        label_txt_micro = "Capítulo Atual" if is_historia else "Especificação Técnica e Legal"

        tab_macro, tab_micro, tab_criativo = st.tabs([label_macro, label_micro, "🎨 Laboratório Criativo"])
        
        # --- ABA MACRO ---
        with tab_macro:
            c1, c2 = st.columns([1,1])
            with c1:
                st.subheader("Definições Gerais")
                if st.button("🪄 Resumir Chat", key="auto_macro"):
                    hist = st.session_state.get(f"chat_memory_{proj['id']}_macro", proj.get("macro_chat_history", []))
                    res = gerar_resumo_ia(hist, "macro")
                    if res:
                        atualizar_campo_firebase(proj["id"], "macro_context_text", res)
                        proj["macro_context_text"] = res
                        st.rerun()
                
                txt_macro = st.text_area(label_txt_macro, value=proj.get("macro_context_text", ""), height=300, key="t_macro")
                if st.button("💾 Salvar Macro"):
                    atualizar_campo_firebase(proj["id"], "macro_context_text", txt_macro)
                    proj["macro_context_text"] = txt_macro
                    st.toast("Salvo!")

                st.divider()
                if st.button("✨ Validar Estratégia (CrewAI)", type="primary", key="v_macro"):
                    if not txt_macro:
                        st.error("Escreva algo primeiro!")
                    else:
                        with st.status("🤖 Analisando...", expanded=True):
                            if is_historia:
                                res = teams.rodar_equipe_macro(txt_macro, proj['title'])
                            elif proj['category'] == 'empreendimento':
                                # CHAMA A EQUIPE FÍSICA MACRO
                                res = teams.rodar_equipe_fisico_macro(txt_macro, proj['title'])
                            else:
                                # CHAMA A EQUIPE DIGITAL MACRO (PROJETOS)
                                res = teams.rodar_equipe_negocio_macro(txt_macro, proj['title'])
                            
                            salvar_relatorio_crew(proj['id'], "reports_macro", res)
                            st.rerun()
                
                if proj.get("reports_macro"):
                    st.divider()
                    st.subheader("📊 Relatórios")
                    for i, rep in enumerate(reversed(proj["reports_macro"])):
                        with st.expander(f"Relatório {rep['date']}", expanded=(i==0)):
                            st.markdown(rep['content'])
                            st.download_button("📥 Baixar", rep['content'], f"Macro_{i}.txt", key=f"d1_{i}")

            with c2:
                renderizar_chat_componente(proj, "macro_chat_history", f"Você é um {prompt_sys_macro}. Projeto: {proj['title']}", "macro")

        # --- ABA MICRO ---
        with tab_micro:
            c1, c2 = st.columns([1,1])
            with c1:
                st.subheader("Detalhes e Execução")
                if st.button("🪄 Resumir Chat", key="auto_micro"):
                    hist = st.session_state.get(f"chat_memory_{proj['id']}_micro", proj.get("micro_chat_history", []))
                    res = gerar_resumo_ia(hist, "micro")
                    if res:
                        atualizar_campo_firebase(proj["id"], "micro_content_text", res)
                        proj["micro_content_text"] = res
                        st.rerun()

                txt_micro = st.text_area(label_txt_micro, value=proj.get("micro_content_text", ""), height=300, key="t_micro")
                if st.button("💾 Salvar Micro"):
                    atualizar_campo_firebase(proj["id"], "micro_content_text", txt_micro)
                    proj["micro_content_text"] = txt_micro
                    st.toast("Salvo!")

                st.divider()
                if st.button("✨ Validar Execução (CrewAI)", type="primary", key="v_micro"):
                    if not txt_micro:
                        st.error("Escreva algo primeiro!")
                    else:
                        with st.status("🤖 Analisando...", expanded=True):
                            ctx = proj.get("macro_context_text", "")
                            if is_historia:
                                res = teams.rodar_equipe_micro(txt_micro, ctx)
                            elif proj['category'] == 'empreendimento':
                                # CHAMA A EQUIPE FÍSICA MICRO
                                res = teams.rodar_equipe_fisico_micro(txt_micro, ctx)
                            else:
                                # CHAMA A EQUIPE DIGITAL MICRO (PROJETOS)
                                res = teams.rodar_equipe_negocio_micro(txt_micro, ctx)
                            
                            salvar_relatorio_crew(proj['id'], "reports_micro", res)
                            st.rerun()

                if proj.get("reports_micro"):
                    st.divider()
                    st.subheader("📊 Relatórios")
                    for i, rep in enumerate(reversed(proj["reports_micro"])):
                        with st.expander(f"Relatório {rep['date']}", expanded=(i==0)):
                            st.markdown(rep['content'])
                            st.download_button("📥 Baixar", rep['content'], f"Micro_{i}.txt", key=f"d2_{i}")

            with c2:
                ctx_prompt = proj.get("macro_context_text", "")
                renderizar_chat_componente(proj, "micro_chat_history", f"Você é um {prompt_sys_micro}. Contexto: {ctx_prompt}", "micro")

        # --- ABA CRIATIVA ---
        with tab_criativo:
            st.header("🎨 Laboratório Criativo")
            st.info("🚧 Em breve: Integração com LangGraph para geração automática de pivôs e variações.")
            c1, c2 = st.columns(2)
            c1.checkbox("Gerar Pivô de Negócio")
            c1.checkbox("Expandir Funcionalidades")
            c2.button("🧪 Iniciar (Desativado)", disabled=True)
