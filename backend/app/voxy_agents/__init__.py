"""
Pacote agents do Voxy.

Este pacote contém os agentes e ferramentas usados pelo Voxy.
"""

# Importar ferramentas individuais de seus respectivos módulos
from .tools.memory_tools import remember_info, recall_info, summarize_memory
from .tools.weather import get_weather

# Importar agentes e funções principais
from .vision import vision_agent
from .brain import brain_agent, process_message, process_vision_result

# Definir listas de ferramentas (se necessário para exportação ou uso futuro)
memory_tools = [remember_info, recall_info, summarize_memory]
weather_tools = [get_weather]

# Atualizar __all__ para exportar nomes corretos/úteis
__all__ = [
    "brain_agent", 
    "vision_agent",
    "process_message",
    "process_vision_result",
    # Exportar ferramentas individuais
    "get_weather",
    "remember_info",
    "recall_info",
    "summarize_memory",
    # Opcionalmente, exportar as listas se forem usadas em outros lugares
    # "memory_tools", 
    # "weather_tools"
] 