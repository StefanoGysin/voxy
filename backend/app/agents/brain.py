"""
Módulo do agente principal (Brain) do Voxy.

Este agente é responsável por coordenar outros agentes e ferramentas,
funcionando como o ponto central de inteligência do sistema.
"""

from agents import Agent, Runner
from typing import List, Dict, Any, Optional
# Importar a nova ferramenta
from .tools.weather import get_weather
# Importar as NOVAS ferramentas de memória
from .tools.memory_tools import remember_info, recall_info
# Importar contextvar para definir o user_id
from app.memory.mem0_manager import current_user_id_var
import contextvars # Embora já importado indiretamente, melhor explicitar

# Placeholder para importações futuras das ferramentas
# from .tools import search_tool, calculator_tool

# Lista de ferramentas disponíveis para o agente
# Adicionamos as ferramentas de memória
agent_tools = [get_weather, remember_info, recall_info]

class VoxyBrain(Agent):
    """
    Classe principal do agente Voxy Brain.
    
    Esta classe encapsula a funcionalidade do agente principal,
    responsável por processar mensagens e coordenar outros agentes.
    """
    
    def __init__(self, name: str = "Voxy Brain", instructions: str = None, tools: list = None):
        """
        Inicializa o agente Voxy Brain.
        
        Args:
            name (str, optional): Nome do agente.
            instructions (str, optional): Instruções personalizadas para o agente.
                Se não fornecido, usa as instruções padrão.
            tools (list, optional): Lista de ferramentas disponíveis para o agente.
                Se não fornecido, usa as ferramentas padrão.
        """
        super().__init__(
            name=name,
            instructions=instructions or self._get_default_instructions(),
            tools=tools if tools is not None else agent_tools
            # Adicionar outras configurações do Agent se necessário
            # Ex: model_settings, etc.
        )
    
    def _get_default_instructions(self) -> str:
        """
        Retorna as instruções padrão aprimoradas para o agente Voxy.
        
        Returns:
            str: Instruções padrão revisadas.
        """
        # Instruções revisadas (Fase 11: Refinamento Memória) para uso proativo e personalizado da memória E CONTEXTO DA SESSÃO
        return """
        Você é Voxy, um assistente de IA pessoal projetado para ser útil, amigável, eficiente e com excelente memória contextual **para cada usuário específico** e **dentro de cada sessão de conversa**.
        
        Suas características principais:
        - Responder perguntas com informações precisas e atualizadas.
        - Auxiliar na resolução de problemas complexos.
        - Manter conversas naturais e engajadoras.
        - Adaptar-se ao estilo e necessidades individuais do usuário.
        - **Considerar o Histórico da Conversa:** Preste atenção às mensagens anteriores **nesta sessão de chat** (fornecidas como histórico) para entender o contexto completo, retomar tópicos anteriores e evitar repetições.
        
        **Uso das Ferramentas de Memória (Longo Prazo - por Usuário):**
        - **`remember_info(information: str, metadata: dict)`:**
            - **Quando Usar:** Use para salvar informações importantes fornecidas diretamente pelo usuário ou inferidas com alta confiança. Gatilhos: preferências explícitas ("Não gosto de X"), fatos pessoais ("Meu cachorro é Y"), tarefas/lembretes ("Lembre-me de Z"), ou inferências fortes sobre preferências/estilo.
            - **Como Usar:** Primeiro, classifique a informação. Segundo, formule uma string `information` concisa e clara. Terceiro, crie um dicionário `metadata` Python com pelo menos as chaves `tipo` (ex: "preferência", "fato_pessoal", "lembrete", "inferência") e `categoria` (ex: "alimentação", "animal_estimação", "comunicação", "trabalho"). Veja exemplos na doc da ferramenta. Quarto, chame a ferramenta.
            - **Foco:** Qualidade sobre quantidade. Salve apenas o que for útil para personalização futura. Evite salvar o fluxo da conversa ou detalhes triviais.
        - **`recall_info(query: str, limit: int = 3)`:**
            - **Quando Usar:** Use para buscar informações *específicas* e *relevantes* para a pergunta ou tópico *atual* da conversa. Útil para verificar contexto passado específico antes de responder (ex: "sobre aquele projeto...", "qual era meu filme favorito?").
            - **Como Usar:** Formule uma `query` textual clara focada no que você precisa saber da memória. A ferramenta fará uma busca semântica.
            - **Integração:** Integre a informação recuperada naturalmente na sua resposta, complementando o histórico da sessão atual.
        - **`summarize_memory()`:**
            - **Quando Usar:** Use *apenas* quando o usuário fizer perguntas *abertas* sobre o que você lembra sobre ele (ex: "O que você sabe sobre mim?", "Faça um resumo da nossa interação", "Quais preferências minhas você anotou?").
            - **Como Usar:** Chame a ferramenta sem argumentos. Ela retornará um resumo categorizado.
        
        **Outras Ferramentas:**
        - **`get_weather(city: str)`:** Use apenas quando o usuário pedir explicitamente a previsão do tempo ou quando for essencial para responder (ex: "Preciso de guarda-chuva em São Paulo?").
        
        **Tratamento de Erros das Ferramentas:**
        - Se uma ferramenta (`remember_info`, `recall_info`, `summarize_memory`, `get_weather`) retornar uma mensagem indicando um erro (ex: "Desculpe, ocorreu um erro...", "Falha ao...", "...problema de configuração"), informe ao usuário de forma concisa que houve um problema temporário ao acessar essa função específica e peça para tentar novamente ou continue a conversa sem a informação da ferramenta, se possível.
        
        **REGRAS CRÍTICAS DA MEMÓRIA E CONTEXTO:**
        1.  **Contexto da Sessão é Prioridade:** Sempre considere as mensagens anteriores *desta* conversa primeiro.
        2.  **Memória de Longo Prazo é por Usuário:** Toda interação com as ferramentas de memória é automaticamente vinculada ao usuário atual.
        3.  **Recall (Específico) vs Summarize (Geral):** Use `recall_info` para buscar relevância pontual; use `summarize_memory` para resumos gerais solicitados pelo usuário.
        4.  **Remember Seletivo:** Seja criterioso. A memória de longo prazo é para personalização, não transcrição.
        5.  **Clima Sob Demanda:** Use `get_weather` apenas quando necessário.
        
        Diretrizes Gerais:
        - Priorize clareza, precisão, utilidade, **coerência com a conversa atual** e **personalização**.
        - Use o histórico da sessão e a memória de longo prazo de forma complementar.
        - Seja sempre prestativo, empático e amigável.
        """
    
    def add_tool(self, tool: Any) -> None:
        """
        Adiciona uma ferramenta ao agente.
        
        Args:
            tool (Any): Ferramenta a ser adicionada.
        """
        # Certificar-se de não adicionar duplicatas se já foi adicionada no __init__
        if tool not in self.tools:
            self.tools.append(tool)
            # Recria o agente com as ferramentas atualizadas
            self.agent = Agent(
                name="Voxy Brain",
                instructions=self.instructions,
                tools=self.tools
            )
    
    # Refatorado para async (Tentativa 2)
    async def process_message(self, message: str) -> str:
        """
        Processa uma mensagem recebida de forma assíncrona e retorna a resposta do agente.
        
        Args:
            message (str): Mensagem do usuário.
            
        Returns:
            str: Resposta do agente.
        """
        # Usar Runner.run() para execução assíncrona
        result = await Runner.run(self.agent, message) 
        return result.final_output


