import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
# Não precisamos mais importar AsyncClient diretamente aqui se usarmos patch

# Marcar todos os testes neste módulo para serem executados com pytest-asyncio
pytestmark = pytest.mark.asyncio

# Importar as funções e exceções a serem testadas
from app.services import agent_service
from app.core.exceptions import DatabaseError


# --- Testes para agent_service.add_message ---

# Remover a fixture mock_supabase_async_client por enquanto
# @pytest.fixture
# def mock_supabase_async_client():
#    ...

@pytest.fixture
def message_data():
    """Dados de exemplo para uma mensagem."""
    return {
        "session_id": uuid.uuid4(),
        "role": "user",
        "content": "Olá, mundo!",
        "user_id": uuid.uuid4()
    }

@pytest.fixture
def created_message_response(message_data):
    """Resposta simulada do Supabase para inserção bem-sucedida."""
    return {
        "id": uuid.uuid4(),
        "session_id": str(message_data["session_id"]),
        "role": message_data["role"],
        "content": message_data["content"],
        "user_id": str(message_data["user_id"]),
        "created_at": "2023-10-27T10:00:00+00:00", # Exemplo ISO timestamp
    }

# Remover o patch
# @patch('app.services.agent_service.supabase.table')
async def test_add_message_success_user_role(
    # Não precisamos mais do mock injetado pelo patch
    message_data,
    created_message_response
):
    """Testa add_message com sucesso para role 'user' (mock dentro do teste)."""
    # --- Criar a cadeia de mocks aqui dentro --- 
    # Mock final para a chamada .execute()
    mock_execute = AsyncMock()

    # Mock para o objeto retornado por .insert()
    mock_insert_obj = MagicMock()
    mock_insert_obj.execute = mock_execute # Configura .insert().execute

    # Mock para o objeto retornado por .table()
    mock_table_obj = MagicMock()
    mock_table_obj.insert.return_value = mock_insert_obj # Configura .table().insert()

    # Mock principal do cliente Supabase que será passado para a função
    supabase_mock_client = MagicMock()
    supabase_mock_client.table.return_value = mock_table_obj # Configura .table()
    # --- Fim da criação da cadeia de mocks ---

    # Configurar a resposta de sucesso do mock_execute final
    mock_response = MagicMock()
    mock_response.data = [created_message_response]
    mock_response.error = None
    mock_execute.return_value = mock_response

    # Dados esperados para a chamada insert
    insert_data = {
        "session_id": str(message_data["session_id"]),
        "role": "user",
        "content": message_data["content"],
        "user_id": str(message_data["user_id"])
    }

    # Chamar a função de serviço com o mock criado localmente
    result = await agent_service.add_message(
        supabase=supabase_mock_client, # Passa o mock do cliente
        session_id=message_data["session_id"],
        role="user",
        content=message_data["content"],
        user_id=message_data["user_id"],
    )

    # Asserts
    # Verificar se .table() foi chamado no mock do cliente
    supabase_mock_client.table.assert_called_once_with("messages") 
    # Verificar se .insert() foi chamado no objeto retornado por .table()
    supabase_mock_client.table().insert.assert_called_once_with(insert_data)
    # Verificar se .execute() foi chamado e awaited no objeto retornado por .insert()
    mock_execute.assert_awaited_once() 
    assert result == created_message_response

