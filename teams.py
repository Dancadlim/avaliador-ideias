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
# 📚 DOMÍNIO 1: HISTÓRIA (LIVROS/ROTEIROS)
# ==========================================================

def rodar_equipe_macro(resumo_universo, titulo_projeto):
    my_llm = get_llm()
    if not my_llm: return "Erro: Chave de API não encontrada."

    ag_logica = Agent(role='Crítico Estrutural', goal='Identificar furos de roteiro.', backstory='Editor chato. Odeia Deus Ex Machina.', llm=my_llm, verbose=True)
    ag_psico = Agent(role='Psicólogo de Personagens', goal='Avaliar motivações.', backstory='Analisa profundidade emocional.', llm=my_llm, verbose=True)
    ag_mercado = Agent(role='Agente Literário', goal='Avaliar potencial de venda.', backstory='Focado em best-sellers.', llm=my_llm, verbose=True)

    t_logica = Task(description=f"Universo: '{resumo_universo}'. Aponte furos de lógica.", expected_output="Lista de inconsistências.", agent=ag_logica)
    t_psico = Task(description="Analise a motivação dos personagens.", expected_output="Análise psicológica.", agent=ag_psico)
    t_mercado = Task(description="Potencial comercial e nota 0-10.", expected_output="Veredito comercial.", agent=ag_mercado)

    crew = Crew(agents=[ag_logica, ag_psico, ag_mercado], tasks=[t_logica, t_psico, t_mercado], process=Process.sequential)
    return crew.kickoff()

def rodar_equipe_micro(texto_capitulo, contexto_macro):
    my_llm = get_llm()
    if not my_llm: return "Erro: Chave de API não encontrada."

    ag_cont = Agent(role='Fiscal de Continuidade', goal='Garantir regras do mundo.', backstory='Você briga se quebrar regras mágicas.', llm=my_llm, verbose=True)
    ag_editor = Agent(role='Editor de Texto', goal='Melhorar prosa.', backstory='Mestre em descrições.', llm=my_llm, verbose=True)
    ag_hater = Agent(role='Leitor Cínico', goal='Apontar tédio.', backstory='Deixa review de 1 estrela. Brutalmente honesto.', llm=my_llm, verbose=True)

    t_cont = Task(description=f"Contexto: {contexto_macro}. Texto: {texto_capitulo}. Erros de continuidade?", expected_output="Relatório continuidade.", agent=ag_cont)
    t_editor = Task(description="Melhore a prosa e ritmo.", expected_output="Crítica técnica.", agent=ag_editor)
    t_hater = Task(description="O que está chato ou brega?", expected_output="Crítica ácida.", agent=ag_hater)

    crew = Crew(agents=[ag_cont, ag_editor, ag_hater], tasks=[t_cont, t_editor, t_hater], process=Process.sequential)
    return crew.kickoff()

# ==========================================================
# 💻 DOMÍNIO 2: PROJETOS DIGITAIS (APPS/SITES)
# ==========================================================

def rodar_equipe_negocio_macro(resumo_negocio, titulo):
    my_llm = get_llm()
    if not my_llm: return "Erro: Chave de API não configurada."

    ag_cfo = Agent(role='CFO Estrategista', goal='Avaliar lucro.', backstory='Especialista em monetização. Focado em números.', llm=my_llm, verbose=True)
    ag_produto = Agent(role='Diretor de Produto', goal='Validar dor do cliente.', backstory='Usa Canvas e Lean Startup.', llm=my_llm, verbose=True)
    ag_legal = Agent(role='Consultor Jurídico', goal='Riscos legais.', backstory='Verifica patentes e leis.', llm=my_llm, verbose=True)

    t_cfo = Task(description=f"Ideia: '{titulo}' - '{resumo_negocio}'. Modelos de receita e riscos financeiros.", expected_output="Análise financeira.", agent=ag_cfo)
    t_prod = Task(description="Product-Market Fit. O problema é real?", expected_output="Validação de mercado.", agent=ag_produto)
    t_legal = Task(description="Riscos regulatórios ou criminais?", expected_output="Parecer jurídico.", agent=ag_legal)

    crew = Crew(agents=[ag_cfo, ag_produto, ag_legal], tasks=[t_cfo, t_prod, t_legal], process=Process.sequential)
    return crew.kickoff()

