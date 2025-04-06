"""
Testes para o agente Voxy Brain.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.brain import VoxyBrain, process_message, brain_agent
from app.agents.tools.weather import get_weather
from app.agents.tools.memory_tools import remember_info, recall_info
import logging

logger = logging.getLogger(__name__)

# Fixture para mockar o Runner.run
@pytest.fixture
def mock_agent_runner(monkeypatch):
    """ Mocka a função Runner.run para testes unitários de process_message. """
    # Mock para o objeto de resultado retornado por Runner.run
    mock_run_result = MagicMock()
    mock_run_result.final_output = "Resposta final mockada pelo Runner"
    
    mock_runner_run = AsyncMock(return_value=mock_run_result)
    monkeypatch.setattr("app.agents.brain.Runner.run", mock_runner_run)
    # Retorna o próprio mock de Runner.run para que os testes possam inspecioná-lo
    return mock_runner_run

@pytest.fixture
def voxy_brain_instance():
    """ Fixture que cria uma instância padrão do VoxyBrain. """
    return VoxyBrain()

# --- Testes --- 

# Testes de Inicialização
@pytest.mark.asyncio
async def test_voxy_brain_initialization_default(voxy_brain_instance):
    """
    Testa a inicialização padrão do VoxyBrain.
    """
    logger.debug("Iniciando test_voxy_brain_initialization_default")
    brain = voxy_brain_instance
    assert brain.name == "Voxy Brain"
    assert isinstance(brain.instructions, str)
    assert len(brain.instructions) > 0
    # Verificar ferramentas diretamente no atributo tools
    assert isinstance(brain.tools, list)
    # Verificar se as ferramentas reais estão presentes (comparar funções)
    default_tools = [get_weather, remember_info, recall_info]
    assert all(tool in brain.tools for tool in default_tools)
    assert len(brain.tools) == len(default_tools)
    logger.debug(f"VoxyBrain inicializado com ferramentas: {[getattr(t, '__name__', repr(t)) for t in brain.tools]}")

@pytest.mark.asyncio
async def test_voxy_brain_custom_instructions(voxy_brain_instance):
    """
    Testa a inicialização do VoxyBrain com instruções personalizadas.
    """
    logger.debug("Iniciando test_voxy_brain_custom_instructions")
    custom_instructions = "Instruções personalizadas."
    # Criar instância dentro do teste para instruções customizadas
    brain = VoxyBrain(instructions=custom_instructions)
    # Verificar instruções diretamente
    assert brain.instructions == custom_instructions
    logger.debug("Instruções personalizadas verificadas.")

# Testes de Processamento (usando mock_agent_runner)
@pytest.mark.asyncio
async def test_process_message_calls_runner(mock_agent_runner, voxy_brain_instance):
    """
    Testa se a função wrapper process_message chama Runner.run com os args corretos.
    """
    logger.debug("Iniciando test_process_message_calls_runner")
    message = "Olá Voxy"
    user_id = 123 # ID de usuário de teste
    
    # Chama a função de processamento (a wrapper que define o contextvar)
    response = await process_message(message, user_id=user_id)
    
    # Verifica se Runner.run foi chamado uma vez
    mock_agent_runner.assert_called_once()
    
    # Verifica os argumentos passados para Runner.run
    # A função process_message deve passar a instância global `brain_agent`
    args, kwargs = mock_agent_runner.call_args
    assert args[0] is brain_agent 
    assert args[1] == message
    
    # Verifica se a resposta retornada é o final_output do mock
    assert response == mock_agent_runner.return_value.final_output
    logger.debug("Runner.run chamado corretamente e resposta verificada.")

@pytest.mark.asyncio
async def test_process_message_no_user_id_raises_error(mock_agent_runner):
    """
    Testa se process_message levanta ValueError se user_id não for fornecido.
    """
    logger.debug("Iniciando test_process_message_no_user_id_raises_error")
    message = "Olá Voxy"
    
    with pytest.raises(ValueError, match="user_id é obrigatório"):
        await process_message(message, user_id=None)
        
    # Garante que Runner.run não foi chamado
    mock_agent_runner.assert_not_called()
    logger.debug("ValueError levantado corretamente para user_id=None.")

# REMOVER Testes antigos que dependiam de self.agent ou add_tool
# @pytest.mark.asyncio
# async def test_voxy_brain_initialization_includes_all_tools(mock_openai_sdk):
#     ...

# @pytest.mark.asyncio
# async def test_add_tool_does_not_duplicate(mock_openai_sdk):
#     ...

# @pytest.mark.asyncio
# async def test_process_message_returns_string(mock_openai_sdk):
#     ...

# @pytest.mark.asyncio
# async def test_process_message_can_use_weather_tool_mocked(mock_openai_sdk):
#     ...

# @pytest.mark.asyncio
# async def test_process_message_can_use_remember_tool_mocked(mock_openai_sdk):
#     ...

# @pytest.mark.asyncio
# async def test_process_message_can_use_recall_tool_mocked(mock_openai_sdk):
#     ... 