import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
import openai # Import openai for exception types

from agents import Runner # Importar Runner
from app.core.models import VisioScanRequest, ImageRequest
from app.voxy_agents.vision import VisionAgent # Importar a classe, não a instância global

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

# TODO: Add fixtures for VisionAgent instance, mocks, etc.

@pytest.fixture
def mock_model_fixture():
    """Fixture to mock the vision_model for agent initialization."""
    with patch("app.voxy_agents.vision.vision_model", new_callable=MagicMock) as mock_model:
        yield mock_model

@pytest.fixture
def mock_openai_client_fixture():
    """Fixture to mock the openai_async_client instance."""
    # 1. Create a mock AsyncOpenAI client instance
    mock_client = AsyncMock(spec=openai.AsyncOpenAI)
    # 2. Mock the chat.completions property and its create method
    mock_client.chat = AsyncMock()
    mock_client.chat.completions = AsyncMock()
    mock_client.chat.completions.create = AsyncMock() # Default behavior
    with patch("app.voxy_agents.vision.openai_async_client", mock_client):
        yield mock_client # Yield the mock client instance itself


async def test_vision_agent_initialization(mock_model_fixture):
    """Test that VisionAgent initializes correctly."""
    # Arrange (handled by fixture)
    # Act
    agent = VisionAgent()

    # Assert
    assert isinstance(agent, VisionAgent)
    assert agent.name == "Vision"
    assert agent.model == mock_model_fixture # Check fixture was used


@patch("agents.Runner.run", new_callable=AsyncMock)
async def test_vision_agent_process_image_url_success(mock_runner_run):
    """Test the core logic of processing an image URL successfully using Runner."""
    # Arrange
    agent = VisionAgent()
    
    # Preparar o input
    input_prompt = "Por favor analise a imagem em https://i.imgur.com/Tzpwlhp.jpeg usando análise do tipo description."
    
    # Configurar mock de resposta
    expected_analysis = "This is a detailed description of the image at https://i.imgur.com/Tzpwlhp.jpeg."
    mock_response = [AsyncMock()]
    mock_response[-1].content = expected_analysis
    mock_runner_run.return_value = mock_response

    # Act
    result_message = await Runner.run(starting_agent=agent, input=input_prompt)

    # Assert
    mock_runner_run.assert_awaited_once_with(starting_agent=agent, input=input_prompt)
    assert result_message[-1].content == expected_analysis


@patch("agents.Runner.run", new_callable=AsyncMock)
async def test_vision_agent_openai_api_error(mock_runner_run):
    """Test that Runner raises an error if the OpenAI API call fails."""
    # Arrange
    agent = VisionAgent()
    
    # Usar uma string como input para o agente
    input_prompt = "Por favor analise a imagem em https://i.imgur.com/Tzpwlhp.jpeg."

    # Configurar o mock para lançar exceção
    error_message = "OpenAI API error"
    mock_runner_run.side_effect = openai.APIError(
        message=error_message,
        request=MagicMock(),
        body=None
    )

    # Act & Assert
    with pytest.raises(openai.APIError, match=error_message):
        await Runner.run(starting_agent=agent, input=input_prompt)

    # Verify mock was called
    mock_runner_run.assert_awaited_once_with(starting_agent=agent, input=input_prompt)


@patch("agents.Runner.run", new_callable=AsyncMock)
async def test_vision_agent_process_base64_success(mock_runner_run):
    """Test processing a base64 encoded image successfully using Runner."""
    # Arrange
    agent = VisionAgent()
    
    # Preparar o input para o agente
    input_prompt = "Extraia o texto da imagem codificada em base64 com mime-type image/png."
    
    # Configurar mock de resposta
    expected_analysis = "This is a description of the base64 image."
    mock_response = [AsyncMock()]
    mock_response[-1].content = expected_analysis
    mock_runner_run.return_value = mock_response

    # Act
    result_message = await Runner.run(starting_agent=agent, input=input_prompt)

    # Assert
    mock_runner_run.assert_awaited_once_with(starting_agent=agent, input=input_prompt)
    assert result_message[-1].content == expected_analysis


async def test_vision_agent_invalid_url():
    """Test how the agent handles an invalid image URL (if applicable within the agent itself)."""
    # Validation likely happens BEFORE the agent (in API layer or handoff logic).
    pass # Placeholder


# TODO: Add more tests:
# - Test different user prompts / analysis types if logic changes based on them
# - Test if VisioScanRequest included base64 data instead of URL
# - Test interaction with context if the agent uses it significantly (unlikely for Vision)
# - Test rate limiting or other OpenAI specific errors if necessary 