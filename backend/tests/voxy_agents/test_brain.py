import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Import the class and function to test
from app.voxy_agents.brain import VoxyBrain, process_message, brain_agent, agent_tools

# Import tools to potentially mock or check if they are passed
from app.voxy_agents.tools.weather import get_weather
from app.voxy_agents.tools.memory_tools import remember_info, recall_info

# Import context var
from app.memory.mem0_manager import current_user_id_var

@pytest.mark.asyncio
async def test_voxy_brain_initialization_defaults():
    """Testa a inicialização do VoxyBrain com valores padrão."""
    with patch('agents.Agent.__init__') as mock_agent_init:
        brain = VoxyBrain()

        # Verifica se Agent.__init__ foi chamado com os argumentos corretos
        mock_agent_init.assert_called_once()
        call_args, call_kwargs = mock_agent_init.call_args
        
        assert call_kwargs.get('name') == "Voxy Brain"
        # Verifica se as instruções padrão estão sendo carregadas
        assert "Você é Voxy, um assistente de IA pessoal" in call_kwargs.get('instructions', '')
        # Verifica se as ferramentas padrão foram passadas
        assert call_kwargs.get('tools') == agent_tools
        assert get_weather in call_kwargs.get('tools', [])
        assert remember_info in call_kwargs.get('tools', [])
        assert recall_info in call_kwargs.get('tools', [])

@pytest.mark.asyncio
async def test_voxy_brain_initialization_custom_args():
    """Testa a inicialização do VoxyBrain com argumentos customizados."""
    custom_name = "Custom Brain"
    custom_instructions = "Be very brief."
    # Use MagicMocks para ferramentas customizadas
    mock_tool_1 = MagicMock()
    mock_tool_2 = MagicMock()
    custom_tools = [mock_tool_1, mock_tool_2]

    with patch('agents.Agent.__init__') as mock_agent_init:
        brain = VoxyBrain(name=custom_name, instructions=custom_instructions, tools=custom_tools)

        # Verifica se Agent.__init__ foi chamado com os argumentos customizados
        mock_agent_init.assert_called_once()
        call_args, call_kwargs = mock_agent_init.call_args
        
        assert call_kwargs.get('name') == custom_name
        assert call_kwargs.get('instructions') == custom_instructions
        assert call_kwargs.get('tools') == custom_tools

# Mais testes serão adicionados aqui 

# --- Testes para a função process_message --- 

@pytest.mark.asyncio
@patch('app.voxy_agents.brain.Runner.run')
@patch('app.voxy_agents.brain.current_user_id_var')
async def test_process_message_success(mock_context_var, mock_runner_run):
    """Testa o processamento bem-sucedido de uma mensagem."""
    # Configura o mock para Runner.run
    mock_run_result = MagicMock()
    mock_run_result.final_output = "Resposta simulada do agente"
    mock_runner_run.return_value = mock_run_result
    
    # Configura o mock para context_var
    mock_token = "mock_token"
    mock_context_var.set.return_value = mock_token
    
    test_message = "Olá Voxy!"
    test_user_id = "user123"
    
    response = await process_message(test_message, test_user_id)
    
    # Verifica se context_var.set foi chamado corretamente
    mock_context_var.set.assert_called_once_with(str(test_user_id))
    
    # Verifica se Runner.run foi chamado corretamente
    # Note: brain_agent é a instância global importada
    mock_runner_run.assert_awaited_once_with(brain_agent, test_message)
    
    # Verifica a resposta
    assert response == mock_run_result.final_output
    
    # Verifica se context_var.reset foi chamado
    mock_context_var.reset.assert_called_once_with(mock_token)

