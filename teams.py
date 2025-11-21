import os
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st

# --- CONFIGURAÇÃO DA IA PARA OS AGENTES ---
# Função para pegar o LLM configurado com a sua chave
def get_llm():
    if "google" in st.secrets:
        api_key = st.secrets["google"]["api_key"]
        # Usando Flash para ser rápido no Streamlit Cloud
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.7
        )
    return None

# ==========================================================
# 🌍 EQUIPE 1: VALIDAÇÃO DE MACRO (MUNDO/HISTÓRIA)
# ==========================================================
def rodar_equipe_macro(resumo_universo, titulo_projeto):
    llm = get_llm()
    if not llm: return "Erro: Chave de API não configurada."

    # 1. Agentes
    agente_logica = Agent(
        role='Arquiteto de Lore',
        goal='Garantir que as regras do mundo sejam consistentes e lógicas.',
        backstory='Você é um especialista em worldbuilding que odeia furos de roteiro e sistemas de magia mal explicados.',
        llm=llm,
        verbose=True
    )

    agente_mercado = Agent(
        role='Analista Literário',
        goal='Avaliar se a premissa é interessante para o público atual.',
        backstory='Você é um editor sênior de uma grande editora. Você sabe o que vende e o que é clichê.',
        llm=llm,
        verbose=True
    )

    # 2. Tarefas
    task_logica = Task(
        description=f"""
        Analise o seguinte resumo de universo do projeto '{titulo_projeto}':
        "{resumo_universo}"
        
        Identifique:
        1. Pontos onde a lógica do mundo parece falhar ou se contradizer.
        2. Perguntas que o autor precisa responder para solidificar o mundo.
        """,
        agent=agente_logica,
        expected_output="Uma lista de furos de lógica e perguntas críticas."
    )

    task_mercado = Task(
        description=f"""
        Com base na análise do Arquiteto, dê um veredito sobre o potencial comercial e a originalidade dessa premissa.
        Destaque os pontos fortes e os clichês que devem ser evitados.
        """,
        agent=agente_mercado,
        expected_output="Um relatório de viabilidade literária e originalidade."
    )

    # 3. Crew
    crew = Crew(
        agents=[agente_logica, agente_mercado],
        tasks=[task_logica, task_mercado],
        process=Process.sequential
    )

    return crew.kickoff()

# ==========================================================
# ✍️ EQUIPE 2: VALIDAÇÃO DE MICRO (CAPÍTULO/CENA)
# ==========================================================
def rodar_equipe_micro(texto_capitulo, contexto_macro):
    llm = get_llm()
    
    # 1. Agentes
    agente_continuidade = Agent(
        role='Fiscal de Continuidade',
        goal='Garantir que o capítulo respeite as regras definidas no Macro.',
        backstory='Você é obcecado por detalhes. Se o autor disse no Macro que a gravidade é invertida, você vai reclamar se alguém derrubar um copo e ele cair no chão.',
        llm=llm
    )

    agente_prosa = Agent(
        role='Crítico de Estilo',
        goal='Melhorar a qualidade da escrita, diálogos e descrições.',
        backstory='Você é um crítico literário exigente. Você odeia advérbios em excesso e diálogos robóticos.',
        llm=llm
    )

    # 2. Tarefas
    task_verificacao = Task(
        description=f"""
        CONTEXTO DO MUNDO (REGRAS): "{contexto_macro}"
        
        TEXTO DO CAPÍTULO: "{texto_capitulo}"
        
        Analise se o texto respeita as regras do mundo. Aponte contradições diretas.
        """,
        agent=agente_continuidade,
        expected_output="Relatório de erros de continuidade."
    )

    task_estilo = Task(
        description="Analise o texto focando no ritmo, diálogo e 'Show, Don't Tell'. Dê sugestões de reescrita para 2 parágrafos.",
        agent=agente_prosa,
        expected_output="Crítica de estilo e sugestões de melhoria."
    )

    # 3. Crew
    crew = Crew(
        agents=[agente_continuidade, agente_prosa],
        tasks=[task_verificacao, task_estilo],
        process=Process.sequential
    )

    return crew.kickoff()
