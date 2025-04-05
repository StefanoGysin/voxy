"""
Testes para o agente Voxy Brain.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.brain import VoxyBrain, process_message, brain_agent
from app.agents.tools.weather import get_weather
from app.agents.tools.memory_tools import remember_info, recall_info
import logging # Adicionar import de logging

# Configurar logging para testes (opcional, mas útil)
# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__) # Usar logger

# Mock assíncrono para o OpenAI Agents SDK
class MockAsyncRunnerResult:
    def __init__(self, output):
        self.final_output = output

async def mock_async_runner_run(agent, message):
    # Simula alguma operação assíncrona (opcional)
    await asyncio.sleep(0)
    logger.debug(f"mock_async_runner_run: Recebido agent='{agent.name}', message='{message[:50]}...'")
    
    # Simula escolha de ferramenta pelo LLM baseado em palavras-chave
    lower_message = message.lower()
    tool_name = None
    tool_kwargs = {}
    tool_response = "Default Tool Response"

    if 'tempo em' in lower_message:
        city_match = message.split('tempo em ')[-1].split('?')[0].strip()
        tool_name = "get_weather"
        tool_kwargs = {"city": city_match}
        tool_response = f"Tempo ensolarado para {city_match} (mocked)" # Resposta simulada
            
    elif 'lembre-se que' in lower_message or 'memorize que' in lower_message:
        content_match = message.split('que ', 1)[-1].strip()
        tool_name = "remember_info"
        tool_kwargs = {"content": content_match}
        tool_response = "Ok, lembrei disso (mocked)" # Resposta simulada
            
    elif 'qual é' in lower_message or 'o que você lembra sobre' in lower_message:
        query_match = message
        tool_name = "recall_info"
        tool_kwargs = {"query": query_match}
        tool_response = "Lembrei disto: ... (mocked)" # Resposta simulada
            
    # Se uma ferramenta foi "escolhida", chama o método mockado no agente
    if tool_name:
        logger.debug(f"mock_async_runner_run: Simulando chamada a agent.call_tool_mock(tool_name='{tool_name}', kwargs={tool_kwargs})")
        # Chama o método mockado no MockAgent
        await agent.call_tool_mock(tool_name=tool_name, **tool_kwargs)
        # Retorna uma resposta simulada que viria após a execução da ferramenta
        return MockAsyncRunnerResult(f"[Tool Response] {tool_response}")
    else:
        # Resposta padrão se nenhuma ferramenta for "acionada"
        logger.debug(f"mock_async_runner_run: Nenhuma ferramenta acionada. Retornando resposta padrão.")
        return MockAsyncRunnerResult("Mocked default async response")

class MockAgent:
    def __init__(self, name, instructions, tools):
        self.name = name
        self.instructions = instructions
        self.tools = tools
        # Adiciona um mock para simular a chamada de ferramenta
        self.call_tool_mock = AsyncMock()

@pytest.fixture()
def mock_openai_sdk(monkeypatch):
    """Aplica mocks APENAS ao Agent e Runner.run."""
    monkeypatch.setattr("app.agents.brain.Agent", MockAgent)
    monkeypatch.setattr("app.agents.brain.Runner.run", mock_async_runner_run)

# Mock SDK OpenAI Agents (simplificado)
# Fixture para mockar o Runner.run
@pytest.fixture
def mock_agent_runner(monkeypatch):
    """ Mocka a função Runner.run para testes. """
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
async def test_voxy_brain_custom_instructions(mock_agent_runner):
    """
    Testa a inicialização do VoxyBrain com instruções personalizadas.
    """
    logger.debug("Iniciando test_voxy_brain_custom_instructions")
    custom_instructions = "Instruções personalizadas."
    brain = VoxyBrain(instructions=custom_instructions)
    # Verificar instruções diretamente
    assert brain.instructions == custom_instructions
    logger.debug("Instruções personalizadas verificadas.")

# Testes de Processamento (usando mock_agent_runner)
@pytest.mark.asyncio
async def test_process_message_calls_runner(mock_agent_runner, voxy_brain_instance):
    """
    Testa se process_message chama Runner.run com os argumentos corretos.
    """
    logger.debug("Iniciando test_process_message_calls_runner")
    message = "Olá Voxy"
    user_id = 123
    
    # Chama a função de processamento
    response = await process_message(message, user_id=user_id)
    
    # Verifica se Runner.run foi chamado uma vez
    mock_agent_runner.assert_called_once()
    
    # Verifica os argumentos passados para Runner.run
    args, kwargs = mock_agent_runner.call_args
    assert args[0] is brain_agent # Verifica se passou a instância singleton global
    assert args[1] == message
    
    # Verifica se a resposta retornada é o final_output do mock
    assert response == mock_agent_runner.return_value.final_output
    logger.debug("Runner.run chamado corretamente e resposta verificada.")

@pytest.mark.asyncio
async def test_process_message_no_user_id_raises_error(mock_agent_runner, voxy_brain_instance):
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