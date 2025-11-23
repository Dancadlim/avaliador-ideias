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
    if not my_llm: return "Erro: Chave de API não configurada."

    # Especialistas
    ag_logica = Agent(role='Crítico Estrutural', goal='Identificar furos de roteiro.', backstory='Editor chato. Odeia Deus Ex Machina.', llm=my_llm, verbose=True)
    ag_psico = Agent(role='Psicólogo de Personagens', goal='Avaliar motivações.', backstory='Analisa profundidade emocional.', llm=my_llm, verbose=True)
    ag_mercado = Agent(role='Agente Literário', goal='Avaliar potencial de venda.', backstory='Focado em best-sellers.', llm=my_llm, verbose=True)
    
    # O CHEFE (NOVO)
    ag_editor_chefe = Agent(role='Editor Chefe Sênior', goal='Consolidar todos os relatórios.', backstory='Você organiza o feedback em um plano de ação claro para o autor.', llm=my_llm, verbose=True)

    # Tarefas
    t_logica = Task(description=f"Universo: '{resumo_universo}'. Aponte furos de lógica.", expected_output="Lista de inconsistências.", agent=ag_logica)
    t_psico = Task(description="Analise a motivação dos personagens.", expected_output="Análise psicológica.", agent=ag_psico)
    t_mercado = Task(description="Potencial comercial e nota 0-10.", expected_output="Veredito comercial.", agent=ag_mercado)
    
    # Tarefa de Consolidação (NOVA)
    t_consolida = Task(
        description="Reúna as críticas de Lógica, Psicologia e Mercado. Crie um Relatório Final formatado em Markdown com: 1. Resumo Executivo, 2. Pontos Fortes, 3. Pontos Fracos Críticos, 4. Veredito Final.",
        expected_output="Relatório Final Consolidado.",
        agent=ag_editor_chefe,
        context=[t_logica, t_psico, t_mercado] # Importante: Lê o output dos anteriores
    )

    crew = Crew(agents=[ag_logica, ag_psico, ag_mercado, ag_editor_chefe], tasks=[t_logica, t_psico, t_mercado, t_consolida], process=Process.sequential)
    return crew.kickoff()

def rodar_equipe_micro(texto_capitulo, contexto_macro):
    my_llm = get_llm()
    if not my_llm: return "Erro: Chave de API não encontrada."

    ag_cont = Agent(role='Fiscal de Continuidade', goal='Garantir regras do mundo.', backstory='Você briga se quebrar regras mágicas.', llm=my_llm, verbose=True)
    ag_editor = Agent(role='Editor de Texto', goal='Melhorar prosa.', backstory='Mestre em descrições.', llm=my_llm, verbose=True)
    ag_hater = Agent(role='Leitor Cínico', goal='Apontar tédio.', backstory='Brutalmente honesto.', llm=my_llm, verbose=True)
    
    # O CHEFE (NOVO)
    ag_revisor = Agent(role='Revisor Final', goal='Criar um guia de reescrita.', backstory='Você diz exatamente o que o autor deve mudar no texto.', llm=my_llm, verbose=True)

    t_cont = Task(description=f"Contexto: {contexto_macro}. Texto: {texto_capitulo}. Erros de continuidade?", expected_output="Relatório continuidade.", agent=ag_cont)
    t_editor = Task(description="Melhore a prosa e ritmo.", expected_output="Crítica técnica.", agent=ag_editor)
    t_hater = Task(description="O que está chato ou brega?", expected_output="Crítica ácida.", agent=ag_hater)
    
    t_consolida = Task(
        description="Baseado na continuidade, estilo e críticas ácidas, crie um 'Guia de Reescrita' passo a passo para este capítulo.",
        expected_output="Guia de Reescrita Consolidado.",
        agent=ag_revisor,
        context=[t_cont, t_editor, t_hater]
    )

    crew = Crew(agents=[ag_cont, ag_editor, ag_hater, ag_revisor], tasks=[t_cont, t_editor, t_hater, t_consolida], process=Process.sequential)
    return crew.kickoff()


