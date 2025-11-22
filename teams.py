import os
import streamlit as st
from crewai import Agent, Task, Crew, Process, LLM

# --- CONFIGURAÇÃO DO CÉREBRO ---
def get_llm():
    if "google" in st.secrets:
        api_key = st.secrets["google"]["api_key"]
        os.environ["GOOGLE_API_KEY"] = api_key
        return LLM(
            model="gemini/gemini-2.5-flash",
            api_key=api_key,
            temperature=0.7
        )
    return None

# ==========================================================
# 📚 DOMÍNIO: HISTÓRIA (LIVROS/ROTEIROS)
# ==========================================================

# --- MACRO (O MUNDO E A LÓGICA) ---
def rodar_equipe_macro(resumo_universo, titulo_projeto):
    my_llm = get_llm()
    if not my_llm: return "Erro: Chave de API não configurada."

    # 1. O Crítico Estrutural
    ag_logica = Agent(
        role='Crítico Estrutural de Narrativa',
        goal='Identificar furos de roteiro e inconsistências no mundo.',
        backstory='Você é um editor chato. Se a magia precisa de água, você questiona por que eles vivem no deserto. Você odeia "Deus Ex Machina".',
        llm=my_llm, verbose=True
    )

    # 2. O Psicólogo de Personagens
    ag_psico = Agent(
        role='Psicólogo de Personagens',
        goal='Avaliar as motivações e arcos dos protagonistas e vilões.',
        backstory='Você analisa se as ações dos personagens fazem sentido com suas histórias de vida. Você busca profundidade emocional.',
        llm=my_llm, verbose=True
    )

    # 3. O Agente de Mercado
    ag_mercado = Agent(
        role='Agente Literário Comercial',
        goal='Avaliar o potencial de venda e o "gancho" da história.',
        backstory='Você só se importa se o livro vai vender. Você conhece os clichês que funcionam e os que cansam o público.',
        llm=my_llm, verbose=True
    )

    # Tarefas
    t_logica = Task(
        description=f"Analise o universo de '{titulo_projeto}': '{resumo_universo}'. Aponte 3 furos graves na lógica ou regras do mundo.",
        expected_output="Lista de inconsistências lógicas.",
        agent=ag_logica
    )
    t_psico = Task(
        description=f"Analise os personagens descritos. Suas motivações sustentam uma história longa? O vilão é crível?",
        expected_output="Análise psicológica dos personagens.",
        agent=ag_psico
    )
    t_mercado = Task(
        description=f"Essa premissa é original ou genérica? Tem apelo comercial? Dê uma nota de 0 a 10 para o potencial de venda.",
        expected_output="Veredito comercial e nota.",
        agent=ag_mercado
    )

    crew = Crew(agents=[ag_logica, ag_psico, ag_mercado], tasks=[t_logica, t_psico, t_mercado], process=Process.sequential)
    return crew.kickoff()

# --- MICRO (A CENA E A ESCRITA) ---
def rodar_equipe_micro(texto_capitulo, contexto_macro):
    my_llm = get_llm()
    if not my_llm: return "Erro: Chave de API não configurada."

    # 1. O Fiscal de Continuidade
    ag_cont = Agent(
        role='Fiscal de Continuidade',
        goal='Garantir que o texto respeite as regras do Macro.',
        backstory='Você lê o contexto do mundo e briga se o autor mudar a cor do olho do herói ou quebrar uma regra mágica.',
        llm=my_llm, verbose=True
    )

    # 2. O Editor de Texto (Técnico)
    ag_editor = Agent(
        role='Editor de Texto Sênior',
        goal='Melhorar a prosa, ritmo e eliminar vícios de linguagem.',
        backstory='Você odeia advérbios, repetições e frases passivas. Seu foco é fluidez e clareza.',
        llm=my_llm, verbose=True
    )

    # 3. O Hater (Leitor Cínico)
    ag_hater = Agent(
        role='Leitor Cínico (O Hater)',
        goal='Apontar diálogos bregas, tédio e vergonha alheia.',
        backstory='Você é aquele leitor que deixa review de 1 estrela. Você não tem pena. Fale na cara o que está ruim/chato.',
        llm=my_llm, verbose=True
    )

    # Tarefas
    t_cont = Task(
        description=f"CONTEXTO MACRO: {contexto_macro}\nTEXTO: {texto_capitulo}\nO texto respeita as regras? Há erros de continuidade?",
        expected_output="Relatório de continuidade.",
        agent=ag_cont
    )
    t_editor = Task(
        description="Analise a prosa. O ritmo está bom? O 'Show, Don't Tell' foi usado? Reescreva o pior parágrafo.",
        expected_output="Crítica técnica e reescrita.",
        agent=ag_editor
    )
    t_hater = Task(
        description="O que está chato, brega ou forçado nessa cena? Seja brutalmente honesto.",
        expected_output="Crítica ácida e pontos fracos.",
        agent=ag_hater
    )

    crew = Crew(agents=[ag_cont, ag_editor, ag_hater], tasks=[t_cont, t_editor, t_hater], process=Process.sequential)
    return crew.kickoff()