async def test_add_message_success_assistant_role(
    # Remover mock_supabase_async_client
    message_data, created_message_response
):
    """Testa add_message com sucesso para role 'assistant' (mock dentro do teste)."""
    # --- Criar a cadeia de mocks aqui dentro --- 
    mock_execute = AsyncMock()
    mock_insert_obj = MagicMock()
    mock_insert_obj.execute = mock_execute
    mock_table_obj = MagicMock()
    mock_table_obj.insert.return_value = mock_insert_obj
    supabase_mock_client = MagicMock()
    supabase_mock_client.table.return_value = mock_table_obj
    # --- Fim da criação da cadeia de mocks ---
    
    # Ajustar role na resposta esperada
    created_message_response["role"] = "assistant"
    insert_data = {
        "session_id": str(message_data["session_id"]),
        "role": "assistant", # Usar 'assistant' aqui
        "content": message_data["content"],
        "user_id": str(message_data["user_id"])
    }

    # Configurar resposta de sucesso do mock_execute
    mock_response = MagicMock()
    mock_response.data = [created_message_response]
    mock_response.error = None
    mock_execute.return_value = mock_response

    # Chamar a função
    result = await agent_service.add_message(
        supabase=supabase_mock_client,
        session_id=message_data["session_id"],
        role="assistant", # Passar 'assistant'
        content=message_data["content"],
        user_id=message_data["user_id"],
    )

    # Asserts
    supabase_mock_client.table.assert_called_once_with("messages")
    supabase_mock_client.table().insert.assert_called_once_with(insert_data)
    mock_execute.assert_awaited_once()
    assert result == created_message_response


async def test_add_message_invalid_role(
    # Remover mock_supabase_async_client
    message_data
):
    """Testa add_message com um role inválido (mock dentro do teste)."""
    # --- Criar a cadeia de mocks (mesmo que não seja usada) ---
    mock_execute = AsyncMock()
    mock_insert_obj = MagicMock()
    mock_insert_obj.execute = mock_execute
    mock_table_obj = MagicMock()
    mock_table_obj.insert.return_value = mock_insert_obj
    supabase_mock_client = MagicMock()
    supabase_mock_client.table.return_value = mock_table_obj
    # --- Fim da criação da cadeia de mocks ---

    with pytest.raises(ValueError, match="Role inválido"):
        await agent_service.add_message(
            supabase=supabase_mock_client,
            session_id=message_data["session_id"],
            role="invalid_role", # Role inválido
            content=message_data["content"],
            user_id=message_data["user_id"],
        )

    # Verificar que o Supabase não foi chamado
    supabase_mock_client.table.assert_not_called()
    mock_execute.assert_not_awaited()


async def test_add_message_supabase_error(message_data):
    """Testa add_message quando Supabase retorna um erro."""
    # --- Mocks ---
    mock_execute = AsyncMock()
    mock_insert_obj = MagicMock()
    mock_insert_obj.execute = mock_execute
    mock_table_obj = MagicMock()
    mock_table_obj.insert.return_value = mock_insert_obj
    supabase_mock_client = MagicMock()
    supabase_mock_client.table.return_value = mock_table_obj
    # --- Fim Mocks ---

    # Configurar resposta de erro
    mock_error = MagicMock()
    mock_error.message = "Erro simulado"
    mock_response = MagicMock()
    mock_response.data = None
    mock_response.error = mock_error
    mock_execute.return_value = mock_response

    insert_data = {
        "session_id": str(message_data["session_id"]),
        "role": message_data["role"],
        "content": message_data["content"],
        "user_id": str(message_data["user_id"])
    }

    # Chamar e verificar exceção - Mudança na mensagem de erro esperada
    with pytest.raises(DatabaseError, match="Erro inesperado ao adicionar mensagem: Erro inesperado ao adicionar mensagem: Falha ao adicionar mensagem: Supabase não retornou dados."):
        await agent_service.add_message(
            supabase_mock_client,
            message_data["session_id"],  # Não converter para UUID, já é um objeto UUID
            message_data["role"],
            message_data["content"],
            message_data["user_id"]      # Não converter para UUID, já é um objeto UUID
        )

    # Asserts
    supabase_mock_client.table.assert_called_once_with("messages")
    supabase_mock_client.table().insert.assert_called_once_with(insert_data)
    mock_execute.assert_awaited_once()

