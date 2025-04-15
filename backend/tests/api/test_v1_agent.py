# backend/tests/api/test_v1_agent.py

import uuid
from unittest.mock import AsyncMock, patch, ANY, MagicMock
from typing import Any
from datetime import datetime

import pytest
from httpx import AsyncClient
# Usar Client síncrono se as chamadas diretas forem síncronas, mas aqui mockamos tudo
from supabase import Client as SupabaseClient
# Importar AsyncClient também
from supabase import AsyncClient as SupabaseAsyncClient 

# Corrigir import Runner
from agents import Runner
from app.schemas.agent import AgentChatRequest, AgentChatResponse, Message, Session
from app.db.models import UserRead
from app.core.security import get_current_user
# Importar a dependência do cliente Supabase Async
from app.db.supabase_client import get_supabase_client

# Mark all tests in this module to use the asyncio event loop
pytestmark = pytest.mark.asyncio

# Fixtures like 'test_client', 'test_user', 'supabase_test_client'
# are expected to be available from conftest.py
# auth_headers não é mais necessário aqui

# Importar app e get_current_user para override
from app.main import app
from app.core.security import get_current_user

# --- Test GET /api/v1/agent/sessions ---

@pytest.mark.asyncio
async def test_list_sessions_success(
    test_client: AsyncClient, 
    test_user: UserRead
):
    """Tests successful listing of user's sessions by overriding get_current_user."""
    now = datetime.now()
    mock_sessions_data = [
        {"id": uuid.uuid4(), "user_id": test_user.id, "created_at": now, "updated_at": now, "title": "Session 1"},
        {"id": uuid.uuid4(), "user_id": test_user.id, "created_at": now, "updated_at": now, "title": "Session 2"},
    ]

    # Override da dependência get_current_user
    app.dependency_overrides[get_current_user] = lambda: test_user

    # Criar um mock do cliente Supabase para o middleware
    mock_supabase_auth = MagicMock(spec=SupabaseAsyncClient)
    mock_supabase_auth.auth = MagicMock()
    
    # Configurar o mock para retornar o test_user quando auth.get_user for chamado
    mock_response = MagicMock()
    mock_response.user = MagicMock()
    mock_response.user.id = str(test_user.id)
    mock_response.user.email = test_user.email
    mock_response.user.user_metadata = {'username': test_user.username}
    mock_supabase_auth.auth.get_user = AsyncMock(return_value=mock_response)

    # Mockar apenas o service que busca as sessões
    # Usar mocker.patch para consistência se mocker for injetado
    with patch(
        "app.api.v1.endpoints.agent.agent_service.get_sessions_by_user",
        # Se agent_service for sync, não usar AsyncMock, mas aqui mockamos
        return_value=mock_sessions_data,
    ) as mock_get_sessions, patch(
        "app.middleware.get_supabase_client", 
        return_value=mock_supabase_auth
    ):
        # Adicionar token fictício no cabeçalho de autenticação
        headers = {"Authorization": "Bearer fake-test-token"}
        response = await test_client.get("/api/v1/agent/sessions", headers=headers)

        assert response.status_code == 200
        response_data = response.json()
        assert "sessions" in response_data
        assert len(response_data["sessions"]) == len(mock_sessions_data)
        response_session_ids = {s["id"] for s in response_data["sessions"]}
        mock_session_ids = {str(s["id"]) for s in mock_sessions_data}
        assert response_session_ids == mock_session_ids

        # Verificar se o service foi chamado com o user_id correto
        mock_get_sessions.assert_called_once_with(
            supabase=ANY, # Usar ANY se não precisar verificar o cliente exato
            user_id=test_user.id
        )
        
        # Verificar se o middleware tentou validar o token
        mock_supabase_auth.auth.get_user.assert_awaited_once_with("fake-test-token")

    # Limpar overrides após o teste
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_sessions_error(
    test_client: AsyncClient, 
    test_user: UserRead
):
    """Tests error handling when the service fails by overriding get_current_user."""
    # Override da dependência get_current_user
    app.dependency_overrides[get_current_user] = lambda: test_user

    # Criar um mock do cliente Supabase para o middleware
    mock_supabase_auth = MagicMock(spec=SupabaseAsyncClient)
    mock_supabase_auth.auth = MagicMock()
    
    # Configurar o mock para retornar o test_user quando auth.get_user for chamado
    mock_response = MagicMock()
    mock_response.user = MagicMock()
    mock_response.user.id = str(test_user.id)
    mock_response.user.email = test_user.email
    mock_response.user.user_metadata = {'username': test_user.username}
    mock_supabase_auth.auth.get_user = AsyncMock(return_value=mock_response)

    # Mockar apenas o service para levantar uma exceção
    with patch(
        "app.api.v1.endpoints.agent.agent_service.get_sessions_by_user",
        side_effect=Exception("Database connection failed"),
    ) as mock_get_sessions, patch(
        "app.middleware.get_supabase_client", 
        return_value=mock_supabase_auth
    ):
        # Adicionar token fictício no cabeçalho de autenticação
        headers = {"Authorization": "Bearer fake-test-token"}  
        response = await test_client.get("/api/v1/agent/sessions", headers=headers)

        assert response.status_code == 500
        assert "Erro interno ao buscar sessões" in response.json()["detail"]
        
        from unittest.mock import ANY 
        mock_get_sessions.assert_called_once_with(
            supabase=ANY, # Ajustar se precisar verificar cliente específico
            user_id=test_user.id
        )
        
        # Verificar se o middleware tentou validar o token
        mock_supabase_auth.auth.get_user.assert_awaited_once_with("fake-test-token")
        
    # Limpar overrides após o teste
    app.dependency_overrides.clear()

