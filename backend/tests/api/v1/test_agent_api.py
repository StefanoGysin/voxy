import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
import uuid # Import uuid
import json
import base64 # Para criar um token JWT mockado

from app.db.models import User
from app.core.security import get_current_user  # Importar a dependência que vamos sobrescrever
# from app.voxy_agents.brain import process_message # No longer mocking this
from agents import Runner # Import Runner to mock its run method
from fastapi import Depends  # Importar Depends para usar com a sobrescrita de dependência

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

# Função para criar um token JWT mockado válido
def create_mock_jwt(user_id):
    # Criar um token JWT com estrutura válida (header.payload.signature)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": str(user_id), "exp": 9999999999, "aud": "authenticated"}
    signature = "mocksignature123456789"
    
    # Codificar as partes em base64
    def encode_part(part):
        return base64.urlsafe_b64encode(json.dumps(part).encode()).rstrip(b'=').decode()
    
    # Montar o token com as três partes
    token = f"{encode_part(header)}.{encode_part(payload)}.{signature}"
    return token

# Fixtures like 'client' (AsyncClient) and 'test_user' are typically defined in conftest.py
# Assume they provide an authenticated client and a user object.

# Função async para mockar get_current_user
async def mock_get_current_user():
    """Mock da função get_current_user que retorna um usuário fake em vez de chamar o Supabase."""
    mock_user = AsyncMock()
    mock_user.id = "mocked-user-id-from-security"
    return mock_user

@pytest.fixture(autouse=True)
def setup_test_dependencies(monkeypatch):
    """Setup das dependências para os testes, incluindo override de get_current_user."""
    from app.main import app  # Importar app aqui para evitar problemas de circularidade
    
    # Sobrescrever a dependência get_current_user
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    yield
    
    # Limpar override após os testes
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def mock_db_operations():
    """Automatically mock database operations called within the endpoint."""
    # Mock session creation/fetching and message adding/fetching
    with (
        patch("app.api.v1.endpoints.agent.agent_service.create_session", new_callable=AsyncMock) as mock_create,
        patch("app.api.v1.endpoints.agent.get_supabase_client") as mock_get_supabase,
        patch("app.middleware.get_supabase_client") as mock_middleware_get_supabase, # Adicionar mock para o middleware
        patch("app.api.v1.endpoints.agent.agent_service.add_message", new_callable=AsyncMock) as mock_add,
        patch("app.api.v1.endpoints.agent.agent_service.get_messages_by_session", new_callable=AsyncMock) as mock_get_msgs
    ):
        # Create a mock supabase client with table method
        mock_supabase = AsyncMock()
        mock_table = AsyncMock()
        mock_supabase.table.return_value = mock_table
        mock_get_supabase.return_value = mock_supabase
        
        # Configure the auth methods for the middleware mock
        mock_auth = AsyncMock()
        mock_user_response = AsyncMock()
        mock_user = AsyncMock()
        mock_user.id = "mocked-user-id"
        mock_user_response.user = mock_user
        mock_auth.get_user.return_value = mock_user_response
        
        # Attach auth to the Supabase client
        mock_middleware_supabase = AsyncMock()
        mock_middleware_supabase.auth = mock_auth
        
        # Configure the middleware mock
        mock_middleware_get_supabase.return_value = mock_middleware_supabase

        # Setup default return values for mocks
        mock_create.return_value = {"id": uuid.uuid4()}
        mock_add.return_value = {"id": uuid.uuid4()}
        mock_get_msgs.return_value = [] # Return empty history by default

        # Configure mock_table for session checks
        mock_select = AsyncMock()
        mock_eq = AsyncMock()
        mock_maybe_single = AsyncMock()
        mock_execute = AsyncMock()

        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.maybe_single.return_value = mock_maybe_single
        mock_maybe_single.execute.return_value = mock_execute
        # Default: Session found and belongs to user (modify in specific tests if needed)
        mock_execute.data = {"id": str(uuid.uuid4()), "user_id": "user_uuid_placeholder"}

        yield { # Yield mocks if needed in tests, though autouse is main goal
            "create_session": mock_create,
            "add_message": mock_add,
            "get_messages": mock_get_msgs,
            "mock_supabase": mock_supabase,
            "mock_table": mock_table,
            "mock_middleware_supabase": mock_middleware_supabase
        }

# Sobreescrever a fixture auth_headers do conftest para usar o token JWT mockado válido
@pytest.fixture
def auth_headers(test_user: User):
    """
    Fixture para criar headers de autenticação com um token JWT mockado que tem estrutura válida.
    """
    mock_token = create_mock_jwt(test_user.id)
    return {"Authorization": f"Bearer {mock_token}"}


