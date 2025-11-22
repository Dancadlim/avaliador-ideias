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
            model="gemini/gemini-2.5-flash",
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

# ==========================================================
# 💼 PROJETOS: MACRO (ESTRATÉGIA DE NEGÓCIO)
# ==========================================================
def rodar_equipe_negocio_macro(resumo_negocio, titulo):
    my_llm = get_llm()
    if not my_llm: return "Erro: Chave de API não configurada."

    # 1. Agentes (Foco em Dinheiro e Produto)
    ag_financeiro = Agent(
        role='CFO Estrategista',
        goal='Avaliar viabilidade financeira e modelos de receita.',
        backstory='Especialista em startups e monetização. Focado em lucro.',
        llm=my_llm, verbose=True
    )
    ag_produto = Agent(
        role='Gerente de Produto',
        goal='Validar o "Product-Market Fit" e a utilidade real.',
        backstory='Focado na dor do cliente e na solução.',
        llm=my_llm, verbose=True
    )

    # 2. Tarefas
    task_fin = Task(
        description=f"Analise a ideia '{titulo}': '{resumo_negocio}'. Liste 3 formas de monetizar e os maiores custos iniciais.",
        expected_output="Relatório financeiro resumido.",
        agent=ag_financeiro
    )
    task_prod = Task(
        description=f"Quem é o usuário dessa ideia? O problema é real? A solução faz sentido?",
        expected_output="Análise de produto e público-alvo.",
        agent=ag_produto
    )

    crew = Crew(
        agents=[ag_financeiro, ag_produto],
        tasks=[task_fin, task_prod],
        process=Process.sequential
    )
    return crew.kickoff()

# ==========================================================
# ⚙️ PROJETOS: MICRO (EXECUÇÃO E RISCO)
# ==========================================================
def rodar_equipe_negocio_micro(detalhes_tecnicos, contexto_macro):
    my_llm = get_llm()
    if not my_llm: return "Erro: Chave de API não configurada."

    # 1. Agentes (Foco em Risco e Usabilidade)
    ag_ux = Agent(
        role='UX Designer Sênior',
        goal='Garantir que a experiência do usuário seja fluida.',
        backstory='Especialista em jornada do usuário e acessibilidade.',
        llm=my_llm, verbose=True
    )
    ag_risco = Agent(
        role='Analista de Risco e Legal',
        goal='Identificar falhas de segurança, problemas legais (LGPD) e éticos.',
        backstory='Advogado e Engenheiro de QA. O "Hater" profissional.',
        llm=my_llm, verbose=True
    )

    # 2. Tarefas
    task_ux = Task(
        description=f"Contexto Macro: {contexto_macro}. Detalhes Técnicos: '{detalhes_tecnicos}'. A jornada do usuário faz sentido? Onde ele vai travar?",
        expected_output="Crítica de UX e usabilidade.",
        agent=ag_ux
    )
    task_risk = Task(
        description=f"Analise riscos legais (dados, direitos) e técnicos. O que pode dar errado?",
        expected_output="Relatório de riscos e bandeiras vermelhas.",
        agent=ag_risco
    )

    crew = Crew(
        agents=[ag_ux, ag_risco],
        tasks=[task_ux, task_risk],
        process=Process.sequential
    )
    return crew.kickoff()