# --- Test GET /api/v1/agent/sessions/{session_id}/messages ---

@pytest.mark.asyncio
async def test_get_session_messages_success(
    test_client: AsyncClient,
    test_user: UserRead, # auth_headers removido
    supabase_test_client: SupabaseClient, # Usar cliente sync se aplicável
    mocker
):
    """Tests successful retrieval of messages for a specific session."""
    session_id = uuid.uuid4()
    now = datetime.now()
    # Garantir que test_user.id seja UUID aqui se for o tipo esperado
    mock_supabase_session_data = {"id": str(session_id), "user_id": str(test_user.id), "created_at": now.isoformat(), "updated_at": now.isoformat(), "title": "Test Session"}
    mock_messages_data = [
        # Garantir que test_user.id seja UUID aqui se for o tipo esperado
        {"id": uuid.uuid4(), "session_id": session_id, "role": "user", "content": "Hello", "created_at": now.isoformat(), "user_id": test_user.id},
        {"id": uuid.uuid4(), "session_id": session_id, "role": "assistant", "content": "Hi there!", "created_at": now.isoformat(), "user_id": test_user.id},
    ]

    # Override da dependência get_current_user
    app.dependency_overrides[get_current_user] = lambda: test_user
    
    # Criar um mock do cliente Supabase para o middleware
    mock_supabase_auth = MagicMock(spec=SupabaseAsyncClient)
    mock_supabase_auth.auth = MagicMock()
    
    # Configurar o mock para retornar o test_user quando auth.get_user for chamado
    mock_auth_response = MagicMock()
    mock_auth_response.user = MagicMock()
    mock_auth_response.user.id = str(test_user.id)
    mock_auth_response.user.email = test_user.email
    mock_auth_response.user.user_metadata = {'username': test_user.username}
    mock_supabase_auth.auth.get_user = AsyncMock(return_value=mock_auth_response)

    # Mockar APENAS a chamada ao service get_messages_by_session
    # A função get_messages_by_session agora é async
    with patch("app.api.v1.endpoints.agent.agent_service.get_messages_by_session", new_callable=AsyncMock, return_value=mock_messages_data) as mock_get_messages:

        # Mockar a chamada interna ao supabase client para verificação da sessão
        mock_supabase_response = MagicMock()
        mock_supabase_response.data = mock_supabase_session_data
        mock_supabase_response.error = None

        # --- Correção do Mock --- 
        # Mockar a cadeia de chamadas Supabase, garantindo que execute seja AsyncMock
        mock_execute = AsyncMock(return_value=mock_supabase_response) # <<< CORRIGIDO
        mock_maybe_single = MagicMock()
        mock_maybe_single.execute = mock_execute
        mock_eq = MagicMock(return_value=mock_maybe_single)
        mock_select = MagicMock(return_value=mock_eq)
        # Mockar o método table do cliente Async (obtido via get_supabase_client)
        # Precisamos mockar o cliente que a *rota* recebe, não a fixture sync.
        # Vamos usar patch para mockar o cliente dentro do escopo da rota.
        # Isso é mais robusto que mockar a fixture.
        mock_async_client = MagicMock()
        mock_async_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute = mock_execute

        # Aplicar override para o cliente Supabase Async que a rota usa
        app.dependency_overrides[get_supabase_client] = lambda: mock_async_client

        # Patch para o middleware usar o mesmo mock do cliente Supabase
        with patch("app.middleware.get_supabase_client", return_value=mock_supabase_auth):
            # Adicionar token fictício no cabeçalho de autenticação
            headers = {"Authorization": "Bearer fake-test-token"}
            response = await test_client.get(f"/api/v1/agent/sessions/{session_id}/messages", headers=headers)

            assert response.status_code == 200
            response_data = response.json()
            assert "messages" in response_data
            assert len(response_data["messages"]) == 2
            assert response_data["messages"][0]["content"] == "Hello"
            assert response_data["messages"][1]["role"] == "assistant"

            # Verificar se a cadeia de chamadas no cliente mockado foi feita corretamente
            mock_async_client.table.assert_called_once_with("sessions")
            mock_async_client.table.return_value.select.assert_called_once_with("id, user_id")
            mock_async_client.table.return_value.select.return_value.eq.assert_called_once_with("id", str(session_id))
            mock_async_client.table.return_value.select.return_value.eq.return_value.maybe_single.assert_called_once()
            mock_execute.assert_awaited_once() # <<< CORRIGIDO

            # Verificar se get_messages_by_session foi chamado corretamente
            mock_get_messages.assert_awaited_once_with(supabase=ANY, session_id=session_id)
            
            # Verificar se o middleware tentou validar o token
            mock_supabase_auth.auth.get_user.assert_awaited_once_with("fake-test-token")

    # Limpar overrides após o teste
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_session_messages_session_not_found(
    test_client: AsyncClient,
    test_user: UserRead, # auth_headers removido
    mocker # Remover supabase_test_client, usar mocker/patch
):
    """Tests getting messages when the session is not found for the user."""
    session_id = uuid.uuid4()

    # Override da dependência get_current_user
    app.dependency_overrides[get_current_user] = lambda: test_user
    
    # Criar um mock do cliente Supabase para o middleware
    mock_supabase_auth = MagicMock(spec=SupabaseAsyncClient)
    mock_supabase_auth.auth = MagicMock()
    
    # Configurar o mock para retornar o test_user quando auth.get_user for chamado
    mock_auth_response = MagicMock()
    mock_auth_response.user = MagicMock()
    mock_auth_response.user.id = str(test_user.id)
    mock_auth_response.user.email = test_user.email
    mock_auth_response.user.user_metadata = {'username': test_user.username}
    mock_supabase_auth.auth.get_user = AsyncMock(return_value=mock_auth_response)

    # Mockar APENAS a chamada ao service (que não deve ser chamada)
    # E a cadeia de chamadas Supabase Async
    with patch("app.api.v1.endpoints.agent.agent_service.get_messages_by_session", new_callable=AsyncMock) as mock_get_messages:

        # Mockar a chamada interna ao supabase async client para retornar None
        mock_supabase_response = MagicMock()
        mock_supabase_response.data = None # Simula sessão não encontrada
        mock_supabase_response.error = None # <<< ADICIONADO: Explicitar que não houve erro
        
        # --- Correção do Mock --- 
        mock_execute = AsyncMock(return_value=mock_supabase_response) # <<< CORRIGIDO
        mock_async_client = MagicMock()
        mock_async_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute = mock_execute
        app.dependency_overrides[get_supabase_client] = lambda: mock_async_client

        # Patch para o middleware usar o mesmo mock do cliente Supabase
        with patch("app.middleware.get_supabase_client", return_value=mock_supabase_auth):
            # Adicionar token fictício no cabeçalho de autenticação
            headers = {"Authorization": "Bearer fake-test-token"}
            response = await test_client.get(f"/api/v1/agent/sessions/{session_id}/messages", headers=headers)

            assert response.status_code == 404
            assert "Sessão não encontrada" in response.json()["detail"]

            # Verificar mocks da cadeia Supabase Async
            mock_async_client.table.assert_called_once_with("sessions")
            mock_async_client.table.return_value.select.assert_called_once_with("id, user_id")
            mock_async_client.table.return_value.select.return_value.eq.assert_called_once_with("id", str(session_id))
            mock_async_client.table.return_value.select.return_value.eq.return_value.maybe_single.assert_called_once()
            mock_execute.assert_awaited_once() # <<< CORRIGIDO

            mock_get_messages.assert_not_called() # Não foi awaited
            
            # Verificar se o middleware tentou validar o token
            mock_supabase_auth.auth.get_user.assert_awaited_once_with("fake-test-token")

    # Limpar overrides após o teste
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_session_messages_forbidden(
    test_client: AsyncClient,
    test_user: UserRead, # auth_headers removido
    mocker # Remover supabase_test_client, usar mocker/patch
):
    """Tests getting messages when the session exists but belongs to another user."""
    session_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    now = datetime.now() # Necessário para mock data

    # Override da dependência get_current_user
    app.dependency_overrides[get_current_user] = lambda: test_user
    
    # Criar um mock do cliente Supabase para o middleware
    mock_supabase_auth = MagicMock(spec=SupabaseAsyncClient)
    mock_supabase_auth.auth = MagicMock()
    
    # Configurar o mock para retornar o test_user quando auth.get_user for chamado
    mock_auth_response = MagicMock()
    mock_auth_response.user = MagicMock()
    mock_auth_response.user.id = str(test_user.id)
    mock_auth_response.user.email = test_user.email
    mock_auth_response.user.user_metadata = {'username': test_user.username}
    mock_supabase_auth.auth.get_user = AsyncMock(return_value=mock_auth_response)

    # Mockar APENAS a cadeia de chamadas Supabase Async
    # (agent_service.get_messages_by_session não deve ser chamado)
    with patch("app.api.v1.endpoints.agent.agent_service.get_messages_by_session", new_callable=AsyncMock) as mock_get_messages:

        # Mockar a chamada interna ao supabase async client para retornar sessão de outro user
        mock_supabase_session_data = {"id": str(session_id), "user_id": str(other_user_id), "created_at": now.isoformat(), "updated_at": now.isoformat(), "title": "Forbidden Session"}
        mock_supabase_response = MagicMock()
        mock_supabase_response.data = mock_supabase_session_data
        mock_supabase_response.error = None # <<< ADICIONADO: Explicitar que não houve erro

        # --- Correção do Mock --- 
        mock_execute = AsyncMock(return_value=mock_supabase_response) # <<< CORRIGIDO
        mock_async_client = MagicMock()
        mock_async_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute = mock_execute
        app.dependency_overrides[get_supabase_client] = lambda: mock_async_client

        # Patch para o middleware usar o mesmo mock do cliente Supabase
        with patch("app.middleware.get_supabase_client", return_value=mock_supabase_auth):
            # Adicionar token fictício no cabeçalho de autenticação
            headers = {"Authorization": "Bearer fake-test-token"}
            response = await test_client.get(f"/api/v1/agent/sessions/{session_id}/messages", headers=headers)

            assert response.status_code == 403
            assert response.json()["detail"] == "Acesso não autorizado a esta sessão"

            # Verificar mocks da cadeia Supabase Async
            mock_async_client.table.assert_called_once_with("sessions")
            mock_async_client.table.return_value.select.assert_called_once_with("id, user_id")
            mock_async_client.table.return_value.select.return_value.eq.assert_called_once_with("id", str(session_id))
            mock_async_client.table.return_value.select.return_value.eq.return_value.maybe_single.assert_called_once()
            mock_execute.assert_awaited_once() # <<< CORRIGIDO

            mock_get_messages.assert_not_called() # Não foi awaited
            
            # Verificar se o middleware tentou validar o token
            mock_supabase_auth.auth.get_user.assert_awaited_once_with("fake-test-token")

    # Limpar overrides após o teste
    app.dependency_overrides.clear()


