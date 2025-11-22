import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from services import database as db
from services import llm
import teams

# --- COMPONENTE DE CHAT ---
def render_chat(projeto, campo_banco, system_prompt, key_suffix):
    st.subheader(f"💬 Assistente ({key_suffix.capitalize()})")
    session_key = f"chat_memory_{projeto['id']}_{key_suffix}"

    # Inicializa memória local se não existir
    if session_key not in st.session_state:
        st.session_state[session_key] = []
        historico_salvo = projeto.get(campo_banco, [])
        # Reconstrói objetos LangChain a partir do JSON do banco
        for msg in historico_salvo:
            if msg["role"] == "user":
                st.session_state[session_key].append(HumanMessage(content=msg["content"]))
            else:
                st.session_state[session_key].append(AIMessage(content=msg["content"]))

    # Exibe mensagens
    with st.container(height=400):
        for msg in st.session_state[session_key]:
            avatar = "👤" if isinstance(msg, HumanMessage) else "🤖"
            role = "user" if isinstance(msg, HumanMessage) else "ai"
            st.chat_message(role, avatar=avatar).write(msg.content)

    # Input do usuário
    chat_model = llm.get_chat_model()
    if prompt := st.chat_input(f"Fale com o {key_suffix}...", key=f"input_{key_suffix}"):
        if not chat_model: return

        # Adiciona msg do usuário
        st.session_state[session_key].append(HumanMessage(content=prompt))
        
        # Roda a IA
        messages = [HumanMessage(content=system_prompt)] + st.session_state[session_key]
        response = chat_model.invoke(messages)
        
        # Adiciona resposta da IA
        st.session_state[session_key].append(AIMessage(content=response.content))
        
        # Salva no banco (Serviço Database)
        # Converte para JSON puro antes de salvar
        hist_json = [{"role": "user" if isinstance(m, HumanMessage) else "ai", "content": m.content} for m in st.session_state[session_key]]
        db.atualizar_campo(projeto["id"], campo_banco, hist_json)
        st.rerun()

