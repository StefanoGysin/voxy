import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Import the class and function to test
from app.voxy_agents.brain import VoxyBrain, process_message, brain_agent, agent_tools

# Import tools to potentially mock or check if they are passed
from app.voxy_agents.tools.weather import get_weather
from app.voxy_agents.tools.memory_tools import remember_info, recall_info

# Import context var
from app.memory.mem0_manager import current_user_id_var

# Import items needed for handoff check
from app.core.models import VisioScanRequest
from app.voxy_agents.vision import vision_agent # Import the instance
from app.voxy_agents.brain import process_vision_result # Import the callback

# Import new imports
from app.schemas.agent import Message, Session # Alterado de app.db.models
from agents import Runner, Agent
from app.core.models import VisioScanRequest, ImageRequest

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
async def test_voxy_brain_initialization_with_visioscan_handoff():
    """Testa se VoxyBrain inicializa com a configuração de handoff para Vision."""
    with patch('agents.Agent.__init__') as mock_agent_init:
        brain = VoxyBrain()  # Initialize with defaults

        # Verifica se Agent.__init__ foi chamado
        mock_agent_init.assert_called_once()
        call_args, call_kwargs = mock_agent_init.call_args

        # Verifica o argumento handoffs
        handoffs_list = call_kwargs.get('handoffs', [])
        assert isinstance(handoffs_list, list)
        assert len(handoffs_list) > 0  # Deve ter pelo menos um handoff

        # Busca mais flexível pelo handoff do Vision
        vision_handoff_found = False
        
        for handoff_item in handoffs_list:
            # Verificação direta se é o agente Vision
            if hasattr(handoff_item, 'name') and 'Vision' in handoff_item.name:
                vision_handoff_found = True
                break
                
            # Se for um objeto handoff customizado
            elif hasattr(handoff_item, 'agent') and hasattr(handoff_item.agent, 'name') and 'Vision' in handoff_item.agent.name:
                vision_handoff_found = True
                break
                
            # Se for um objeto com tool_name que indique Vision
            elif hasattr(handoff_item, 'tool_name') and 'vision' in handoff_item.tool_name.lower():
                vision_handoff_found = True
                break
                
            # Se for um dict ou objeto com descrição que mencione Vision
            elif (hasattr(handoff_item, 'tool_description') and 'vision' in handoff_item.tool_description.lower()) or \
                 (hasattr(handoff_item, 'description') and 'vision' in handoff_item.description.lower()):
                vision_handoff_found = True
                break
                
            # Se for uma tupla contendo o agente e alguma configuração
            elif isinstance(handoff_item, tuple) and len(handoff_item) >= 1:
                agent_part = handoff_item[0]
                if hasattr(agent_part, 'name') and 'Vision' in agent_part.name:
                    vision_handoff_found = True
                    break

        assert vision_handoff_found, "Handoff para Vision não encontrado na lista de handoffs"

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
    mock_runner_run.assert_awaited_once_with(brain_agent, test_message, context=None)
    
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
    mock_runner_run.assert_awaited_once_with(brain_agent, test_message, context=None)
    
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
    mock_runner_run.assert_awaited_once_with(brain_agent, test_message, context=None)
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
    mock_runner_run.assert_awaited_once_with(brain_agent, test_message, context=None)
    mock_context_var.reset.assert_called_once_with(mock_token)
    
    # Verifica a resposta via 'content'
    assert response == mock_run_result.content 

# --- Mocks --- 

@pytest.fixture
def mock_supabase_client():
    mock_agent_service = MagicMock()
    mock_agent_service.get_formatted_message_history.return_value = []
    yield mock_agent_service

@pytest.fixture
def mock_runner_run(mocker):
    """Mock Runner.run completely."""
    return mocker.patch('agents.Runner.run', new_callable=AsyncMock)

# Mock the specific vision_agent instance used in brain.py
@pytest.fixture
def mock_vision_agent_instance(mocker):
    mock = mocker.patch('app.voxy_agents.brain.vision_agent', spec=Agent)
    mock.process_image = AsyncMock(return_value="Mocked Vision Analysis")
    return mock

# Mock the process_vision_result callback function
@pytest.fixture
def mock_process_vision_result(mocker):
    return mocker.patch('app.voxy_agents.brain.process_vision_result', new_callable=AsyncMock)


# --- Test Cases --- 

@pytest.mark.asyncio
async def test_process_message_success(mock_supabase_client, mock_runner_run, mocker):
    # Arrange
    user_id = "user123"
    message_content = "What is this image?"
    image_req = ImageRequest(source="url", content="http://example.com/image.jpg")

    # Mock process_image_from_context para retornar True e configurar run_context['vision_result']
    mock_handoff_response = "[ANÁLISE DA IMAGEM - VISION]: Mocked Vision Analysis"
    expected_response = f"Análise da imagem: {mock_handoff_response}"

    # Mock para a função process_image_from_context
    async def mock_process_image_implementation(context, message):
        context['vision_result'] = mock_handoff_response
        return True

    mocker.patch.object(brain_agent, 'process_image_from_context', side_effect=mock_process_image_implementation)

    # Act
    response = await process_message(message_content, user_id, run_context={"image_request": image_req})
    
    # Assert
    assert response == expected_response
    
    # Verify process_image_from_context was called
    brain_agent.process_image_from_context.assert_called_once()
    
    # Runner.run should not be called when vision_result is returned directly
    mock_runner_run.assert_not_called()


@pytest.mark.asyncio
async def test_process_message_with_image_handoff(
    mock_supabase_client, 
    mock_runner_run,
    mock_vision_agent_instance,
    mock_process_vision_result,
    mocker
):
    """Test message processing triggers handoff when image_request is present."""
    # Arrange
    user_id = "user123"
    message_content = "What is this image?"
    image_req = ImageRequest(source="url", content="http://example.com/image.jpg")

    # Mock handoff response
    mock_handoff_response = "[ANÁLISE DA IMAGEM - VISION]: Mocked Vision Analysis"
    expected_response = f"Análise da imagem: {mock_handoff_response}"
    
    # Mock para a função process_image_from_context
    async def mock_process_image_implementation(context, message):
        context['vision_result'] = mock_handoff_response
        return True
    
    mocker.patch.object(brain_agent, 'process_image_from_context', side_effect=mock_process_image_implementation)
    
    # Act
    response = await process_message(message_content, user_id, run_context={"image_request": image_req})
    
    # Assert
    assert response == expected_response
    
    # Verify process_image_from_context was called
    brain_agent.process_image_from_context.assert_called_once()
    
    # Runner.run should not be called when vision_result is returned directly
    mock_runner_run.assert_not_called()


@pytest.mark.asyncio
async def test_process_message_runner_error(mock_supabase_client, mock_runner_run, mocker):
    # Arrange
    user_id = "user123"
    message_content = "What is this image?"
    image_req = ImageRequest(source="url", content="http://example.com/image.jpg")

    # Configure mock for process_image_from_context to fail with an exception
    test_exception = Exception("Test exception")
    
    # Mock para a função process_image_from_context que lança uma exceção
    async def mock_process_image_implementation(context, message):
        raise test_exception
    
    mocker.patch.object(brain_agent, 'process_image_from_context', side_effect=mock_process_image_implementation)

    # Act and Assert
    with pytest.raises(Exception, match="Test exception"):
        await process_message(message_content, user_id, run_context={"image_request": image_req})
    
    # Verify process_image_from_context was called
    brain_agent.process_image_from_context.assert_called_once()
    
    # Runner.run should not be called due to exception
    mock_runner_run.assert_not_called()


   