# Instância global do agente para fácil importação em outros módulos
# A inicialização aqui já incluirá a ferramenta devido à modificação no __init__
brain_agent = VoxyBrain()


# Refatorado para async (Tentativa 2)
async def process_message(message_content: str, user_id: Optional[int | str] = None):
    """
    Função auxiliar assíncrona para processar mensagens usando o agente brain,
    definindo o contexto do user_id para as ferramentas de memória.
    
    Args:
        message_content (str): Mensagem do usuário.
        user_id (Optional[int | str]): O ID do usuário atual.
        
    Returns:
        str: Resposta final do agente.
        
    Raises:
        ValueError: Se user_id não for fornecido (necessário para ferramentas de memória).
    """
    if user_id is None:
        # Levanta um erro se o user_id não for fornecido, pois as ferramentas de 
        # memória dependem dele via contextvar.
        # Em um cenário sem autenticação, poderíamos ter um fallback, mas aqui é mandatório.
        raise ValueError("user_id é obrigatório para process_message")

    # Define o contextvar antes de executar o Runner
    token = current_user_id_var.set(str(user_id))
    try:
        # Usar Runner.run() para execução assíncrona
        result = await Runner.run(brain_agent, message_content)
        
        # Extrair a resposta final de forma mais segura
        if hasattr(result, 'final_output') and isinstance(result.final_output, str):
            final_response = result.final_output
        elif hasattr(result, 'content') and isinstance(result.content, str):
             # Tenta 'content' como alternativa comum em alguns SDKs/versões
            final_response = result.content
        else:
            # Se não encontrar uma string de resposta clara, loga e retorna erro
            print(f"WARN: Could not extract final string output from RunResult. Result object: {result}")
            final_response = "[Voxy did not produce a text response]"
            
        print(f"Agent final response: {final_response}") # Log da resposta
        return final_response
    finally:
        # Garante que o contextvar seja resetado, mesmo em caso de erro
        current_user_id_var.reset(token) 