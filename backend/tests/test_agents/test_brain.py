"""
Testes para o agente Voxy Brain.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock
from backend.app.agents.brain import VoxyBrain, process_message
from backend.app.agents.tools.weather import get_weather

# Mock assíncrono para o OpenAI Agents SDK
class MockAsyncRunnerResult:
    def __init__(self, output):
        self.final_output = output

async def mock_async_runner_run(agent, message):
    # Simula alguma operação assíncrona (opcional)
    await asyncio.sleep(0)
    # Simula que o agente usou a ferramenta se a mensagem mencionar 'tempo'
    if 'tempo' in message.lower():
        city_match = message.split('tempo em ')[-1].split('?')[0]
        # Verifica se a ferramenta get_weather está disponível (como AsyncMock)
        weather_tool_mock = next((t for t in agent.tools if isinstance(t, AsyncMock) and t.__name__ == 'get_weather'), None)
        if weather_tool_mock:
            # Simula a chamada e o retorno da ferramenta mockada
            tool_response = await weather_tool_mock(city=city_match) 
            return MockAsyncRunnerResult(tool_response) 
        else:
             return MockAsyncRunnerResult(f"Erro: ferramenta get_weather não encontrada ou não é async mock")
    return MockAsyncRunnerResult("Mocked async response")

class MockAgent:
    def __init__(self, name, instructions, tools):
        self.name = name
        self.instructions = instructions
        self.tools = tools

@pytest.fixture()
def mock_openai_sdk(monkeypatch):
    """Aplica mocks ao OpenAI Agents SDK (versão assíncrona)."""
    monkeypatch.setattr("backend.app.agents.brain.Agent", MockAgent)
    monkeypatch.setattr("backend.app.agents.brain.Runner.run", mock_async_runner_run)

@pytest.mark.asyncio
async def test_voxy_brain_initialization_includes_weather_tool(mock_openai_sdk):
    """
    Testa a inicialização da classe VoxyBrain.
    
    Verifica se o agente é criado com as instruções padrão atualizadas
    e se a ferramenta get_weather está presente (como AsyncMock).
    """
    # Criar um mock assíncrono para a ferramenta get_weather antes de inicializar
    mock_weather_tool = AsyncMock(name="get_weather")
    # Substituir a ferramenta real pela mockada durante o teste
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.app.agents.brain.get_weather", mock_weather_tool)
        brain = VoxyBrain()
    
    assert brain.agent is not None
    assert "Voxy" in brain.agent.instructions
    # Verificar se as instruções mencionam a capacidade de verificar o tempo
    assert "previsão do tempo" in brain.agent.instructions 
    # Verificar se o mock da ferramenta foi adicionado
    assert mock_weather_tool in brain.tools
    assert mock_weather_tool in brain.agent.tools
    assert len(brain.tools) == 1 # Garantir que apenas a ferramenta esperada está lá

@pytest.mark.asyncio
async def test_voxy_brain_custom_instructions(mock_openai_sdk):
    """
    Testa a inicialização do VoxyBrain com instruções personalizadas.
    
    Verifica se as instruções personalizadas são usadas.
    """
    custom_instructions = "Instruções personalizadas."
    brain = VoxyBrain(instructions=custom_instructions)
    assert brain.agent.instructions == custom_instructions

@pytest.mark.asyncio
async def test_process_message_returns_string(mock_openai_sdk):
    """
    Testa se a função assíncrona process_message retorna uma string.
    
    Verifica se a função chama o SDK mockado (versão async) e retorna a saída esperada.
    """
    response = await process_message("Olá, Voxy!")
    assert isinstance(response, str)
    assert response == "Mocked async response"

@pytest.mark.asyncio
async def test_add_tool_does_not_duplicate(mock_openai_sdk):
    """
    Testa que adicionar a mesma ferramenta novamente não a duplica.
    
    Verifica se a ferramenta get_weather não é adicionada novamente.
    """
    mock_weather_tool = AsyncMock(name="get_weather")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.app.agents.brain.get_weather", mock_weather_tool)
        brain = VoxyBrain() # Já inicializa com o mock de get_weather
        
    initial_tool_count = len(brain.tools)
    
    # Tenta adicionar o mesmo mock novamente
    brain.add_tool(mock_weather_tool)
    
    assert len(brain.tools) == initial_tool_count
    assert len(brain.agent.tools) == initial_tool_count
    assert brain.tools.count(mock_weather_tool) == 1 # Garante que só há uma instância

@pytest.mark.asyncio
async def test_process_message_can_use_weather_tool_mocked(mock_openai_sdk):
    """
    Testa se uma mensagem sobre o tempo invoca a resposta simulada da ferramenta mockada.
    """
    city = "Lisboa"
    message = f"Qual o tempo em {city}?"
    expected_tool_response = f"Tempo mockado para {city}"
    
    # Configurar o retorno do mock da ferramenta
    mock_weather_tool = AsyncMock(name="get_weather")
    mock_weather_tool.return_value = expected_tool_response
    
    # Substituir a ferramenta real pela mockada na instância global e executar
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.app.agents.brain.get_weather", mock_weather_tool)
        # Precisamos re-instanciar VoxyBrain ou atualizar a instância global 
        # para que use o mock ANTES de process_message ser chamado.
        # O mais seguro é mockar a instância global usada por process_message
        mp.setattr("backend.app.agents.brain.brain_agent.tools", [mock_weather_tool])
        # Recriar o agente interno da instância global também
        mp.setattr("backend.app.agents.brain.brain_agent.agent", MockAgent(
            name="Voxy Brain", 
            instructions=brain_agent.instructions, 
            tools=[mock_weather_tool]
        ))

        response = await process_message(message)

    # Verificar se a ferramenta mockada foi chamada (opcional)
    # mock_weather_tool.assert_awaited_once_with(city=city)
        
    assert isinstance(response, str)
    # A resposta final agora deve ser o retorno mockado da ferramenta
    assert response == expected_tool_response 