async def test_chat_endpoint_without_image(client: AsyncClient, test_user: User, mock_db_operations, auth_headers):
    """Test the /chat endpoint with a simple text query, mocking Runner."""
    # Arrange
    query = "Hello Voxy"
    expected_response = "Hello there! How can I help?"
    user_id_str = str(test_user.id)

    # Update mock session data to match test_user
    mock_db_operations["mock_table"].select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data["user_id"] = user_id_str

    # Mock the Runner.run method called within the endpoint
    with patch("app.api.v1.endpoints.agent.Runner.run", new_callable=AsyncMock) as mock_runner_run:
        # Mock the result structure returned by Runner.run
        # Assume it returns a list of messages, last one is the assistant's response
        mock_assistant_message = AsyncMock()
        mock_assistant_message.content = expected_response
        mock_runner_run.return_value = [mock_assistant_message] # Return list with mock message

        # Act: Send POST request as form data
        response = await client.post(
            "/api/v1/agent/chat",
            data={"query": query},
            headers=auth_headers
        )

    # Assert
    assert response.status_code == 200
    json_response = response.json()
    assert json_response.get("assistant_content") == expected_response
    assert json_response.get("success") is True

    # Verify Runner.run was awaited correctly
    mock_runner_run.assert_awaited_once()
    call_args, call_kwargs = mock_runner_run.call_args_list[0]
    # call_args[0] should be the agent instance, call_args[1] is the input message
    assert call_args[1] == query # Input should be the original query

    # Verify DB operations were called (using the autouse fixture mocks)
    mock_db_operations["create_session"].assert_awaited_once() # Assumes new session
    assert mock_db_operations["add_message"].await_count == 2 # User msg + Assistant msg

async def test_chat_endpoint_with_image_url(client: AsyncClient, test_user: User, mock_db_operations, auth_headers):
    """Test the /chat endpoint when a valid image_url is provided, mocking Runner."""
    # Arrange
    query = "What is in this image?"
    image_url = "https://i.imgur.com/Tzpwlhp.jpeg"
    expected_agent_response = "The image shows a test pattern."
    expected_input_for_agent = f"{query} [Image URL: {image_url}]" # Combined query + image info
    user_id_str = str(test_user.id)

    # Update mock session data to match test_user
    mock_db_operations["mock_table"].select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data["user_id"] = user_id_str

    # Mock BOTH Runner.run and process_image_from_context to prevent real handoff
    with patch("app.api.v1.endpoints.agent.Runner.run", new_callable=AsyncMock) as mock_runner_run, \
         patch("app.voxy_agents.brain.VoxyBrain.process_image_from_context", new_callable=AsyncMock) as mock_process_image, \
         patch("app.voxy_agents.brain.process_vision_result", new_callable=AsyncMock) as mock_vision_result:
        
        # Configure mocks
        mock_assistant_message = AsyncMock()
        mock_assistant_message.content = expected_agent_response
        mock_runner_run.return_value = [mock_assistant_message]
        
        # Make process_image_from_context return False to force using Runner.run
        mock_process_image.return_value = False

        # Act: Send POST request as form data including image_url
        response = await client.post(
            "/api/v1/agent/chat",
            data={
                "query": query,
                "image_url": image_url
            },
            headers=auth_headers
        )

    # Assert
    assert response.status_code == 200
    json_response = response.json()
    assert json_response.get("assistant_content") == expected_agent_response
    assert json_response.get("success") is True

    # Verify Runner.run was awaited correctly with the MODIFIED input
    mock_runner_run.assert_awaited_once()
    call_args, call_kwargs = mock_runner_run.call_args_list[0]
    assert call_args[1] == expected_input_for_agent # Input includes the image URL string

    # Verify DB operations (assuming new session)
    mock_db_operations["create_session"].assert_awaited_once()
    assert mock_db_operations["add_message"].await_count == 2
    # Check that the user message saved to DB has the ORIGINAL query
    user_message_call = next(call for call in mock_db_operations["add_message"].call_args_list if call.kwargs.get("role") == "user")
    assert user_message_call.kwargs.get("content") == query

async def test_chat_endpoint_invalid_image_url(client: AsyncClient, test_user: User, auth_headers):
    """Test the /chat endpoint with an invalid image_url."""
    # Arrange
    query = "Analyze this"
    invalid_image_url = "not-a-valid-url"

    # Act
    response = await client.post(
        "/api/v1/agent/chat",
        data={
            "query": query,
            "image_url": invalid_image_url
        },
        headers=auth_headers
    )

    # Assert
    # Expecting a 422 Unprocessable Entity due to Pydantic/FastAPI validation
    # or a custom 400 Bad Request if we added specific validation
    assert response.status_code == 400 # Or 422 depending on implementation
    # Check for specific error detail if implemented
    # assert "Invalid image URL format" in response.text

# TODO:
# - Add tests for /sessions endpoint
# - Add tests for /sessions/{session_id}/messages endpoint
# - Test authentication errors (missing/invalid token) - might be in a separate auth test file
# - Test missing 'query' field 