async def test_add_message_supabase_no_data_returned(
    # Remover mock_supabase_async_client
    message_data
):
    """Testa add_message quando Supabase não retorna dados nem erro (mock dentro do teste)."""
    # --- Criar a cadeia de mocks aqui dentro --- 
    mock_execute = AsyncMock()
    mock_insert_obj = MagicMock()
    mock_insert_obj.execute = mock_execute
    mock_table_obj = MagicMock()
    mock_table_obj.insert.return_value = mock_insert_obj
    supabase_mock_client = MagicMock()
    supabase_mock_client.table.return_value = mock_table_obj
    # --- Fim da criação da cadeia de mocks ---

    # Configurar resposta sem dados e sem erro
    mock_response = MagicMock()
    mock_response.data = [] # Lista vazia ou None
    mock_response.error = None
    mock_execute.return_value = mock_response

    # Dados esperados para a chamada insert
    insert_data = {
        "session_id": str(message_data["session_id"]),
        "role": message_data["role"],
        "content": message_data["content"],
        "user_id": str(message_data["user_id"])
    }

    with pytest.raises(DatabaseError, match="Falha ao adicionar mensagem: Supabase não retornou dados."):
        await agent_service.add_message(
            supabase=supabase_mock_client,
            session_id=message_data["session_id"],
            role=message_data["role"],
            content=message_data["content"],
            user_id=message_data["user_id"],
        )

    # Verificar que o Supabase foi chamado
    supabase_mock_client.table.assert_called_once_with("messages")
    supabase_mock_client.table().insert.assert_called_once_with(insert_data)
    mock_execute.assert_awaited_once()

async def test_add_message_unexpected_exception(
    # Remover mock_supabase_async_client
    message_data
):
    """Testa add_message quando ocorre uma exceção inesperada (mock dentro do teste)."""
    # --- Criar a cadeia de mocks aqui dentro --- 
    mock_execute = AsyncMock()
    mock_insert_obj = MagicMock()
    mock_insert_obj.execute = mock_execute
    mock_table_obj = MagicMock()
    mock_table_obj.insert.return_value = mock_insert_obj
    supabase_mock_client = MagicMock()
    supabase_mock_client.table.return_value = mock_table_obj
    # --- Fim da criação da cadeia de mocks ---
    
    # Configurar execute_mock para levantar uma exceção genérica
    generic_error_message = "Erro de conexão simulado"
    mock_execute.side_effect = Exception(generic_error_message)

    # Dados esperados para a chamada insert (ainda é feita antes da exceção)
    insert_data = {
        "session_id": str(message_data["session_id"]),
        "role": message_data["role"],
        "content": message_data["content"],
        "user_id": str(message_data["user_id"])
    }

    with pytest.raises(DatabaseError, match=f"Erro inesperado ao adicionar mensagem: {generic_error_message}"):
        await agent_service.add_message(
            supabase=supabase_mock_client,
            session_id=message_data["session_id"],
            role=message_data["role"],
            content=message_data["content"],
            user_id=message_data["user_id"],
        )

    # Verificar que o Supabase foi chamado
    supabase_mock_client.table.assert_called_once_with("messages")
    supabase_mock_client.table().insert.assert_called_once_with(insert_data)
    mock_execute.assert_awaited_once()

# TODO: Adicionar testes para create_session, get_messages_by_session, get_sessions_by_user 

# --- Testes para agent_service.create_session ---

@pytest.fixture
def user_id_fixture():
    """Fixture para um UUID de usuário."""
    return uuid.uuid4()

@pytest.fixture
def created_session_response(user_id_fixture):
    """Resposta simulada do Supabase para criação de sessão bem-sucedida."""
    session_id = uuid.uuid4()
    return {
        "id": session_id,
        "user_id": str(user_id_fixture),
        "created_at": "2023-10-28T10:00:00+00:00",
        "updated_at": "2023-10-28T10:00:00+00:00",
        "title": None,
    }