# --- VIEW PRINCIPAL ---
def render_workspace():
    proj = st.session_state.active_project
    
    # Sidebar simplificada para voltar
    with st.sidebar:
        st.title("📂 Projeto")
        if st.button("⬅️ Voltar para Lista"):
            # Limpa memória RAM dos chats
            keys_to_del = [k for k in st.session_state.keys() if "chat_memory" in k]
            for k in keys_to_del: del st.session_state[k]
            
            st.session_state.active_project = None
            st.rerun()
        st.divider()
        st.info(f"Editando: **{proj['title']}**")

    st.title(f"📂 {proj['title']}")

    # Configurações dinâmicas baseadas no tipo
    is_historia = proj['category'] == 'historia'
    label_macro = "🌍 Universo (Macro)" if is_historia else "1️⃣ Estratégia (Macro)"
    label_micro = "✍️ Manuscrito (Micro)" if is_historia else "2️⃣ Execução (Micro)"
    
    prompt_sys_macro = "Arquiteto de Mundos" if is_historia else "Estrategista de Negócios"
    prompt_sys_micro = "Editor Literário" if is_historia else "Gerente de Projeto e Legal"

    tab_macro, tab_micro, tab_criativo = st.tabs([label_macro, label_micro, "🎨 Laboratório Criativo"])

    # --- ABA MACRO ---
    with tab_macro:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("Definições Gerais")
            
            # Botão Mágico de Resumo
            if st.button("🪄 Resumir Chat", key="auto_macro"):
                # Busca histórico (da sessão ou do projeto)
                hist = st.session_state.get(f"chat_memory_{proj['id']}_macro", proj.get("macro_chat_history", []))
                resumo = llm.gerar_resumo(hist, "macro")
                if resumo:
                    db.atualizar_campo(proj["id"], "macro_context_text", resumo)
                    proj["macro_context_text"] = resumo # Atualiza local
                    st.rerun()

            txt_macro = st.text_area("Texto Principal", value=proj.get("macro_context_text", ""), height=300, key="t_macro")
            
            if st.button("💾 Salvar Macro"):
                db.atualizar_campo(proj["id"], "macro_context_text", txt_macro)
                proj["macro_context_text"] = txt_macro
                st.toast("Salvo!")

            st.divider()
            
            # Validação CrewAI
            if st.button("✨ Validar Estratégia", type="primary", key="v_macro"):
                if not txt_macro:
                    st.error("Escreva algo primeiro!")
                else:
                    with st.status("🤖 Analisando...", expanded=True):
                        if is_historia:
                            res = teams.rodar_equipe_macro(txt_macro, proj['title'])
                        elif proj['category'] == 'empreendimento':
                            res = teams.rodar_equipe_fisico_macro(txt_macro, proj['title'])
                        else:
                            res = teams.rodar_equipe_negocio_macro(txt_macro, proj['title'])
                        
                        # Salva e atualiza a sessão local
                        novo_relatorio = db.salvar_relatorio(proj['id'], "reports_macro", res)
                        if "reports_macro" not in proj: proj["reports_macro"] = []
                        proj["reports_macro"].append(novo_relatorio)
                        st.rerun()

            # Exibir Relatórios
            if proj.get("reports_macro"):
                st.divider()
                for i, rep in enumerate(reversed(proj["reports_macro"])):
                    with st.expander(f"Relatório {rep['date']}", expanded=(i==0)):
                        st.markdown(rep['content'])
                        st.download_button("📥 Baixar", rep['content'], f"Macro_{i}.txt", key=f"dm_{i}")

        with c2:
            render_chat(proj, "macro_chat_history", f"Você é um {prompt_sys_macro}.", "macro")

    # --- ABA MICRO ---
    with tab_micro:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("Detalhes e Execução")
            if st.button("🪄 Resumir Chat", key="auto_micro"):
                hist = st.session_state.get(f"chat_memory_{proj['id']}_micro", proj.get("micro_chat_history", []))
                resumo = llm.gerar_resumo(hist, "micro")
                if resumo:
                    db.atualizar_campo(proj["id"], "micro_content_text", resumo)
                    proj["micro_content_text"] = resumo
                    st.rerun()

            txt_micro = st.text_area("Texto Detalhado", value=proj.get("micro_content_text", ""), height=300, key="t_micro")
            
            if st.button("💾 Salvar Micro"):
                db.atualizar_campo(proj["id"], "micro_content_text", txt_micro)
                proj["micro_content_text"] = txt_micro
                st.toast("Salvo!")

            st.divider()
            
            if st.button("✨ Validar Execução", type="primary", key="v_micro"):
                if not txt_micro:
                    st.error("Escreva algo primeiro!")
                else:
                    with st.status("🤖 Analisando...", expanded=True):
                        ctx = proj.get("macro_context_text", "")
                        if is_historia:
                            res = teams.rodar_equipe_micro(txt_micro, ctx)
                        elif proj['category'] == 'empreendimento':
                            res = teams.rodar_equipe_fisico_micro(txt_micro, ctx)
                        else:
                            res = teams.rodar_equipe_negocio_micro(txt_micro, ctx)
                        
                        novo_relatorio = db.salvar_relatorio(proj['id'], "reports_micro", res)
                        if "reports_micro" not in proj: proj["reports_micro"] = []
                        proj["reports_micro"].append(novo_relatorio)
                        st.rerun()

            if proj.get("reports_micro"):
                st.divider()
                for i, rep in enumerate(reversed(proj["reports_micro"])):
                    with st.expander(f"Relatório {rep['date']}", expanded=(i==0)):
                        st.markdown(rep['content'])
                        st.download_button("📥 Baixar", rep['content'], f"Micro_{i}.txt", key=f"dmic_{i}")

        with c2:
            ctx_prompt = proj.get("macro_context_text", "")
            render_chat(proj, "micro_chat_history", f"Você é um {prompt_sys_micro}. Contexto: {ctx_prompt}", "micro")

    with tab_criativo:
        st.header("🎨 Laboratório Criativo")
        st.info("Integração LangGraph em breve.")
