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

            mock_get_messages.assert_not_called() # Não deve chamar o histórico para uma nova sessão
            
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

            mock_get_messages.assert_not_called() # Não deve chamar o histórico para uma nova sessão
            
            # Verificar se o middleware tentou validar o token
            mock_supabase_auth.auth.get_user.assert_awaited_once_with("fake-test-token")

    # Limpar overrides após o teste
    app.dependency_overrides.clear()


# --- Test POST /api/v1/agent/chat ---

@pytest.mark.asyncio
async def test_handle_chat_message_existing_session(
    test_client: AsyncClient,
    test_user: UserRead, # auth_headers removido
    mocker # Remover supabase_test_client, usar mocker/patch
):
    """ Test chat with an existing session, mocking process_message. """
    session_id = uuid.uuid4()
    user_message_id = uuid.uuid4()
    assistant_message_id = uuid.uuid4()
    user_query = "Me conte uma piada"
    assistant_response = "Por que o esqueleto não foi à festa? Porque ele não tinha corpo para ir!"

    # Override da dependência get_current_user
    app.dependency_overrides[get_current_user] = lambda: test_user

    # Criar um mock do cliente Supabase para o middleware
    mock_supabase_auth = MagicMock(spec=SupabaseAsyncClient)
    mock_supabase_auth.auth = MagicMock()
    mock_auth_response = MagicMock()
    mock_auth_response.user = MagicMock()
    mock_auth_response.user.id = str(test_user.id)
    mock_auth_response.user.email = test_user.email
    mock_auth_response.user.user_metadata = {'username': test_user.username}
    mock_supabase_auth.auth.get_user = AsyncMock(return_value=mock_auth_response)

    # Mockar a chamada interna ao supabase client para verificação da sessão
    mock_supabase_session_data = {"id": str(session_id), "user_id": str(test_user.id)}
    mock_supabase_check_response = MagicMock()
    mock_supabase_check_response.data = mock_supabase_session_data
    mock_supabase_check_response.error = None
    mock_execute_check = AsyncMock(return_value=mock_supabase_check_response)

    # Mockar o get_messages_by_session para retornar histórico vazio (ou algum histórico)
    mock_get_messages = mocker.patch(
        "app.api.v1.endpoints.agent.agent_service.get_messages_by_session",
        new_callable=AsyncMock,
        return_value=[] # Sem histórico neste exemplo
    )
    
    # Mockar o add_message para a mensagem do usuário
    mock_add_user_msg = mocker.patch(
        "app.api.v1.endpoints.agent.agent_service.add_message",
        new_callable=AsyncMock,
        # Simular retorno da mensagem do usuário salva e depois da do assistente
        side_effect=[
            {"id": user_message_id, "role": "user", "content": user_query},
            {"id": assistant_message_id, "role": "assistant", "content": assistant_response}
        ]
    )
    
    # **** NOVO: Mockar process_message ****
    mock_process_message = mocker.patch(
        "app.voxy_agents.brain.process_message",
        new_callable=AsyncMock,
        return_value=assistant_response
    )
    
    # --- Correção do Mock do Cliente Supabase --- 
    # (Necessário para a verificação da sessão feita ANTES de process_message)
    mock_async_client = MagicMock()
    mock_async_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute = mock_execute_check
    app.dependency_overrides[get_supabase_client] = lambda: mock_async_client

    # Patch para o middleware usar o mesmo mock do cliente Supabase para autenticação
    with patch("app.middleware.get_supabase_client", return_value=mock_supabase_auth):
        # Adicionar token fictício no cabeçalho de autenticação
        headers = {"Authorization": "Bearer fake-test-token"}
        
        # **** MUDANÇA: Usar 'data' em vez de 'json' ****
        data = {"query": user_query, "session_id": str(session_id)}
        
        response = await test_client.post("/api/v1/agent/chat", headers=headers, data=data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] == True
        assert response_data["session_id"] == str(session_id)
        assert response_data["user_message_id"] == str(user_message_id)
        assert response_data["assistant_content"] == assistant_response
        assert response_data["assistant_message_id"] == str(assistant_message_id)

        # Verificar chamadas mocks
        mock_supabase_auth.auth.get_user.assert_awaited_once_with("fake-test-token")
        mock_async_client.table.assert_called_once_with("sessions") # Verificação da sessão
        mock_get_messages.assert_awaited_once_with(supabase=ANY, session_id=session_id)
        
        # Verificar add_message (chamado duas vezes)
        assert mock_add_user_msg.await_count == 2
        # Primeira chamada (usuário)
        call_args_user = mock_add_user_msg.await_args_list[0]
        assert call_args_user.kwargs['role'] == 'user'
        assert call_args_user.kwargs['content'] == user_query
        assert call_args_user.kwargs['session_id'] == session_id
        # Segunda chamada (assistente)
        call_args_assistant = mock_add_user_msg.await_args_list[1]
        assert call_args_assistant.kwargs['role'] == 'assistant'
        assert call_args_assistant.kwargs['content'] == assistant_response
        assert call_args_assistant.kwargs['session_id'] == session_id
        
        # Verificar process_message
        mock_process_message.assert_awaited_once()
        # Verificar args passados para process_message
        args_pm, kwargs_pm = mock_process_message.await_args
        assert kwargs_pm['message_content'] == user_query # Sem info de imagem neste teste
        assert kwargs_pm['user_id'] == test_user.id # Comparar UUID com UUID, não com string
        assert kwargs_pm['run_context'] == {} # Era None, agora espera um dicionário vazio

    # Limpar overrides após o teste
    app.dependency_overrides.clear()