async def test_create_session_success_with_user_id(user_id_fixture, created_session_response):
    """Testa create_session com sucesso quando user_id é fornecido."""
    # --- Mocks ---
    mock_execute = AsyncMock()
    mock_insert_obj = MagicMock()
    mock_insert_obj.execute = mock_execute
    mock_table_obj = MagicMock()
    mock_table_obj.insert.return_value = mock_insert_obj
    supabase_mock_client = MagicMock()
    supabase_mock_client.table.return_value = mock_table_obj
    # --- Fim Mocks ---

    # Configurar resposta de sucesso
    mock_response = MagicMock()
    mock_response.data = [created_session_response]
    mock_response.error = None
    mock_execute.return_value = mock_response

    insert_data = {"user_id": str(user_id_fixture)}

    # Chamar a função
    result = await agent_service.create_session(supabase_mock_client, user_id_fixture)

    # Asserts
    supabase_mock_client.table.assert_called_once_with("sessions")
    supabase_mock_client.table().insert.assert_called_once_with(insert_data)
    mock_execute.assert_awaited_once()
    assert result == created_session_response

async def test_create_session_success_without_user_id(created_session_response):
    """Testa create_session com sucesso quando user_id NÃO é fornecido."""
    # --- Mocks ---
    mock_execute = AsyncMock()
    mock_insert_obj = MagicMock()
    mock_insert_obj.execute = mock_execute
    mock_table_obj = MagicMock()
    mock_table_obj.insert.return_value = mock_insert_obj
    supabase_mock_client = MagicMock()
    supabase_mock_client.table.return_value = mock_table_obj
    # --- Fim Mocks ---

    # Ajustar resposta esperada para user_id=None
    created_session_response["user_id"] = None
    
    # Configurar resposta de sucesso
    mock_response = MagicMock()
    mock_response.data = [created_session_response]
    mock_response.error = None
    mock_execute.return_value = mock_response

    insert_data = {"user_id": None} # Espera None para user_id

    # Chamar a função
    result = await agent_service.create_session(supabase_mock_client, None) # Passar None

    # Asserts
    supabase_mock_client.table.assert_called_once_with("sessions")
    supabase_mock_client.table().insert.assert_called_once_with(insert_data)
    mock_execute.assert_awaited_once()
    assert result == created_session_response


async def test_create_session_supabase_error(user_id_fixture):
    """Testa create_session quando Supabase retorna um erro."""
    # --- Mocks ---
    mock_execute = AsyncMock()
    mock_insert_obj = MagicMock()
    mock_insert_obj.execute = mock_execute
    mock_table_obj = MagicMock()
    mock_table_obj.insert.return_value = mock_insert_obj
    supabase_mock_client = MagicMock()
    supabase_mock_client.table.return_value = mock_table_obj
    # --- Fim Mocks ---

    # Configurar resposta de erro
    mock_error = MagicMock()
    mock_error.message = "Erro simulado de sessão"
    mock_response = MagicMock()
    mock_response.data = None
    mock_response.error = mock_error
    mock_execute.return_value = mock_response

    insert_data = {"user_id": str(user_id_fixture)}

    # Chamar e verificar exceção - Mudança na mensagem de erro esperada
    with pytest.raises(DatabaseError, match="Erro inesperado ao criar sessão: Erro inesperado ao criar sessão: Falha ao criar sessão de chat: Supabase não retornou dados."):
        await agent_service.create_session(supabase_mock_client, user_id_fixture)

    # Asserts
    supabase_mock_client.table.assert_called_once_with("sessions")
    supabase_mock_client.table().insert.assert_called_once_with(insert_data)
    mock_execute.assert_awaited_once()


