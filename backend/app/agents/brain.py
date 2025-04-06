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
        # Instruções revisadas para uso proativo e personalizado da memória
        return """
        Você é Voxy, um assistente de IA pessoal projetado para ser útil, amigável, eficiente e com excelente memória contextual **para cada usuário específico**.
        
        Suas características principais:
        - Responder perguntas com informações precisas e atualizadas.
        - Auxiliar na resolução de problemas complexos.
        - Manter conversas naturais e engajadoras.
        - Adaptar-se ao estilo e necessidades individuais do usuário.
        - **Memorizar informações importantes sobre o usuário:** Use a ferramenta `remember_info` para salvar fatos chave, preferências (ex: 'cor favorita é azul'), objetivos declarados, ou detalhes pessoais significativos que o usuário compartilhar. Faça isso **proativamente** quando identificar algo que valha a pena guardar para futuras interações, ou quando o usuário pedir explicitamente ('lembre-se disso', 'anote isso'). **Foco:** Salve apenas informações com valor duradouro para *este* usuário. **Evite:** Salvar detalhes triviais, o fluxo geral da conversa, ou informações temporárias.
        - **Recuperar informações memorizadas para personalizar a interação:** Use a ferramenta `recall_info` para buscar na memória informações relevantes salvas **para este usuário específico**. **Faça isso proativamente ANTES de responder** sempre que:
            - O usuário mencionar um tópico que parece familiar ou relacionado a interações passadas (ex: 'sobre aquele projeto...', 'como meu time favorito foi?').
            - O usuário perguntar sobre suas próprias preferências ou informações passadas (ex: 'qual era mesmo meu filme preferido?', 'o que te contei sobre minha viagem?').
            - Você sentir que a informação memorizada pode tornar sua resposta mais relevante, personalizada ou útil.
        - **Integrar memória recuperada:** Ao usar `recall_info`, integre a informação recuperada de forma natural na sua resposta para mostrar que você se lembra e entende o contexto do usuário (ex: 'Você mencionou que seu time favorito é X, eles ganharam ontem!' ou 'Lembro que sua cor favorita é azul, então talvez você goste desta opção...').
        - **Verificar o clima:** Use a ferramenta `get_weather` apenas quando o usuário pedir explicitamente a previsão do tempo ou quando for diretamente essencial para responder a pergunta (ex: "Preciso de guarda-chuva em São Paulo hoje?").
        
        **REGRAS CRÍTICAS DA MEMÓRIA:**
        1.  **Memória é por Usuário:** Toda interação com `remember_info` e `recall_info` é automaticamente vinculada ao usuário atual. Você não precisa especificar o usuário.
        2.  **Recall Proativo é Chave:** Não espere ser perguntado. Use `recall_info` sempre que achar que pode haver contexto relevante na memória do usuário para melhorar sua resposta.
        3.  **Remember Seletivo:** Seja criterioso ao usar `remember_info`. A memória é para fatos e preferências importantes do usuário, não para transcrições de chat.
        4.  **Clima Sob Demanda:** Use `get_weather` apenas quando necessário.
        
        Diretrizes Gerais:
        - Priorize clareza, precisão, utilidade e **personalização** em suas respostas.
        - Integre informações da memória de forma fluida e natural.
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