# ==========================================================
# 💻 DOMÍNIO 2: PROJETOS DIGITAIS (APPS/SITES)
# ==========================================================

def rodar_equipe_negocio_macro(resumo_negocio, titulo):
    my_llm = get_llm()
    if not my_llm: return "Erro: Chave de API não configurada."

    ag_cfo = Agent(role='CFO Estrategista', goal='Avaliar lucro.', backstory='Focado em números.', llm=my_llm, verbose=True)
    ag_produto = Agent(role='Diretor de Produto', goal='Validar dor do cliente.', backstory='Usa Canvas.', llm=my_llm, verbose=True)
    ag_legal = Agent(role='Consultor Jurídico', goal='Riscos legais.', backstory='Verifica leis.', llm=my_llm, verbose=True)
    
    # O CHEFE (NOVO)
    ag_ceo = Agent(role='CEO Interino', goal='Decidir se investe ou não.', backstory='Você consolida tudo e dá o Go/No-Go.', llm=my_llm, verbose=True)

    t_cfo = Task(description=f"Ideia: '{titulo}' - '{resumo_negocio}'. Modelos de receita?", expected_output="Análise financeira.", agent=ag_cfo)
    t_prod = Task(description="Product-Market Fit?", expected_output="Validação de mercado.", agent=ag_produto)
    t_legal = Task(description="Riscos legais?", expected_output="Parecer jurídico.", agent=ag_legal)
    
    t_consolida = Task(
        description="Como CEO, leia os relatórios Financeiro, Produto e Legal. Crie um 'Sumário Executivo' e decida se o projeto é viável.",
        expected_output="Sumário Executivo e Decisão de Investimento.",
        agent=ag_ceo,
        context=[t_cfo, t_prod, t_legal]
    )

    crew = Crew(agents=[ag_cfo, ag_produto, ag_legal, ag_ceo], tasks=[t_cfo, t_prod, t_legal, t_consolida], process=Process.sequential)
    return crew.kickoff()

def rodar_equipe_negocio_micro(detalhes_tecnicos, contexto_macro):
    my_llm = get_llm()
    if not my_llm: return "Erro: Chave de API não configurada."

    ag_ux = Agent(role='UX Designer', goal='Criticar jornada.', backstory='Defende o usuário.', llm=my_llm, verbose=True)
    ag_qa = Agent(role='Engenheiro QA', goal='Achar falhas.', backstory='Pensa como quebra.', llm=my_llm, verbose=True)
    ag_etica = Agent(role='Auditor Ético', goal='Garantir inclusão.', backstory='Verifica viés.', llm=my_llm, verbose=True)
    
    # O CHEFE (NOVO)
    ag_pm = Agent(role='Project Manager Técnico', goal='Criar backlog de correções.', backstory='Transforma problemas em tarefas.', llm=my_llm, verbose=True)

    t_ux = Task(description=f"Contexto: {contexto_macro}. Detalhes: '{detalhes_tecnicos}'. Crítica UX.", expected_output="Crítica UX.", agent=ag_ux)
    t_qa = Task(description="Riscos técnicos?", expected_output="Relatório riscos.", agent=ag_qa)
    t_etica = Task(description="Problemas éticos?", expected_output="Parecer ético.", agent=ag_etica)
    
    t_consolida = Task(
        description="Reúna os problemas de UX, QA e Ética. Crie uma lista priorizada de correções técnicas para o time de desenvolvimento.",
        expected_output="Backlog de Correções Priorizado.",
        agent=ag_pm,
        context=[t_ux, t_qa, t_etica]
    )

    crew = Crew(agents=[ag_ux, ag_qa, ag_etica, ag_pm], tasks=[t_ux, t_qa, t_etica, t_consolida], process=Process.sequential)
    return crew.kickoff()