# Adicionar NOVO teste para chat com image_path
@pytest.mark.asyncio
async def test_handle_chat_message_with_image_path(
    test_client: AsyncClient,
    test_user: UserRead,
    mocker
):
    """ Test chat sending an image_path, mocking create_signed_url and process_message. """
    session_id = uuid.uuid4()
    user_message_id = uuid.uuid4()
    assistant_message_id = uuid.uuid4()
    user_query = "O que você vê nesta imagem?"
    image_path_sent = "user_uploads/nice_cat.jpg"
    signed_url_mock = "https://supabase.example/signed/nice_cat.jpg?token=123"
    assistant_response = "Vejo um gato fofo!"

    # Override da dependência get_current_user
    app.dependency_overrides[get_current_user] = lambda: test_user

    # Mock do cliente Supabase para autenticação no middleware
    mock_supabase_auth = MagicMock(spec=SupabaseAsyncClient)
    mock_supabase_auth.auth = MagicMock()
    mock_auth_response = MagicMock()
    mock_auth_response.user = MagicMock()
    mock_auth_response.user.id = str(test_user.id)
    mock_auth_response.user.email = test_user.email
    mock_auth_response.user.user_metadata = {'username': test_user.username}
    mock_supabase_auth.auth.get_user = AsyncMock(return_value=mock_auth_response)

    # Mock para verificação da sessão existente
    mock_supabase_session_data = {"id": str(session_id), "user_id": str(test_user.id)}
    mock_supabase_check_response = MagicMock()
    mock_supabase_check_response.data = mock_supabase_session_data
    mock_supabase_check_response.error = None
    mock_execute_check = AsyncMock(return_value=mock_supabase_check_response)

    # Mock get_messages_by_session
    mock_get_messages = mocker.patch(
        "app.api.v1.endpoints.agent.agent_service.get_messages_by_session",
        new_callable=AsyncMock,
        return_value=[]
    )
    
    # Mock add_message
    mock_add_user_msg = mocker.patch(
        "app.api.v1.endpoints.agent.agent_service.add_message",
        new_callable=AsyncMock,
        side_effect=[
            {"id": user_message_id, "role": "user", "content": user_query},
            {"id": assistant_message_id, "role": "assistant", "content": assistant_response}
        ]
    )
    
    # **** NOVO: Mockar create_signed_url ****
    mock_create_signed_url = mocker.patch(
        "app.api.v1.endpoints.agent.create_signed_url",
        new_callable=AsyncMock,
        return_value={'signedURL': signed_url_mock, 'error': None}
    )
    
    # **** Mockar process_message ****
    mock_process_message = mocker.patch(
        "app.voxy_agents.brain.process_message",
        new_callable=AsyncMock,
        return_value=assistant_response
    )
    
    # Mock do cliente Supabase Async para a rota (verificação de sessão)
    mock_async_client = MagicMock()
    mock_async_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute = mock_execute_check
    app.dependency_overrides[get_supabase_client] = lambda: mock_async_client

    # Patch para autenticação no middleware
    with patch("app.middleware.get_supabase_client", return_value=mock_supabase_auth):
        headers = {"Authorization": "Bearer fake-test-token"}
        
        # **** MUDANÇA: Usar 'data' e incluir 'image_path' ****
        data = {
            "query": user_query, 
            "session_id": str(session_id), 
            "image_path": image_path_sent
        }
        
        response = await test_client.post("/api/v1/agent/chat", headers=headers, data=data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] == True
        assert response_data["assistant_content"] == assistant_response

        # Verificar mocks
        mock_create_signed_url.assert_awaited_once_with(
            supabase=ANY,
            file_path=image_path_sent,
            expires_in=300
        )
        
        # Verificar que process_message foi chamado com o contexto correto
        mock_process_message.assert_awaited_once()
        args_pm, kwargs_pm = mock_process_message.await_args
        # O message_content passado para o agente deve ter a info da imagem anexada
        expected_message_content = f"{user_query} [Image Uploaded: {image_path_sent}]"
        assert kwargs_pm['message_content'] == expected_message_content
        assert kwargs_pm['user_id'] == test_user.id # Comparar UUID com UUID, não com string
        assert kwargs_pm['run_context'] is not None
        assert 'image_request' in kwargs_pm['run_context']
        # Verificar o conteúdo do ImageRequest dentro do contexto
        image_request_in_context = kwargs_pm['run_context']['image_request']
        assert image_request_in_context.source == 'url'
        assert image_request_in_context.content == signed_url_mock

    # Limpar overrides
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
    # Modificação: Mudar de dict para FormData (application/x-www-form-urlencoded)
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
    with patch("app.api.v1.endpoints.agent.agent_service.create_session", new_callable=AsyncMock, return_value=mock_new_session) as mock_create_session, \
         patch("app.api.v1.endpoints.agent.agent_service.get_messages_by_session", new_callable=AsyncMock) as mock_get_messages, \
         patch("app.api.v1.endpoints.agent.agent_service.add_message", new_callable=AsyncMock, side_effect=[mock_new_user_message, mock_assistant_message]) as mock_add_message, \
         patch("app.api.v1.endpoints.agent.Runner.run", return_value=MagicMock(final_output=assistant_response_content)) as mock_runner_run, \
         patch("app.api.v1.endpoints.agent.brain_agent", MagicMock()) as mock_brain_agent, \
         patch("app.api.v1.endpoints.agent.current_user_id_var") as mock_context_var, \
         patch("app.voxy_agents.brain.process_message", new_callable=AsyncMock, return_value=assistant_response_content) as mock_process_message, \
         patch("app.middleware.get_supabase_client", return_value=mock_supabase_auth):

        # A verificação de sessão existente não deve ocorrer aqui, então não mockamos supabase.table

        # Adicionar token fictício no cabeçalho de autenticação
        headers = {"Authorization": "Bearer fake-test-token"}
        
        # MODIFICAÇÃO: Enviar como form-data
        form_data = {
            "query": user_message_content,
            # Não enviar session_id ou enviar como string "None" se for obrigatório
        }
        
        response = await test_client.post("/api/v1/agent/chat", data=form_data, headers=headers)

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
        mock_create_session.assert_awaited_once_with(
            supabase=ANY,
            user_id=test_user.id
        )
        mock_get_messages.assert_not_called() # Não deve chamar o histórico para uma nova sessão
        assert mock_add_message.await_count == 2
        
        # Verificar as chamadas manualmente usando await_args_list
        call_args_list = mock_add_message.await_args_list
        
        # Verificar que há uma chamada para a mensagem do usuário
        user_message_call = any(
            call.kwargs.get('role') == 'user' and 
            call.kwargs.get('content') == user_message_content and
            call.kwargs.get('session_id') == new_session_id and
            call.kwargs.get('user_id') == test_user.id
            for call in call_args_list
        )
        assert user_message_call, "Não encontrou chamada esperada para mensagem do usuário"
        
        # Verificar que há uma chamada para a mensagem do assistente
        assistant_message_call = any(
            call.kwargs.get('role') == 'assistant' and 
            call.kwargs.get('content') == assistant_response_content and
            call.kwargs.get('session_id') == new_session_id and
            call.kwargs.get('user_id') == test_user.id
            for call in call_args_list
        )
        assert assistant_message_call, "Não encontrou chamada esperada para mensagem do assistente"
        
        # Verificar que process_message foi chamado em vez de Runner.run
        mock_process_message.assert_awaited_once()

    # Limpar overrides após o teste
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_handle_chat_message_session_not_found(
    test_client: AsyncClient,
    test_user: UserRead, # auth_headers removido
    supabase_test_client: SupabaseClient, # Usar cliente sync se aplicável
    mocker
):
    """Tests the case where the provided session_id doesn't exist."""
    session_id = uuid.uuid4()
    user_message_content = "Hello"
    request_payload = {"query": user_message_content, "session_id": str(session_id)}

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

    # Configurar mock para simular sessão não encontrada
    mock_supabase_response = MagicMock()
    mock_supabase_response.data = None  # Sessão não encontrada
    mock_supabase_response.error = None

    # --- Correção do Mock --- 
    # Mockar a cadeia de chamadas Supabase, garantindo que execute seja AsyncMock
    mock_execute = AsyncMock(return_value=mock_supabase_response)
    mock_maybe_single = MagicMock()
    mock_maybe_single.execute = mock_execute
    mock_eq = MagicMock(return_value=mock_maybe_single)
    mock_select = MagicMock(return_value=mock_eq)
    # Mockar o método table do cliente Async
    mock_async_client = MagicMock()
    mock_async_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute = mock_execute

    # Aplicar override para o cliente Supabase Async
    app.dependency_overrides[get_supabase_client] = lambda: mock_async_client

    with patch("app.middleware.get_supabase_client", return_value=mock_supabase_auth):
        # Adicionar token fictício no cabeçalho de autenticação
        headers = {"Authorization": "Bearer fake-test-token"}
        
        # MODIFICAÇÃO: Enviar como form-data
        form_data = {
            "query": user_message_content,
            "session_id": str(session_id)
        }
        
        response = await test_client.post("/api/v1/agent/chat", data=form_data, headers=headers)

        assert response.status_code == 404
        response_data = response.json()
        assert "não encontrada" in response_data["detail"]

    # Limpar overrides após o teste
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_handle_chat_message_forbidden(
    test_client: AsyncClient,
    test_user: UserRead,
    mocker
):
    """Tests the case where the session_id belongs to another user."""
    session_id = uuid.uuid4()
    user_message_content = "Hello"
    request_payload = {"query": user_message_content, "session_id": str(session_id)}

    # Mock para outra sessão (pertencente a outro usuário)
    another_user_id = uuid.uuid4()
    mock_session_data = {"id": str(session_id), "user_id": str(another_user_id)}

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

    # Configurar mock para simular sessão de outro usuário
    mock_supabase_response = MagicMock()
    mock_supabase_response.data = mock_session_data  # Sessão de outro usuário
    mock_supabase_response.error = None

    # --- Correção do Mock --- 
    # Mockar a cadeia de chamadas Supabase, garantindo que execute seja AsyncMock
    mock_execute = AsyncMock(return_value=mock_supabase_response)
    mock_maybe_single = MagicMock()
    mock_maybe_single.execute = mock_execute
    mock_eq = MagicMock(return_value=mock_maybe_single)
    mock_select = MagicMock(return_value=mock_eq)
    # Mockar o método table do cliente Async
    mock_async_client = MagicMock()
    mock_async_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute = mock_execute

    # Aplicar override para o cliente Supabase Async
    app.dependency_overrides[get_supabase_client] = lambda: mock_async_client

    with patch("app.middleware.get_supabase_client", return_value=mock_supabase_auth):
        # Adicionar token fictício no cabeçalho de autenticação
        headers = {"Authorization": "Bearer fake-test-token"}
        
        # MODIFICAÇÃO: Enviar como form-data
        form_data = {
            "query": user_message_content,
            "session_id": str(session_id)
        }
        
        response = await test_client.post("/api/v1/agent/chat", data=form_data, headers=headers)

        assert response.status_code == 403
        response_data = response.json()
        assert "não autorizado" in response_data["detail"]

    # Limpar overrides após o teste
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_handle_chat_message_runner_error(
    test_client: AsyncClient,
    test_user: UserRead,
    mocker # Remover supabase_test_client, não é necessário aqui
):
    """Tests error handling when the Runner.run() throws an exception."""
    new_session_id = uuid.uuid4()
    now = datetime.now()
    user_message_content = "What is the weather?"
    request_payload = {"query": user_message_content, "session_id": None}  # Nova sessão

    # Garantir que test_user.id seja UUID
    mock_new_session = {"id": new_session_id, "user_id": test_user.id, "created_at": now, "updated_at": now, "title": user_message_content[:50]}
    mock_new_user_message = {"id": uuid.uuid4(), "session_id": new_session_id, "role": "user", "content": user_message_content, "created_at": now, "user_id": test_user.id}

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

    # Mockar chamadas ao service para criar uma nova sessão
    # O erro deve ocorrer no Runner.run()
    with patch("app.api.v1.endpoints.agent.agent_service.create_session", return_value=mock_new_session) as mock_create_session, \
         patch("app.api.v1.endpoints.agent.agent_service.add_message", return_value=mock_new_user_message) as mock_add_message, \
         patch("app.api.v1.endpoints.agent.Runner.run", side_effect=Exception("Runner error")) as mock_runner_run, \
         patch("app.api.v1.endpoints.agent.brain_agent", MagicMock()) as mock_brain_agent, \
         patch("app.api.v1.endpoints.agent.current_user_id_var") as mock_context_var, \
         patch("app.middleware.get_supabase_client", return_value=mock_supabase_auth):

        # Adicionar token fictício no cabeçalho de autenticação
        headers = {"Authorization": "Bearer fake-test-token"}
        
        # MODIFICAÇÃO: Enviar como form-data
        form_data = {
            "query": user_message_content
            # Não enviar session_id para criar nova sessão
        }
        
        response = await test_client.post("/api/v1/agent/chat", data=form_data, headers=headers)

        assert response.status_code == 500
        response_data = response.json()
        assert "Erro interno" in response_data["detail"]

    # Limpar overrides após o teste
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_handle_chat_message_add_assistant_message_error(
    test_client: AsyncClient,
    test_user: UserRead, # auth_headers e supabase_test_client removidos
    mocker # Adicionar mocker se não estiver presente
):
    """Tests error handling when adding the assistant's message fails."""
    new_session_id = uuid.uuid4()
    now = datetime.now()
    user_message_content = "What is the weather?"
    assistant_response_content = "The weather is sunny."
    request_payload = {"query": user_message_content, "session_id": None}  # Nova sessão

    # Garantir que test_user.id seja UUID
    mock_new_session = {"id": new_session_id, "user_id": test_user.id, "created_at": now, "updated_at": now, "title": user_message_content[:50]}
    mock_new_user_message = {"id": uuid.uuid4(), "session_id": new_session_id, "role": "user", "content": user_message_content, "created_at": now, "user_id": test_user.id}

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

    # Mockar para simular falha ao adicionar mensagem do assistente
    with patch("app.api.v1.endpoints.agent.agent_service.create_session", return_value=mock_new_session) as mock_create_session, \
         patch("app.api.v1.endpoints.agent.agent_service.add_message", side_effect=[
             mock_new_user_message,  # Primeira chamada bem-sucedida (mensagem do usuário)
             Exception("Database error")  # Segunda chamada falha (mensagem do assistente)
         ]) as mock_add_message, \
         patch("app.api.v1.endpoints.agent.Runner.run", return_value=MagicMock(final_output=assistant_response_content)) as mock_runner_run, \
         patch("app.api.v1.endpoints.agent.brain_agent", MagicMock()) as mock_brain_agent, \
         patch("app.api.v1.endpoints.agent.current_user_id_var") as mock_context_var, \
         patch("app.middleware.get_supabase_client", return_value=mock_supabase_auth):

        # Adicionar token fictício no cabeçalho de autenticação
        headers = {"Authorization": "Bearer fake-test-token"}
        
        # MODIFICAÇÃO: Enviar como form-data
        form_data = {
            "query": user_message_content
            # Não enviar session_id para criar nova sessão
        }
        
        response = await test_client.post("/api/v1/agent/chat", data=form_data, headers=headers)

        assert response.status_code == 500
        response_data = response.json()
        assert "Erro interno" in response_data["detail"]

    # Limpar overrides após o teste
    app.dependency_overrides.clear()

