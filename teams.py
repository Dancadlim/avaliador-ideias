import os
import streamlit as st
from crewai import Agent, Task, Crew, Process, LLM

# --- CONFIGURAÇÃO DO CÉREBRO (SINTAXE NOVA QUE FUNCIONOU) ---
def get_llm():
    if "google" in st.secrets:
        api_key = st.secrets["google"]["api_key"]
        
        # O CrewAI precisa da chave no ambiente para o LiteLLM funcionar
        os.environ["GOOGLE_API_KEY"] = api_key
        
        # Retorna o LLM nativo
        # Nota: 'gemini/gemini-1.5-flash' indica provedor/modelo
        return LLM(
            model="gemini/gemini-1.5-flash",
            temperature=0.7
        )
    return None

# ==========================================================
# 🌍 EQUIPE 1: MACRO (O MUNDO)
# ==========================================================
def rodar_equipe_macro(resumo_universo, titulo_projeto):
    my_llm = get_llm()
    if not my_llm: return "Erro: Chave de API não encontrada."

    # Agente 1: O Lógico
    agente_logica = Agent(
        role='Arquiteto de Lore',
        goal='Validar a consistência do mundo.',
        backstory='Especialista em encontrar furos de roteiro.',
        llm=my_llm,
        verbose=True
    )

    # Agente 2: O Vendedor
    agente_mercado = Agent(
        role='Analista de Mercado Literário',
        goal='Avaliar o potencial comercial.',
        backstory='Editor sênior focado em best-sellers.',
        llm=my_llm,
        verbose=True
    )

    task_logica = Task(
        description=f"Analise a lógica deste mundo: '{resumo_universo}'. Aponte 3 furos principais.",
        expected_output="Lista de furos de lógica.",
        agent=agente_logica
    )

    task_mercado = Task(
        description=f"Baseado na análise anterior, esse livro '{titulo_projeto}' venderia? Por que?",
        expected_output="Parecer comercial curto.",
        agent=agente_mercado
    )

    crew = Crew(
        agents=[agente_logica, agente_mercado],
        tasks=[task_logica, task_mercado],
        process=Process.sequential
    )

    return crew.kickoff()

# ==========================================================
# ✍️ EQUIPE 2: MICRO (A ESCRITA)
# ==========================================================
def rodar_equipe_micro(texto_capitulo, contexto_macro):
    my_llm = get_llm()
    if not my_llm: return "Erro: Chave de API não encontrada."

    # Agente 1: Continuidade
    agente_continuidade = Agent(
        role='Fiscal de Continuidade',
        goal='Verificar se o texto segue as regras do mundo.',
        backstory='Você garante que a magia e as regras não mudem do nada.',
        llm=my_llm,
        verbose=True
    )

    # Agente 2: Estilo
    agente_estilo = Agent(
        role='Editor de Texto',
        goal='Melhorar a prosa.',
        backstory='Crítico literário focado em fluidez.',
        llm=my_llm,
        verbose=True
    )

    task_cont = Task(
        description=f"Regras do Mundo: {contexto_macro}. Texto: {texto_capitulo}. Há contradições?",
        expected_output="Relatório de continuidade.",
        agent=agente_continuidade
    )

    task_estilo = Task(
        description="Melhore o estilo desse texto. Dê 3 sugestões de reescrita.",
        expected_output="Sugestões de estilo.",
        agent=agente_estilo
    )

    crew = Crew(
        agents=[agente_continuidade, agente_estilo],
        tasks=[task_cont, task_estilo],
        process=Process.sequential
    )

    return crew.kickoff()