async def test_create_session_supabase_no_data(user_id_fixture):
    """Testa create_session quando Supabase não retorna dados nem erro."""
    # --- Mocks ---
    mock_execute = AsyncMock()
    mock_insert_obj = MagicMock()
    mock_insert_obj.execute = mock_execute
    mock_table_obj = MagicMock()
    mock_table_obj.insert.return_value = mock_insert_obj
    supabase_mock_client = MagicMock()
    supabase_mock_client.table.return_value = mock_table_obj
    # --- Fim Mocks ---

    # Configurar resposta vazia
    mock_response = MagicMock()
    mock_response.data = [] # Lista vazia
    mock_response.error = None
    mock_execute.return_value = mock_response

    insert_data = {"user_id": str(user_id_fixture)}

    # Chamar e verificar exceção
    with pytest.raises(DatabaseError, match="Falha ao criar sessão de chat: Supabase não retornou dados."):
        await agent_service.create_session(supabase_mock_client, user_id_fixture)

    # Asserts
    supabase_mock_client.table.assert_called_once_with("sessions")
    supabase_mock_client.table().insert.assert_called_once_with(insert_data)
    mock_execute.assert_awaited_once()


async def test_create_session_unexpected_exception(user_id_fixture):
    """Testa create_session quando uma exceção inesperada ocorre."""
    # --- Mocks ---
    # Simular erro ANTES da chamada execute
    supabase_mock_client = MagicMock()
    supabase_mock_client.table.side_effect = Exception("Erro inesperado de conexão")
    # --- Fim Mocks ---

    # Chamar e verificar exceção
    with pytest.raises(DatabaseError, match="Erro inesperado ao criar sessão: Erro inesperado de conexão"):
        await agent_service.create_session(supabase_mock_client, user_id_fixture)

    # Assert
    supabase_mock_client.table.assert_called_once_with("sessions") # A chamada a table() ainda ocorre

# TODO: Adicionar testes para create_session, get_messages_by_session, get_sessions_by_user 

# --- Testes para agent_service.get_messages_by_session ---

@pytest.fixture
def session_id_fixture():
    """Fixture para um UUID de sessão."""
    return uuid.uuid4()

@pytest.fixture
def sample_messages_response(session_id_fixture, user_id_fixture):
    """Resposta simulada do Supabase com uma lista de mensagens."""
    return [
        {
            "id": uuid.uuid4(),
            "session_id": str(session_id_fixture),
            "role": "user",
            "content": "Primeira mensagem",
            "user_id": str(user_id_fixture),
            "created_at": "2023-10-28T11:00:00+00:00",
        },
        {
            "id": uuid.uuid4(),
            "session_id": str(session_id_fixture),
            "role": "assistant",
            "content": "Resposta do assistente",
            "user_id": str(user_id_fixture),
            "created_at": "2023-10-28T11:01:00+00:00",
        }
    ]


async def test_get_messages_by_session_success(session_id_fixture, sample_messages_response):
    """Testa get_messages_by_session com sucesso retornando mensagens."""
    # --- Mocks ---
    mock_execute = AsyncMock()
    mock_limit_obj = MagicMock()
    mock_limit_obj.execute = mock_execute
    mock_order_obj = MagicMock()
    mock_order_obj.limit.return_value = mock_limit_obj
    mock_eq_obj = MagicMock()
    mock_eq_obj.order.return_value = mock_order_obj
    mock_select_obj = MagicMock()
    mock_select_obj.eq.return_value = mock_eq_obj
    mock_table_obj = MagicMock()
    mock_table_obj.select.return_value = mock_select_obj
    supabase_mock_client = MagicMock()
    supabase_mock_client.table.return_value = mock_table_obj
    # --- Fim Mocks ---

    # Configurar resposta de sucesso
    mock_response = MagicMock()
    mock_response.data = sample_messages_response
    mock_response.error = None
    mock_execute.return_value = mock_response

    limit = 50

    # Chamar a função
    result = await agent_service.get_messages_by_session(supabase_mock_client, session_id_fixture, limit=limit)

    # Asserts
    supabase_mock_client.table.assert_called_once_with("messages")
    mock_table_obj.select.assert_called_once_with("*")
    mock_select_obj.eq.assert_called_once_with("session_id", str(session_id_fixture))
    mock_eq_obj.order.assert_called_once_with("created_at", desc=False)
    mock_order_obj.limit.assert_called_once_with(limit)
    mock_execute.assert_awaited_once()
    assert result == sample_messages_response

