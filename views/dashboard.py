import streamlit as st
import datetime
from services import database as db
from services import auth

def render_sidebar():
    with st.sidebar:
        st.title("🚀 Menu")
        st.write(f"Olá, **{st.session_state.user['name']}**")
        
        # Seleção de Categoria
        page = st.radio("Ir para:", ["🏠 Home", "🏗️ Empreendimentos", "💻 Projetos Digitais", "📖 Histórias"])
        
        st.divider()
        if st.button("Sair"):
            auth.logout()
            
    return page

def render_create_dialog(categoria_tecnica):
    @st.dialog("💡 Nova Ideia")
    def dialog_form():
        titulo = st.text_input("Nome Provisório")
        descricao = st.text_area("Descrição Rápida")
        if st.button("Criar Projeto"):
            if titulo:
                # Chama o serviço de banco de dados
                db.criar_nova_ideia(st.session_state.user["email"], titulo, descricao, categoria_tecnica)
                st.toast(f"Ideia '{titulo}' criada!", icon="✅")
                st.rerun()
            else:
                st.warning("O título é obrigatório.")
    
    dialog_form()

def render_dashboard():
    page = render_sidebar()
    
    if page == "🏠 Home":
        st.title("Bem-vindo ao Estúdio")
        st.markdown("Selecione uma categoria no menu lateral para começar.")
        # Aqui futuramente colocaremos métricas gerais
    else:
        # Mapeamento Visual -> Técnico
        cat_map = {
            "🏗️ Empreendimentos": "empreendimento", 
            "💻 Projetos Digitais": "projeto", 
            "📖 Histórias": "historia"
        }
        categoria_tecnica = cat_map.get(page, "projeto")

        # Cabeçalho
        c1, c2 = st.columns([3, 1])
        c1.title(page)
        if c2.button("➕ Nova Ideia", type="primary"):
            render_create_dialog(categoria_tecnica)
        
        # Listagem (Chama o Serviço)
        docs = db.listar_ideias(st.session_state.user["email"], categoria_tecnica)
        ideias = list(docs)
        
        if not ideias:
            st.info("Nenhum projeto aqui ainda.")
        
        # Renderiza Cartões
        for doc in ideias:
            data = doc.to_dict()
            with st.container(border=True):
                col_a, col_b, col_c = st.columns([4, 2, 2])
                col_a.subheader(data['title'])
                col_a.caption(data.get('description', ''))
                col_b.write(f"Status: **{data.get('status', 'Rascunho')}**")
                
                # Botão de Abrir (Atualiza Sessão)
                if col_c.button("Abrir Sala de Guerra ⚔️", key=doc.id):
                    st.session_state.active_project = {**data, "id": doc.id}
                    st.rerun()