# ==========================================================
# 💼 DOMÍNIO: PROJETOS & EMPREENDIMENTOS
# ==========================================================

# --- MACRO (ESTRATÉGIA DE NEGÓCIO) ---
def rodar_equipe_negocio_macro(resumo_negocio, titulo):
    my_llm = get_llm()
    if not my_llm: return "Erro: Chave de API não configurada."

    # 1. O Investidor (CFO)
    ag_cfo = Agent(
        role='Investidor Anjo Cético',
        goal='Validar se o negócio dá dinheiro.',
        backstory='Você quer saber o ROI. Como monetiza? Qual o custo? Você ignora "sonhos" e foca em números.',
        llm=my_llm, verbose=True
    )

    # 2. O Estrategista de Produto
    ag_produto = Agent(
        role='Diretor de Produto',
        goal='Validar a dor do cliente e a solução.',
        backstory='Você usa frameworks como Canvas e Lean Startup. O problema é real ou imaginário?',
        llm=my_llm, verbose=True
    )

    # 3. O Advogado (Risco Macro)
    ag_legal = Agent(
        role='Consultor Jurídico Estratégico',
        goal='Identificar barreiras legais ou regulatórias graves.',
        backstory='Você verifica se a ideia é legal, se precisa de patentes ou se vai ser processada na primeira semana.',
        llm=my_llm, verbose=True
    )

    # Tarefas
    t_cfo = Task(
        description=f"Ideia: '{titulo}' - '{resumo_negocio}'. Liste 3 modelos de receita e os maiores riscos financeiros.",
        expected_output="Análise financeira e de monetização.",
        agent=ag_cfo
    )
    t_prod = Task(
        description="Quem é a persona? A dor é aguda? A solução resolve? Critique o Product-Market Fit.",
        expected_output="Validação de produto e mercado.",
        agent=ag_produto
    )
    t_legal = Task(
        description="Existem riscos regulatórios, de patente ou criminal nessa ideia macro?",
        expected_output="Parecer jurídico preliminar.",
        agent=ag_legal
    )

    crew = Crew(agents=[ag_cfo, ag_produto, ag_legal], tasks=[t_cfo, t_prod, t_legal], process=Process.sequential)
    return crew.kickoff()

# --- MICRO (EXECUÇÃO E TÉCNICO) ---
def rodar_equipe_negocio_micro(detalhes_tecnicos, contexto_macro):
    my_llm = get_llm()
    if not my_llm: return "Erro: Chave de API não configurada."

    # 1. O UX Tester (O Usuário)
    ag_ux = Agent(
        role='Especialista em UX/UI',
        goal='Criticar a jornada do usuário.',
        backstory='Você defende o usuário. Se for difícil de usar, você reclama. Você odeia processos longos.',
        llm=my_llm, verbose=True
    )

    # 2. O Engenheiro de Risco (QA/Tech)
    ag_qa = Agent(
        role='Engenheiro de Sistemas e QA',
        goal='Achar falhas técnicas e de segurança.',
        backstory='Você pensa em como o sistema vai quebrar. E se a internet cair? E se hackearem?',
        llm=my_llm, verbose=True
    )

    # 3. O Auditor Ético
    ag_etica = Agent(
        role='Auditor de Ética e Compliance',
        goal='Garantir que a execução seja justa e inclusiva.',
        backstory='Você verifica viés, acessibilidade e impacto social negativo da implementação.',
        llm=my_llm, verbose=True
    )

    # Tarefas
    t_ux = Task(
        description=f"Contexto Macro: {contexto_macro}. Detalhes Micro: '{detalhes_tecnicos}'. Analise a jornada. Onde o usuário desiste?",
        expected_output="Crítica de usabilidade.",
        agent=ag_ux
    )
    t_qa = Task(
        description="Quais são os riscos técnicos, de segurança ou bugs lógicos nessa implementação?",
        expected_output="Relatório de riscos técnicos.",
        agent=ag_qa
    )
    t_etica = Task(
        description="Essa implementação exclui alguém? Cria vícios? Viola privacidade?",
        expected_output="Parecer ético.",
        agent=ag_etica
    )

    crew = Crew(agents=[ag_ux, ag_qa, ag_etica], tasks=[t_ux, t_qa, t_etica], process=Process.sequential)
    return crew.kickoff()