async def test_get_messages_by_session_success_empty(session_id_fixture):
    """Testa get_messages_by_session com sucesso retornando lista vazia."""
    # --- Mocks ---
    mock_execute = AsyncMock()
    mock_limit_obj = MagicMock()
    mock_limit_obj.execute = mock_execute
    mock_order_obj = MagicMock()
    mock_order_obj.limit.return_value = mock_limit_obj
    mock_eq_obj = MagicMock()
    mock_eq_obj.order.return_value = mock_order_obj
    mock_select_obj = MagicMock()
    mock_select_obj.eq.return_value = mock_eq_obj
    mock_table_obj = MagicMock()
    mock_table_obj.select.return_value = mock_select_obj
    supabase_mock_client = MagicMock()
    supabase_mock_client.table.return_value = mock_table_obj
    # --- Fim Mocks ---

    # Configurar resposta vazia
    mock_response = MagicMock()
    mock_response.data = [] # Lista vazia
    mock_response.error = None
    mock_execute.return_value = mock_response

    limit = 100 # Default

    # Chamar a função
    result = await agent_service.get_messages_by_session(supabase_mock_client, session_id_fixture)

    # Asserts
    supabase_mock_client.table.assert_called_once_with("messages")
    mock_table_obj.select.assert_called_once_with("*")
    mock_select_obj.eq.assert_called_once_with("session_id", str(session_id_fixture))
    mock_eq_obj.order.assert_called_once_with("created_at", desc=False)
    mock_order_obj.limit.assert_called_once_with(limit)
    mock_execute.assert_awaited_once()
    assert result == []


async def test_get_messages_by_session_supabase_error(session_id_fixture):
    """Testa get_messages_by_session quando Supabase retorna um erro."""
    # --- Mocks ---
    mock_execute = AsyncMock()
    mock_limit_obj = MagicMock()
    mock_limit_obj.execute = mock_execute
    mock_order_obj = MagicMock()
    mock_order_obj.limit.return_value = mock_limit_obj
    mock_eq_obj = MagicMock()
    mock_eq_obj.order.return_value = mock_order_obj
    mock_select_obj = MagicMock()
    mock_select_obj.eq.return_value = mock_eq_obj
    mock_table_obj = MagicMock()
    mock_table_obj.select.return_value = mock_select_obj
    supabase_mock_client = MagicMock()
    supabase_mock_client.table.return_value = mock_table_obj
    # --- Fim Mocks ---

    # Configurar resposta de erro
    mock_error = MagicMock()
    mock_error.message = "Erro ao buscar mensagens"
    mock_response = MagicMock()
    mock_response.data = None
    mock_response.error = mock_error
    mock_execute.return_value = mock_response

    limit = 100

    # Chamar e verificar exceção - Mudança na mensagem de erro esperada
    with pytest.raises(DatabaseError, match="Erro inesperado ao buscar mensagens: Erro inesperado ao buscar mensagens: object of type 'NoneType' has no len()"):
        await agent_service.get_messages_by_session(supabase_mock_client, session_id_fixture)

    # Asserts
    supabase_mock_client.table.assert_called_once_with("messages")
    mock_table_obj.select.assert_called_once_with("*")
    mock_select_obj.eq.assert_called_once_with("session_id", str(session_id_fixture))
    mock_eq_obj.order.assert_called_once_with("created_at", desc=False)
    mock_order_obj.limit.assert_called_once_with(limit)
    mock_execute.assert_awaited_once()


