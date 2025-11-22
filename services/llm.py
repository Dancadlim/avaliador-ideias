import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI

def get_chat_model():
    try:
        if "google" in st.secrets:
            api_key = st.secrets["google"]["api_key"]
            return ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)
        return None
    except Exception as e:
        st.error(f"Erro IA: {e}")
        return None

def gerar_resumo(historico_chat, tipo_resumo):
    llm = get_chat_model()
    if not llm or not historico_chat: return None

    texto_conversa = ""
    for msg in historico_chat:
        # Lida com dicionários (do banco) ou objetos (da memória)
        role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "type", "user")
        content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")
        # Ajuste fino para LangChain types
        if role == "human": role = "user"
        if role == "ai": role = "ai"
        
        texto_conversa += f"{role}: {content}\n"
    
    prompt = f"""
    Analise a conversa a seguir. Ignore cumprimentos.
    Crie um documento oficial ({tipo_resumo}) organizado.
    Extraia as melhores ideias e formate como texto profissional.
    
    CONVERSA:
    {texto_conversa}
    """
    
    try:
        return llm.invoke(prompt).content
    except:
        return None
