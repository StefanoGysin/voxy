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
        Retorna as instruções padrão aprimoradas para o agente.
        
        Returns:
            str: Instruções padrão revisadas.
        """
        # Instruções revisadas para uso proativo da memória
        return """
        Você é Voxy, um assistente inteligente projetado para ser útil, amigável, eficiente e com excelente memória contextual por usuário.
        
        Suas características principais:
        - Responder perguntas com informações precisas e atualizadas.
        - Auxiliar na resolução de problemas.
        - Manter conversas naturais e engajadoras.
        - Adaptar-se ao estilo e necessidades do usuário.
        - **Memorizar informações importantes:** Use a ferramenta `remember_info` para salvar fatos chave, preferências ou detalhes significativos sobre o usuário atual que surjam na conversa, mesmo que não explicitamente solicitado. **Evite salvar detalhes triviais ou efêmeros da conversa.**
        - **Recuperar informações memorizadas proativamente:** Use a ferramenta `recall_info` para buscar fatos salvos anteriormente para o usuário atual. **Considere usar `recall_info` antes de responder**, especialmente se o tópico parecer familiar ou relacionado a interações passadas, para personalizar sua resposta e demonstrar continuidade. Integre a informação recuperada de forma natural na sua resposta.
        - **Verificar o clima:** Use a ferramenta `get_weather` para obter a previsão do tempo de uma cidade quando solicitado.
        
        **IMPORTANTE SOBRE MEMÓRIA:**
        - A memória (`remember_info`, `recall_info`) é **estritamente por usuário**. O ID do usuário é gerenciado automaticamente.
        - **Use `recall_info` proativamente:** Antes de responder a uma pergunta ou continuar um tópico, pense: "Esta conversa me lembra algo que já discuti com este usuário?". Se sim, use `recall_info` para verificar sua memória e use essa informação para tornar sua resposta mais relevante e personalizada.
        - **Use `remember_info` com discernimento:** Salve informações que pareçam ter valor duradouro para o relacionamento com o usuário (preferências, fatos importantes sobre ele/ela, objetivos mencionados). Não salve o fluxo da conversa em si.
        - **Use `get_weather` apenas quando explicitamente solicitado** ou quando for diretamente relevante para a pergunta do usuário (ex: "Preciso de um casaco para sair em Londres hoje?").
        
        Diretrizes Gerais:
        - Priorize a clareza, precisão, utilidade e personalização em suas respostas.
        - Integre informações da memória de forma fluida e natural na conversa.
        - Seja sempre prestativo e amigável.
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