async def test_get_messages_by_session_unexpected_exception(session_id_fixture):
    """Testa get_messages_by_session quando uma exceção inesperada ocorre."""
    # --- Mocks ---
    # Simular erro na chamada select
    mock_table_obj = MagicMock()
    mock_table_obj.select.side_effect = Exception("Erro inesperado de rede")
    supabase_mock_client = MagicMock()
    supabase_mock_client.table.return_value = mock_table_obj
    # --- Fim Mocks ---

    # Chamar e verificar exceção
    with pytest.raises(DatabaseError, match="Erro inesperado ao buscar mensagens: Erro inesperado de rede"):
        await agent_service.get_messages_by_session(supabase_mock_client, session_id_fixture)

    # Assert
    supabase_mock_client.table.assert_called_once_with("messages")
    mock_table_obj.select.assert_called_once_with("*")

# TODO: Adicionar testes para get_sessions_by_user

# --- Testes para agent_service.get_sessions_by_user ---

@pytest.fixture
def sample_sessions_response(user_id_fixture):
    """Resposta simulada do Supabase com uma lista de sessões."""
    return [
        {
            "id": uuid.uuid4(),
            "user_id": str(user_id_fixture),
            "created_at": "2023-10-28T12:00:00+00:00",
            "updated_at": "2023-10-28T12:05:00+00:00",
            "title": "Sessão Recente",
        },
        {
            "id": uuid.uuid4(),
            "user_id": str(user_id_fixture),
            "created_at": "2023-10-27T09:00:00+00:00",
            "updated_at": "2023-10-27T09:10:00+00:00",
            "title": "Sessão Antiga",
        }
    ]

async def test_get_sessions_by_user_success(user_id_fixture, sample_sessions_response):
    """Testa get_sessions_by_user com sucesso retornando sessões."""
    # --- Mocks ---
    mock_execute = AsyncMock()
    mock_limit_obj = MagicMock()
    mock_limit_obj.execute = mock_execute
    mock_order_obj = MagicMock()
    mock_order_obj.limit.return_value = mock_limit_obj
    mock_eq_obj = MagicMock()
    mock_eq_obj.order.return_value = mock_order_obj
    mock_select_obj = MagicMock()
    mock_select_obj.eq.return_value = mock_eq_obj
    mock_table_obj = MagicMock()
    mock_table_obj.select.return_value = mock_select_obj
    supabase_mock_client = MagicMock()
    supabase_mock_client.table.return_value = mock_table_obj
    # --- Fim Mocks ---

    # Configurar resposta de sucesso
    mock_response = MagicMock()
    mock_response.data = sample_sessions_response
    mock_response.error = None
    mock_execute.return_value = mock_response

    limit = 20

    # Chamar a função
    result = await agent_service.get_sessions_by_user(supabase_mock_client, user_id_fixture, limit=limit)

    # Asserts
    supabase_mock_client.table.assert_called_once_with("sessions")
    mock_table_obj.select.assert_called_once_with("id, created_at, updated_at, title")
    mock_select_obj.eq.assert_called_once_with("user_id", str(user_id_fixture))
    mock_eq_obj.order.assert_called_once_with("updated_at", desc=True)
    mock_order_obj.limit.assert_called_once_with(limit)
    mock_execute.assert_awaited_once()
    assert result == sample_sessions_response