# ==========================================================
# 🏗️ DOMÍNIO 3: EMPREENDIMENTOS FÍSICOS (OBRAS/LOJAS)
# ==========================================================

def rodar_equipe_fisico_macro(resumo_obra, titulo):
    my_llm = get_llm()
    if not my_llm: return "Erro."

    ag_incorp = Agent(role='Incorporador', goal='Avaliar ROI.', backstory='Focado em retorno.', llm=my_llm, verbose=True)
    ag_ops = Agent(role='Estrategista Ops', goal='Validar logística.', backstory='Focado em fluxo.', llm=my_llm, verbose=True)
    ag_legal = Agent(role='Advogado Imobiliário', goal='Verificar zoneamento.', backstory='Leis e alvarás.', llm=my_llm, verbose=True)
    
    # O CHEFE (NOVO)
    ag_diretor = Agent(role='Diretor de Novos Negócios', goal='Aprovar a compra do terreno.', backstory='Analisa risco x retorno global.', llm=my_llm, verbose=True)

    t_incorp = Task(description=f"Empreendimento: '{titulo}'. Resumo: '{resumo_obra}'. Viabilidade?", expected_output="Análise imobiliária.", agent=ag_incorp)
    t_ops = Task(description="Logística macro?", expected_output="Análise operacional.", agent=ag_ops)
    t_legal = Task(description="Licenças necessárias?", expected_output="Parecer legal.", agent=ag_legal)
    
    t_consolida = Task(
        description="Consolide a visão Imobiliária, Operacional e Legal. O terreno/ponto deve ser adquirido? Quais os maiores riscos?",
        expected_output="Parecer de Viabilidade de Empreendimento.",
        agent=ag_diretor,
        context=[t_incorp, t_ops, t_legal]
    )

    crew = Crew(agents=[ag_incorp, ag_ops, ag_legal, ag_diretor], tasks=[t_incorp, t_ops, t_legal, t_consolida], process=Process.sequential)
    return crew.kickoff()

def rodar_equipe_fisico_micro(planta_detalhes, contexto_macro):
    my_llm = get_llm()
    if not my_llm: return "Erro: Chave de API não configurada."

    ag_xp = Agent(role='Arquiteto XP', goal='Criticar conforto.', backstory='Acústica e luz.', llm=my_llm, verbose=True)
    ag_fiscal = Agent(role='Consultor Normas', goal='Evitar multas.', backstory='Bombeiros e ANVISA.', llm=my_llm, verbose=True)
    ag_rh = Agent(role='Gerente RH', goal='Vida do funcionário.', backstory='Ergonomia.', llm=my_llm, verbose=True)
    
    # O CHEFE (NOVO)
    ag_gerente = Agent(role='Gerente Geral', goal='Preparar a inauguração.', backstory='Garante que a operação vai rodar liso.', llm=my_llm, verbose=True)

    t_xp = Task(description=f"Contexto: {contexto_macro}. Detalhes: '{planta_detalhes}'. Crítica sensorial.", expected_output="Crítica sensorial.", agent=ag_xp)
    t_fiscal = Task(description="Riscos legais físicos?", expected_output="Relatório normas.", agent=ag_fiscal)
    t_rh = Task(description="Ambiente salubre?", expected_output="Parecer RH.", agent=ag_rh)
    
    t_consolida = Task(
        description="Baseado na Experiência, Normas e RH, crie um 'Manual de Ajustes Operacionais' antes da inauguração.",
        expected_output="Manual de Ajustes Operacionais.",
        agent=ag_gerente,
        context=[t_xp, t_fiscal, t_rh]
    )

    crew = Crew(agents=[ag_xp, ag_fiscal, ag_rh, ag_gerente], tasks=[t_xp, t_fiscal, t_rh, t_consolida], process=Process.sequential)
    return crew.kickoff()