@pytest.mark.asyncio
@patch('app.voxy_agents.brain.Runner.run') # Ainda precisa mockar run, embora não deva ser chamado
@patch('app.voxy_agents.brain.current_user_id_var')
async def test_process_message_no_user_id(mock_context_var, mock_runner_run):
    """Testa se ValueError é levantado quando user_id não é fornecido."""
    test_message = "Mensagem sem user_id"
    
    with pytest.raises(ValueError, match="user_id é obrigatório"):
        await process_message(test_message, user_id=None)
        
    # Verifica se set, run e reset não foram chamados
    mock_context_var.set.assert_not_called()
    mock_runner_run.assert_not_awaited()
    mock_context_var.reset.assert_not_called()

@pytest.mark.asyncio
@patch('app.voxy_agents.brain.Runner.run', new_callable=AsyncMock)
@patch('app.voxy_agents.brain.current_user_id_var')
async def test_process_message_runner_error(mock_context_var, mock_runner_run):
    """Testa o tratamento de erro quando Runner.run levanta uma exceção."""
    # Configura o mock para Runner.run levantar uma exceção
    test_exception = Exception("Erro na execução do agente")
    mock_runner_run.side_effect = test_exception
    
    # Configura o mock para context_var
    mock_token = "mock_token_error"
    mock_context_var.set.return_value = mock_token
    
    test_message = "Mensagem que causa erro"
    test_user_id = "user456"
    
    # Verifica se a exceção original é propagada
    with pytest.raises(Exception, match="Erro na execução do agente"):
        await process_message(test_message, test_user_id)
        
    # Verifica se set foi chamado
    mock_context_var.set.assert_called_once_with(str(test_user_id))
    
    # Verifica se run foi chamado
    mock_runner_run.assert_awaited_once_with(brain_agent, test_message)
    
    # Verifica se reset FOI chamado mesmo com erro (bloco finally)
    mock_context_var.reset.assert_called_once_with(mock_token)

@pytest.mark.asyncio
@patch('app.voxy_agents.brain.Runner.run', new_callable=AsyncMock)
@patch('app.voxy_agents.brain.current_user_id_var')
async def test_process_message_result_no_output(mock_context_var, mock_runner_run):
    """Testa o fallback quando RunResult não tem final_output ou content."""
    # Configura o mock para Runner.run retornar um objeto sem final_output/content
    mock_run_result = MagicMock()
    # Garante que não tem os atributos esperados
    del mock_run_result.final_output 
    del mock_run_result.content
    mock_runner_run.return_value = mock_run_result
    
    mock_token = "mock_token_no_output"
    mock_context_var.set.return_value = mock_token
    
    test_message = "Mensagem com resultado estranho"
    test_user_id = "user789"
    
    response = await process_message(test_message, test_user_id)
    
    # Verifica chamadas
    mock_context_var.set.assert_called_once_with(str(test_user_id))
    mock_runner_run.assert_awaited_once_with(brain_agent, test_message)
    mock_context_var.reset.assert_called_once_with(mock_token)
    
    # Verifica a resposta de fallback
    assert response == "[Voxy did not produce a text response]"

@pytest.mark.asyncio
@patch('app.voxy_agents.brain.Runner.run', new_callable=AsyncMock)
@patch('app.voxy_agents.brain.current_user_id_var')
async def test_process_message_result_with_content(mock_context_var, mock_runner_run):
    """Testa o fallback quando RunResult tem 'content' mas não 'final_output'."""
    # Configura o mock para Runner.run retornar um objeto com 'content'
    mock_run_result = MagicMock()
    mock_run_result.content = "Resposta via content"
    # Garante que não tem 'final_output'
    del mock_run_result.final_output 
    mock_runner_run.return_value = mock_run_result
    
    mock_token = "mock_token_content"
    mock_context_var.set.return_value = mock_token
    
    test_message = "Mensagem com resultado content"
    test_user_id = "user101"
    
    response = await process_message(test_message, test_user_id)
    
    # Verifica chamadas
    mock_context_var.set.assert_called_once_with(str(test_user_id))
    mock_runner_run.assert_awaited_once_with(brain_agent, test_message)
    mock_context_var.reset.assert_called_once_with(mock_token)
    
    # Verifica a resposta via 'content'
    assert response == mock_run_result.content 