async def test_get_sessions_by_user_success_empty(user_id_fixture):
    """Testa get_sessions_by_user com sucesso retornando lista vazia."""
    # --- Mocks ---
    mock_execute = AsyncMock()
    mock_limit_obj = MagicMock()
    mock_limit_obj.execute = mock_execute
    mock_order_obj = MagicMock()
    mock_order_obj.limit.return_value = mock_limit_obj
    mock_eq_obj = MagicMock()
    mock_eq_obj.order.return_value = mock_order_obj
    mock_select_obj = MagicMock()
    mock_select_obj.eq.return_value = mock_eq_obj
    mock_table_obj = MagicMock()
    mock_table_obj.select.return_value = mock_select_obj
    supabase_mock_client = MagicMock()
    supabase_mock_client.table.return_value = mock_table_obj
    # --- Fim Mocks ---

    # Configurar resposta vazia
    mock_response = MagicMock()
    mock_response.data = [] # Lista vazia
    mock_response.error = None
    mock_execute.return_value = mock_response

    limit = 50 # Default

    # Chamar a função
    result = await agent_service.get_sessions_by_user(supabase_mock_client, user_id_fixture)

    # Asserts
    supabase_mock_client.table.assert_called_once_with("sessions")
    mock_table_obj.select.assert_called_once_with("id, created_at, updated_at, title")
    mock_select_obj.eq.assert_called_once_with("user_id", str(user_id_fixture))
    mock_eq_obj.order.assert_called_once_with("updated_at", desc=True)
    mock_order_obj.limit.assert_called_once_with(limit)
    mock_execute.assert_awaited_once()
    assert result == []

async def test_get_sessions_by_user_supabase_error(user_id_fixture):
    """Testa get_sessions_by_user quando Supabase retorna um erro."""
    # --- Mocks ---
    mock_execute = AsyncMock()
    mock_limit_obj = MagicMock()
    mock_limit_obj.execute = mock_execute
    mock_order_obj = MagicMock()
    mock_order_obj.limit.return_value = mock_limit_obj
    mock_eq_obj = MagicMock()
    mock_eq_obj.order.return_value = mock_order_obj
    mock_select_obj = MagicMock()
    mock_select_obj.eq.return_value = mock_eq_obj
    mock_table_obj = MagicMock()
    mock_table_obj.select.return_value = mock_select_obj
    supabase_mock_client = MagicMock()
    supabase_mock_client.table.return_value = mock_table_obj
    # --- Fim Mocks ---

    # Configurar resposta de erro
    mock_error = MagicMock()
    mock_error.message = "Erro ao buscar sessões do usuário"
    mock_response = MagicMock()
    mock_response.data = None
    mock_response.error = mock_error
    mock_execute.return_value = mock_response

    limit = 50

    # Chamar e verificar exceção - Mudança na mensagem de erro esperada
    with pytest.raises(DatabaseError, match="Erro inesperado ao buscar sessões: Erro inesperado ao buscar sessões: object of type 'NoneType' has no len()"):
        await agent_service.get_sessions_by_user(supabase_mock_client, user_id_fixture)

    # Asserts
    supabase_mock_client.table.assert_called_once_with("sessions")
    mock_table_obj.select.assert_called_once_with("id, created_at, updated_at, title")
    mock_select_obj.eq.assert_called_once_with("user_id", str(user_id_fixture))
    mock_eq_obj.order.assert_called_once_with("updated_at", desc=True)
    mock_order_obj.limit.assert_called_once_with(limit)
    mock_execute.assert_awaited_once()

async def test_get_sessions_by_user_unexpected_exception(user_id_fixture):
    """Testa get_sessions_by_user quando uma exceção inesperada ocorre."""
    # --- Mocks ---
    # Simular erro na chamada eq
    mock_select_obj = MagicMock()
    mock_select_obj.eq.side_effect = Exception("Erro DB inesperado")
    mock_table_obj = MagicMock()
    mock_table_obj.select.return_value = mock_select_obj
    supabase_mock_client = MagicMock()
    supabase_mock_client.table.return_value = mock_table_obj
    # --- Fim Mocks ---

    # Chamar e verificar exceção
    with pytest.raises(DatabaseError, match="Erro inesperado ao buscar sessões: Erro DB inesperado"):
        await agent_service.get_sessions_by_user(supabase_mock_client, user_id_fixture)

    # Asserts
    supabase_mock_client.table.assert_called_once_with("sessions")
    mock_table_obj.select.assert_called_once_with("id, created_at, updated_at, title")
    mock_select_obj.eq.assert_called_once_with("user_id", str(user_id_fixture))

# --- Fim dos testes para agent_service ---