# --- Test POST /api/v1/agent/chat ---

@pytest.mark.asyncio
async def test_handle_chat_message_existing_session(
    test_client: AsyncClient,
    test_user: UserRead, # auth_headers removido
    supabase_test_client: SupabaseClient, # Usar cliente sync se aplicável
    mocker
):
    """Tests sending a message to an existing session."""
    session_id = uuid.uuid4()
    now = datetime.now()
    user_message_content = "Tell me a joke"
    assistant_response_content = "Why don't scientists trust atoms? Because they make up everything!"
    request_payload = {"query": user_message_content, "session_id": str(session_id)}

    # Garantir que test_user.id seja UUID
    # Mock da resposta da verificação da sessão
    mock_session_check_response = MagicMock()
    mock_session_check_response.data = {"id": str(session_id), "user_id": str(test_user.id)}
    mock_session_check_response.error = None

    mock_history_data = [
        {"role": "user", "content": "Previous message"}
    ]
    # Converter IDs para string nos mocks
    mock_new_user_message = {"id": str(uuid.uuid4()), "session_id": str(session_id), "role": "user", "content": user_message_content, "created_at": now.isoformat(), "user_id": str(test_user.id)}
    mock_assistant_message = {"id": str(uuid.uuid4()), "session_id": str(session_id), "role": "assistant", "content": assistant_response_content, "created_at": now.isoformat(), "user_id": str(test_user.id)}

    # ---- Mock do Cliente Supabase Async ----
    mock_supabase_async_client = AsyncMock(spec=AsyncClient)
    # Configurar o mock para a chamada table().select().eq().maybe_single().execute()
    mock_execute_method = AsyncMock(return_value=mock_session_check_response)
    mock_maybe_single_method = MagicMock()
    mock_maybe_single_method.execute = mock_execute_method
    mock_eq_method = MagicMock()
    mock_eq_method.maybe_single = MagicMock(return_value=mock_maybe_single_method)
    mock_select_method = MagicMock()
    mock_select_method.eq = MagicMock(return_value=mock_eq_method)
    mock_table_method = MagicMock()
    mock_table_method.select = MagicMock(return_value=mock_select_method)
    mock_supabase_async_client.table = MagicMock(return_value=mock_table_method)
    # ---- Fim Mock Supabase ----
    
    # Criar um mock do cliente Supabase para o middleware
    mock_supabase_auth = MagicMock(spec=SupabaseAsyncClient)
    mock_supabase_auth.auth = MagicMock()
    
    # Configurar o mock para retornar o test_user quando auth.get_user for chamado
    mock_auth_response = MagicMock()
    mock_auth_response.user = MagicMock()
    mock_auth_response.user.id = str(test_user.id)
    mock_auth_response.user.email = test_user.email
    mock_auth_response.user.user_metadata = {'username': test_user.username}
    mock_supabase_auth.auth.get_user = AsyncMock(return_value=mock_auth_response)

    # Override das dependências
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase_async_client # Adicionado override

    # Mockar chamadas ao agent_service, Runner e ContextVar
    with patch("app.api.v1.endpoints.agent.agent_service.get_messages_by_session", new_callable=AsyncMock, return_value=mock_history_data) as mock_get_messages, \
         patch("app.api.v1.endpoints.agent.agent_service.add_message", new_callable=AsyncMock, side_effect=[mock_new_user_message, mock_assistant_message]) as mock_add_message, \
         patch("app.api.v1.endpoints.agent.Runner.run", new_callable=AsyncMock, return_value=assistant_response_content) as mock_runner_run, \
         patch("app.api.v1.endpoints.agent.brain_agent", MagicMock()) as mock_brain_agent, \
         patch("app.api.v1.endpoints.agent.current_user_id_var") as mock_context_var, \
         patch("app.middleware.get_supabase_client", return_value=mock_supabase_auth):

        # Adicionar token fictício no cabeçalho de autenticação
        headers = {"Authorization": "Bearer fake-test-token"}
        response = await test_client.post("/api/v1/agent/chat", json=request_payload, headers=headers)

        assert response.status_code == 200
        
        # Verificar se o middleware tentou validar o token
        mock_supabase_auth.auth.get_user.assert_awaited_once_with("fake-test-token")
        
        response_data = response.json()
        assert response_data["success"] is True
        assert "assistant_content" in response_data
        assert response_data["assistant_content"] == assistant_response_content
        assert "user_message_id" in response_data
        assert "assistant_message_id" in response_data
        assert "session_id" in response_data
        assert response_data["session_id"] == str(session_id)

        # Verificar mock_table e mock_add_message
        mock_supabase_async_client.table.assert_called_with("sessions")
        mock_get_messages.assert_awaited_once_with(supabase=ANY, session_id=session_id)
        mock_add_message.assert_has_awaits([
            mocker.call(
                supabase=ANY,
                session_id=session_id,
                content=user_message_content,
                role="user",
                user_id=test_user.id
            ),
            mocker.call(
                supabase=ANY,
                session_id=session_id,
                content=assistant_response_content,
                role="assistant",
                user_id=test_user.id
            )
        ])
        mock_runner_run.assert_awaited_once()

    # Limpar overrides após o teste
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_handle_chat_message_new_session(
    test_client: AsyncClient,
    test_user: UserRead, # auth_headers removido
    supabase_test_client: SupabaseClient, # Usar cliente sync se aplicável
    mocker
):
    """Tests sending a message without a session_id, creating a new one."""
    new_session_id = uuid.uuid4()
    now = datetime.now()
    user_message_content = "What is the weather?"
    assistant_response_content = "The weather is sunny."
    request_payload = {"query": user_message_content, "session_id": None} # No session_id

    # Garantir que test_user.id seja UUID
    mock_new_session = {"id": new_session_id, "user_id": test_user.id, "created_at": now, "updated_at": now, "title": user_message_content[:50]}
    mock_new_user_message = {"id": uuid.uuid4(), "session_id": new_session_id, "role": "user", "content": user_message_content, "created_at": now, "user_id": test_user.id}
    mock_assistant_message = {"id": uuid.uuid4(), "session_id": new_session_id, "role": "assistant", "content": assistant_response_content, "created_at": now, "user_id": test_user.id}

    # Criar um mock do cliente Supabase para o middleware
    mock_supabase_auth = MagicMock(spec=SupabaseAsyncClient)
    mock_supabase_auth.auth = MagicMock()
    
    # Configurar o mock para retornar o test_user quando auth.get_user for chamado
    mock_auth_response = MagicMock()
    mock_auth_response.user = MagicMock()
    mock_auth_response.user.id = str(test_user.id)
    mock_auth_response.user.email = test_user.email
    mock_auth_response.user.user_metadata = {'username': test_user.username}
    mock_supabase_auth.auth.get_user = AsyncMock(return_value=mock_auth_response)

    # Override da dependência get_current_user
    app.dependency_overrides[get_current_user] = lambda: test_user

    # Mockar chamadas ao agent_service, Runner, etc.
    with patch("app.api.v1.endpoints.agent.agent_service.create_session", return_value=mock_new_session) as mock_create_session, \
         patch("app.api.v1.endpoints.agent.agent_service.get_messages_by_session") as mock_get_messages, \
         patch("app.api.v1.endpoints.agent.agent_service.add_message", side_effect=[mock_new_user_message, mock_assistant_message]) as mock_add_message, \
         patch("app.api.v1.endpoints.agent.Runner.run", return_value=assistant_response_content) as mock_runner_run, \
         patch("app.api.v1.endpoints.agent.brain_agent", MagicMock()) as mock_brain_agent, \
         patch("app.api.v1.endpoints.agent.current_user_id_var") as mock_context_var, \
         patch("app.middleware.get_supabase_client", return_value=mock_supabase_auth):

        # A verificação de sessão existente não deve ocorrer aqui, então não mockamos supabase.table

        # Adicionar token fictício no cabeçalho de autenticação
        headers = {"Authorization": "Bearer fake-test-token"}
        response = await test_client.post("/api/v1/agent/chat", json=request_payload, headers=headers)

        assert response.status_code == 200
        
        # Verificar se o middleware tentou validar o token
        mock_supabase_auth.auth.get_user.assert_awaited_once_with("fake-test-token")
        
        response_data = response.json()
        assert response_data["success"] is True
        assert "session_id" in response_data
        assert response_data["session_id"] == str(new_session_id)
        assert "assistant_content" in response_data
        assert response_data["assistant_content"] == assistant_response_content

        # Verificar chamadas
        mock_create_session.assert_called_once_with(
            supabase=ANY,
            user_id=test_user.id
        )
        mock_get_messages.assert_not_called() # Não deve chamar o histórico para uma nova sessão
        assert mock_add_message.call_count == 2
        # Primeira chamada: user message
        mock_add_message.assert_any_call(
            supabase=ANY,
            session_id=new_session_id,
            content=user_message_content,
            role="user",
            user_id=test_user.id
        )
        # Segunda chamada: assistant message
        mock_add_message.assert_any_call(
            supabase=ANY,
            session_id=new_session_id,
            content=assistant_response_content,
            role="assistant",
            user_id=test_user.id
        )
        mock_runner_run.assert_called_once() # Assert de chamada básica

    # Limpar overrides após o teste
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_handle_chat_message_session_not_found(
    test_client: AsyncClient,
    test_user: UserRead, # auth_headers removido
    supabase_test_client: SupabaseClient, # Usar cliente sync se aplicável
    mocker
):
    """Tests sending a message with a non-existent session_id."""
    non_existent_session_id = uuid.uuid4()
    request_payload = {"query": "Hello?", "session_id": str(non_existent_session_id)}

    # 1. Preparar a resposta mockada do Supabase (sessão não encontrada)
    mock_supabase_response = MagicMock()
    mock_supabase_response.data = None # <<< A resposta correta para not_found
    mock_supabase_response.error = None # <<< Importante: Nenhum erro do DB

    # 2. Criar um AsyncMock para o Supabase Async Client
    mock_supabase_async_client = AsyncMock(spec=SupabaseAsyncClient)

    # 3. Preparar o AsyncMock para o resultado final da chamada execute
    mock_execute = AsyncMock(return_value=mock_supabase_response)

    # 4. Configurar a cadeia de mocks passo a passo
    mock_table_builder = MagicMock()
    mock_select_builder = MagicMock()
    mock_eq_builder = MagicMock()
    mock_maybe_single_builder = MagicMock()

    mock_supabase_async_client.table.return_value = mock_table_builder
    mock_table_builder.select.return_value = mock_select_builder
    mock_select_builder.eq.return_value = mock_eq_builder
    mock_eq_builder.maybe_single.return_value = mock_maybe_single_builder
    mock_maybe_single_builder.execute = mock_execute # O final é async
    
    # Criar um mock do cliente Supabase para o middleware
    mock_supabase_auth = MagicMock(spec=SupabaseAsyncClient)
    mock_supabase_auth.auth = MagicMock()
    
    # Configurar o mock para retornar o test_user quando auth.get_user for chamado
    mock_auth_response = MagicMock()
    mock_auth_response.user = MagicMock()
    mock_auth_response.user.id = str(test_user.id)
    mock_auth_response.user.email = test_user.email
    mock_auth_response.user.user_metadata = {'username': test_user.username}
    mock_supabase_auth.auth.get_user = AsyncMock(return_value=mock_auth_response)

    # 5. Sobrescrever as dependências
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase_async_client

    # 6. Mockar outros serviços que não devem ser chamados
    with patch("app.api.v1.endpoints.agent.agent_service.get_messages_by_session") as mock_get_messages, \
         patch("app.api.v1.endpoints.agent.agent_service.add_message") as mock_add_message, \
         patch("app.api.v1.endpoints.agent.Runner.run") as mock_runner_run, \
         patch("app.middleware.get_supabase_client", return_value=mock_supabase_auth):

        # 7. Fazer a chamada à API
        headers = {"Authorization": "Bearer fake-test-token"}
        response = await test_client.post("/api/v1/agent/chat", json=request_payload, headers=headers)

        # 8. Verificar a resposta
        assert response.status_code == 404
        assert "não encontrada" in response.json()["detail"]
        
        # Verificar se o middleware tentou validar o token
        mock_supabase_auth.auth.get_user.assert_awaited_once_with("fake-test-token")

        # 9. Verificar que a cadeia de mocks foi chamada corretamente
        mock_supabase_async_client.table.assert_called_once_with("sessions")
        mock_table_builder.select.assert_called_once_with("id, user_id")
        mock_select_builder.eq.assert_called_once_with("id", str(non_existent_session_id))
        mock_eq_builder.maybe_single.assert_called_once()
        mock_execute.assert_awaited_once()

        # 10. Verificar que nenhum outro método foi chamado já que a sessão não foi encontrada
        mock_get_messages.assert_not_called()
        mock_add_message.assert_not_called()
        mock_runner_run.assert_not_called()

    # Limpar overrides após o teste
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_handle_chat_message_forbidden(
    test_client: AsyncClient,
    test_user: UserRead,
    mocker
):
    """Tests sending a message to a session belonging to another user."""
    session_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    now = datetime.now()
    request_payload = {"query": "Can I access this?", "session_id": str(session_id)}

    # 1. Preparar a resposta mockada do Supabase
    mock_supabase_session_data = {"id": str(session_id), "user_id": str(other_user_id), "created_at": now.isoformat(), "updated_at": now.isoformat(), "title": "Forbidden Session"}
    mock_supabase_response = MagicMock()
    mock_supabase_response.data = mock_supabase_session_data
    mock_supabase_response.error = None

    # 2. Criar um AsyncMock para o Supabase Async Client
    mock_supabase_async_client = AsyncMock(spec=SupabaseAsyncClient)

    # 3. Preparar o AsyncMock para o resultado final da chamada execute
    mock_execute = AsyncMock(return_value=mock_supabase_response)

    # 4. Configurar a cadeia de mocks passo a passo
    mock_table_builder = MagicMock()
    mock_select_builder = MagicMock()
    mock_eq_builder = MagicMock()
    mock_maybe_single_builder = MagicMock()

    # Configurar o retorno de cada passo da cadeia
    mock_supabase_async_client.table.return_value = mock_table_builder
    mock_table_builder.select.return_value = mock_select_builder
    mock_select_builder.eq.return_value = mock_eq_builder
    mock_eq_builder.maybe_single.return_value = mock_maybe_single_builder
    # Atribuir o AsyncMock ao método execute do último builder
    mock_maybe_single_builder.execute = mock_execute
    
    # Criar um mock do cliente Supabase para o middleware
    mock_supabase_auth = MagicMock(spec=SupabaseAsyncClient)
    mock_supabase_auth.auth = MagicMock()
    
    # Configurar o mock para retornar o test_user quando auth.get_user for chamado
    mock_auth_response = MagicMock()
    mock_auth_response.user = MagicMock()
    mock_auth_response.user.id = str(test_user.id)
    mock_auth_response.user.email = test_user.email
    mock_auth_response.user.user_metadata = {'username': test_user.username}
    mock_supabase_auth.auth.get_user = AsyncMock(return_value=mock_auth_response)

    # 5. Sobrescrever as dependências
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase_async_client

    # 6. Mockar outros serviços que não devem ser chamados
    with patch("app.api.v1.endpoints.agent.agent_service.get_messages_by_session") as mock_get_messages, \
         patch("app.api.v1.endpoints.agent.agent_service.add_message") as mock_add_message, \
         patch("app.api.v1.endpoints.agent.Runner.run") as mock_runner_run, \
         patch("app.middleware.get_supabase_client", return_value=mock_supabase_auth):

        # 7. Fazer a chamada à API
        headers = {"Authorization": "Bearer fake-test-token"}
        response = await test_client.post("/api/v1/agent/chat", json=request_payload, headers=headers)

        # 8. Verificar a resposta
        assert response.status_code == 403
        assert response.json()["detail"] == "Acesso não autorizado a esta sessão"
        
        # Verificar se o middleware tentou validar o token
        mock_supabase_auth.auth.get_user.assert_awaited_once_with("fake-test-token")

        # 9. Verificar que a busca da sessão foi feita corretamente
        mock_supabase_async_client.table.assert_called_once_with("sessions")
        mock_table_builder.select.assert_called_once_with("id, user_id")
        mock_select_builder.eq.assert_called_once_with("id", str(session_id))
        mock_eq_builder.maybe_single.assert_called_once()
        mock_execute.assert_awaited_once()

        # 10. Verificar que nenhum outro método foi chamado já que o acesso foi negado
        mock_get_messages.assert_not_called()
        mock_add_message.assert_not_called()
        mock_runner_run.assert_not_called()

    # Limpar overrides após o teste
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_handle_chat_message_runner_error(
    test_client: AsyncClient,
    test_user: UserRead,
    mocker # Remover supabase_test_client, não é necessário aqui
):
    """Tests error handling when the Agent Runner fails."""
    session_id = uuid.uuid4()
    now = datetime.now()
    user_message_content = "Cause an error"
    request_payload = {"query": user_message_content, "session_id": str(session_id)}

    mock_supabase_session_data = {"id": str(session_id), "user_id": str(test_user.id), "created_at": now.isoformat(), "updated_at": now.isoformat(), "title": "Error Session"}
    mock_history_data = []
    mock_new_user_message = {"id": uuid.uuid4(), "session_id": session_id, "role": "user", "content": user_message_content, "created_at": now, "user_id": test_user.id}

    # Criar um mock do cliente Supabase para o middleware
    mock_supabase_auth = MagicMock(spec=SupabaseAsyncClient)
    mock_supabase_auth.auth = MagicMock()
    
    # Configurar o mock para retornar o test_user quando auth.get_user for chamado
    mock_auth_response = MagicMock()
    mock_auth_response.user = MagicMock()
    mock_auth_response.user.id = str(test_user.id)
    mock_auth_response.user.email = test_user.email
    mock_auth_response.user.user_metadata = {'username': test_user.username}
    mock_supabase_auth.auth.get_user = AsyncMock(return_value=mock_auth_response)

    # Override da dependência get_current_user
    app.dependency_overrides[get_current_user] = lambda: test_user

    # --- Mock Supabase Async Client ---
    mock_supabase_async_client = AsyncMock(spec=SupabaseAsyncClient)
    mock_supabase_response = MagicMock()
    mock_supabase_response.data = mock_supabase_session_data
    mock_supabase_response.error = None # Importante para não gerar DatabaseError

    mock_execute = AsyncMock(return_value=mock_supabase_response)
    mock_table_builder = MagicMock()
    mock_select_builder = MagicMock()
    mock_eq_builder = MagicMock()
    mock_maybe_single_builder = MagicMock()

    mock_supabase_async_client.table.return_value = mock_table_builder
    mock_table_builder.select.return_value = mock_select_builder
    mock_select_builder.eq.return_value = mock_eq_builder
    mock_eq_builder.maybe_single.return_value = mock_maybe_single_builder
    mock_maybe_single_builder.execute = mock_execute

    # Override da dependência get_supabase_client
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase_async_client
    # --- Fim Mock Supabase Async Client ---

    # Mockar chamadas assíncronas, fazendo Runner.run levantar uma exceção
    # Usar AsyncMock para funções async
    with patch("app.api.v1.endpoints.agent.agent_service.get_messages_by_session", new_callable=AsyncMock, return_value=mock_history_data) as mock_get_messages, \
         patch("app.api.v1.endpoints.agent.agent_service.add_message", new_callable=AsyncMock, return_value=mock_new_user_message) as mock_add_message, \
         patch("app.api.v1.endpoints.agent.Runner.run", new_callable=AsyncMock, side_effect=Exception("Agent failed to run")) as mock_runner_run, \
         patch("app.api.v1.endpoints.agent.brain_agent", MagicMock()) as mock_brain_agent, \
         patch("app.api.v1.endpoints.agent.current_user_id_var") as mock_context_var, \
         patch("app.middleware.get_supabase_client", return_value=mock_supabase_auth):

        headers = {"Authorization": "Bearer fake-test-token"}
        response = await test_client.post("/api/v1/agent/chat", json=request_payload, headers=headers)

        assert response.status_code == 500
        assert "Erro interno ao processar mensagem" in response.json()["detail"]
        
        # Verificar se o middleware tentou validar o token
        mock_supabase_auth.auth.get_user.assert_awaited_once_with("fake-test-token")

        # Verificar que a mensagem do usuário foi salva, mas não houve resposta
        mock_add_message.assert_awaited_once()
        mock_runner_run.assert_awaited_once()
        mock_context_var.set.assert_called_once()
        mock_context_var.reset.assert_called_once()

    # Limpar overrides após o teste
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_handle_chat_message_add_assistant_message_error(
    test_client: AsyncClient,
    test_user: UserRead, # auth_headers e supabase_test_client removidos
    mocker # Adicionar mocker se não estiver presente
):
    """Tests error handling when saving the assistant's message fails."""
    session_id = uuid.uuid4()
    now = datetime.now()
    user_message_content = "Save error test"
    assistant_response_content = "I should not be saved."
    request_payload = {"query": user_message_content, "session_id": str(session_id)}

    # Garantir que test_user.id seja UUID
    mock_supabase_session_data = {"id": str(session_id), "user_id": str(test_user.id), "created_at": now.isoformat(), "updated_at": now.isoformat(), "title": "Save Error Test"}
    mock_history_data = []
    # add_message retorna um dict com UUID, não um objeto inteiro
    mock_new_user_message_dict = {"id": uuid.uuid4(), "session_id": session_id, "role": "user", "content": user_message_content, "created_at": now, "user_id": test_user.id}

    # Criar um mock do cliente Supabase para o middleware
    mock_supabase_auth = MagicMock(spec=SupabaseAsyncClient)
    mock_supabase_auth.auth = MagicMock()
    
    # Configurar o mock para retornar o test_user quando auth.get_user for chamado
    mock_auth_response = MagicMock()
    mock_auth_response.user = MagicMock()
    mock_auth_response.user.id = str(test_user.id)
    mock_auth_response.user.email = test_user.email
    mock_auth_response.user.user_metadata = {'username': test_user.username}
    mock_supabase_auth.auth.get_user = AsyncMock(return_value=mock_auth_response)

    # Override da dependência get_current_user
    app.dependency_overrides[get_current_user] = lambda: test_user

    # --- Configurar Mock Supabase Async ---
    mock_supabase_async_client = AsyncMock(spec=SupabaseAsyncClient)
    mock_supabase_response = MagicMock()
    mock_supabase_response.data = mock_supabase_session_data
    mock_supabase_response.error = None # Importante

    mock_execute = AsyncMock(return_value=mock_supabase_response)

    # Construir cadeia de builders
    mock_table_builder = MagicMock()
    mock_select_builder = MagicMock()
    mock_eq_builder = MagicMock()
    mock_maybe_single_builder = MagicMock()

    # Ligar cadeia de mocks
    mock_supabase_async_client.table.return_value = mock_table_builder
    mock_table_builder.select.return_value = mock_select_builder
    mock_select_builder.eq.return_value = mock_eq_builder
    mock_eq_builder.maybe_single.return_value = mock_maybe_single_builder
    mock_maybe_single_builder.execute = mock_execute

    # Aplicar override da dependência do cliente supabase
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase_async_client
    # --- Fim Mock Supabase Async ---

    # Mockar chamadas de serviço e runner, fazendo a segunda chamada a add_message falhar
    # patch cria AsyncMock automaticamente para funções async
    with patch("app.api.v1.endpoints.agent.agent_service.get_messages_by_session", return_value=mock_history_data) as mock_get_messages, \
         patch("app.api.v1.endpoints.agent.agent_service.add_message", side_effect=[mock_new_user_message_dict, Exception("Failed to save assistant message")]) as mock_add_message, \
         patch("app.api.v1.endpoints.agent.Runner.run", return_value=assistant_response_content) as mock_runner_run, \
         patch("app.api.v1.endpoints.agent.brain_agent", MagicMock()) as mock_brain_agent, \
         patch("app.api.v1.endpoints.agent.current_user_id_var") as mock_context_var, \
         patch("app.middleware.get_supabase_client", return_value=mock_supabase_auth):

        # Adicionar token fictício no cabeçalho de autenticação
        headers = {"Authorization": "Bearer fake-test-token"}
        response = await test_client.post("/api/v1/agent/chat", json=request_payload, headers=headers)

        assert response.status_code == 500
        assert "Erro interno ao processar mensagem" in response.json()["detail"]
        
        # Verificar se o middleware tentou validar o token
        mock_supabase_auth.auth.get_user.assert_awaited_once_with("fake-test-token")

        # Verificar chamadas feitas
        mock_add_message.assert_has_calls([
            mocker.call(
                supabase=ANY,
                session_id=session_id, 
                content=user_message_content, 
                role="user", 
                user_id=test_user.id
            ),
            mocker.call(
                supabase=ANY,
                session_id=session_id, 
                content=assistant_response_content, 
                role="assistant", 
                user_id=test_user.id
            )
        ])
        mock_runner_run.assert_called_once()

    # Limpar overrides após o teste
    app.dependency_overrides.clear()

