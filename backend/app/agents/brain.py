"""
Módulo do agente principal (Brain) do Voxy.

Este agente é responsável por coordenar outros agentes e ferramentas,
funcionando como o ponto central de inteligência do sistema.
"""

from agents import Agent, Runner
from typing import List, Dict, Any
# Importar a nova ferramenta
from .tools.weather import get_weather

# Placeholder para importações futuras das ferramentas
# from .tools import search_tool, calculator_tool

class VoxyBrain:
    """
    Classe principal do agente Voxy Brain.
    
    Esta classe encapsula a funcionalidade do agente principal,
    responsável por processar mensagens e coordenar outros agentes.
    """
    
    def __init__(self, instructions: str = None):
        """
        Inicializa o agente Voxy Brain.
        
        Args:
            instructions (str, optional): Instruções personalizadas para o agente.
                Se não fornecido, usa as instruções padrão.
        """
        self.instructions = instructions or self._get_default_instructions()
        # Adicionar a ferramenta get_weather à lista inicial
        self.tools = [get_weather]
        
        # Inicializa o agente com o OpenAI Agents SDK
        self.agent = Agent(
            name="Voxy Brain",
            instructions=self.instructions,
            tools=self.tools
        )
    
    def _get_default_instructions(self) -> str:
        """
        Retorna as instruções padrão para o agente.
        
        Returns:
            str: Instruções padrão.
        """
        # Atualizar instruções para incluir a capacidade de verificar o tempo
        return """
        Você é Voxy, um assistente inteligente projetado para ser útil, amigável e eficiente.
        
        Suas características principais:
        - Responder perguntas com informações precisas e atualizadas
        - Auxiliar na resolução de problemas
        - Manter conversas naturais e engajadoras
        - Adaptar-se ao estilo e necessidades do usuário
        - **Você pode verificar a previsão do tempo para uma cidade específica usando a ferramenta disponível.**
        
        Sempre priorize a clareza, a precisão e a utilidade em suas respostas.
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
async def process_message(message: str) -> str:
    """
    Função auxiliar assíncrona para processar mensagens usando o agente brain.
    
    Args:
        message (str): Mensagem do usuário.
        
    Returns:
        str: Resposta do agente.
    """
    return await brain_agent.process_message(message) 