def rodar_equipe_negocio_micro(detalhes_tecnicos, contexto_macro):
    my_llm = get_llm()
    if not my_llm: return "Erro: Chave de API não configurada."

    ag_ux = Agent(role='UX Designer', goal='Criticar jornada.', backstory='Defende o usuário. Odeia processos difíceis.', llm=my_llm, verbose=True)
    ag_qa = Agent(role='Engenheiro QA', goal='Achar falhas.', backstory='Pensa como o sistema quebra.', llm=my_llm, verbose=True)
    ag_etica = Agent(role='Auditor Ético', goal='Garantir inclusão.', backstory='Verifica viés e privacidade.', llm=my_llm, verbose=True)

    t_ux = Task(description=f"Contexto: {contexto_macro}. Detalhes: '{detalhes_tecnicos}'. Analise a jornada.", expected_output="Crítica UX.", agent=ag_ux)
    t_qa = Task(description="Riscos técnicos e bugs lógicos?", expected_output="Relatório riscos.", agent=ag_qa)
    t_etica = Task(description="Exclui alguém? Cria vícios?", expected_output="Parecer ético.", agent=ag_etica)

    crew = Crew(agents=[ag_ux, ag_qa, ag_etica], tasks=[t_ux, t_qa, t_etica], process=Process.sequential)
    return crew.kickoff()

# ==========================================================
# 🏗️ DOMÍNIO 3: EMPREENDIMENTOS FÍSICOS (OBRAS/LOJAS)
# ==========================================================

def rodar_equipe_fisico_macro(resumo_obra, titulo):
    my_llm = get_llm()
    if not my_llm: return "Erro."

    # Agente 1: O Incorporador (Dinheiro e Ponto)
    ag_incorp = Agent(
        role='Incorporador Imobiliário',
        goal='Avaliar viabilidade do ponto e ROI.',
        backstory='Você só pensa em localização e retorno. O bairro comporta esse negócio? O aluguel se paga?',
        llm=my_llm, verbose=True
    )
    # Agente 2: O Logístico (Operação Macro)
    ag_ops = Agent(
        role='Estrategista de Operações',
        goal='Validar o fluxo logístico macro.',
        backstory='Você pensa em fornecedores, estoque e fluxo de carga. A conta fecha na operação?',
        llm=my_llm, verbose=True
    )

    t_incorp = Task(description=f"Empreendimento: '{titulo}'. Resumo: '{resumo_obra}'. O ponto/ideia é viável financeiramente?", expected_output="Análise de viabilidade imobiliária.", agent=ag_incorp)
    t_ops = Task(description="Como seria a logística macro? Riscos de operação?", expected_output="Análise operacional.", agent=ag_ops)

    crew = Crew(agents=[ag_incorp, ag_ops], tasks=[t_incorp, t_ops], process=Process.sequential)
    return crew.kickoff()

def rodar_equipe_fisico_micro(planta_detalhes, contexto_macro):
    my_llm = get_llm()
    if not my_llm: return "Erro."

    # Agente 1: O Sensorial (Cliente)
    ag_xp = Agent(
        role='Arquiteto de Experiência',
        goal='Criticar o conforto e os 5 sentidos.',
        backstory='Você avalia acústica, iluminação, cheiro e conforto físico. O cliente vai se sentir bem?',
        llm=my_llm, verbose=True
    )
    # Agente 2: O Fiscal (Regras)
    ag_fiscal = Agent(
        role='Consultor de Alvará e Normas',
        goal='Evitar multas e interdições.',
        backstory='Você conhece leis de bombeiro, vigilância sanitária e acessibilidade. Acha problemas na planta.',
        llm=my_llm, verbose=True
    )

    t_xp = Task(description=f"Contexto: {contexto_macro}. Detalhes: '{planta_detalhes}'. O ambiente é agradável? Onde o cliente sofre?", expected_output="Crítica sensorial.", agent=ag_xp)
    t_fiscal = Task(description="Riscos de segurança, acessibilidade ou legalidade física?", expected_output="Relatório de conformidade.", agent=ag_fiscal)

    crew = Crew(agents=[ag_xp, ag_fiscal], tasks=[t_xp, t_fiscal], process=Process.sequential)
    return crew.kickoff()
