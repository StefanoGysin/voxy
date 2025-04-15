import pytest
from httpx import AsyncClient
from fastapi import status, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4
# Remover import DatabaseError de fastapi.exceptions, pois não é dali
# from fastapi.exceptions import DatabaseError 
# Importar de app.core.exceptions
from app.core.exceptions import DatabaseError
# Importar AuthApiError para simular falha de login
from gotrue.errors import AuthApiError

from app.db.supabase_client import get_supabase_client # Importar para mock/override
# Corrigir importações dos schemas
from app.db.models import UserCreate, UserRead # Movidos para db/models.py
from app.core.models import Token # Movido para core/models.py
# from app.schemas.auth import UserCreate, Token # REMOVIDO
# from app.schemas.user import UserRead # REMOVIDO
from tests.factories import UserCreateFactory, UserReadFactory # Importar factories

# --- Fixture para Mock do Cliente Supabase (Escopo Função) ---
# Poderia ser movida para conftest.py se usada em mais lugares
@pytest.fixture
def mock_supabase_auth():
    """ Mockiza os métodos de autenticação do cliente Supabase """
    mock_client = MagicMock() # Usar MagicMock síncrono, pois os métodos são síncronos

    # Mock para sign_up
    mock_signup_response = MagicMock()
    mock_signup_response.user.id = uuid4()
    mock_signup_response.user.email = "test@example.com"
    mock_client.auth.sign_up = MagicMock(return_value=mock_signup_response)

    # Mock para sign_in_with_password
    mock_signin_response = MagicMock()
    mock_signin_response.user.id = uuid4()
    mock_signin_response.session.access_token = "fake-supabase-token"
    mock_client.auth.sign_in_with_password = MagicMock(return_value=mock_signin_response)

    # Mock para get_user (usado por get_current_user)
    mock_get_user_response = MagicMock()
    mock_get_user_response.user.id = uuid4()
    mock_get_user_response.user.email = "current@example.com"
    mock_get_user_response.user.user_metadata = {'username': 'current_user'}
    mock_client.auth.get_user = MagicMock(return_value=mock_get_user_response)

    return mock_client

# --- Testes para /api/auth/register ---

@pytest.mark.asyncio
async def test_register_new_user_success(test_client: AsyncClient, mock_supabase_auth: MagicMock):
    """ Testa o registro bem-sucedido de um novo usuário """
    user_data = UserCreateFactory.build() # Gera dados com a factory
    user_payload = user_data.model_dump()

    # Configura o mock para sign_up como AsyncMock
    test_uuid = uuid4()
    mock_signup_response = MagicMock() # O objeto retornado por sign_up
    mock_signup_response.user = MagicMock()
    mock_signup_response.user.id = test_uuid
    mock_signup_response.user.email = user_data.email
    mock_signup_response.error = None # Simular sucesso

    # Certifique-se de que mock_supabase_auth.auth existe e mock sign_up como AsyncMock
    if not isinstance(mock_supabase_auth.auth, MagicMock):
        mock_supabase_auth.auth = MagicMock()
    mock_supabase_auth.auth.sign_up = AsyncMock(return_value=mock_signup_response)

    # Aplicar o override da dependência
    from app.main import app # Importar app aqui
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase_auth

    response = await test_client.post("/api/auth/register", json=user_payload)

    # Verificar a chamada do mock
    mock_supabase_auth.auth.sign_up.assert_awaited_once()
    # O argumento exato pode ser complexo devido ao dict aninhado, verificar email é mais simples
    call_args, call_kwargs = mock_supabase_auth.auth.sign_up.call_args
    assert call_args[0]['email'] == user_data.email
    assert call_args[0]['password'] == user_data.password

    # Verificar a resposta da API
    assert response.status_code == status.HTTP_201_CREATED
    response_json = response.json()
    assert response_json["message"] == "Usuário registrado com sucesso. Verifique o email para confirmação se necessário."
    assert response_json["user_id"] == str(test_uuid)
    assert response_json["email"] == user_data.email

    # Limpar override após o teste
    app.dependency_overrides.pop(get_supabase_client, None)

@pytest.mark.asyncio
async def test_register_new_user_already_exists(test_client: AsyncClient, mock_supabase_auth: MagicMock):
    """ Testa o registro quando o email já existe no Supabase """
    user_data = UserCreateFactory.build()
    user_payload = user_data.model_dump()

    # Configurar mock para simular erro de usuário existente
    mock_supabase_auth.auth.sign_up = AsyncMock(
        side_effect=Exception("User already registered")
    )

    # Aplicar override
    from app.main import app
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase_auth

    response = await test_client.post("/api/auth/register", json=user_payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email já registrado" in response.json()["detail"]
    mock_supabase_auth.auth.sign_up.assert_awaited_once()

    # Limpar override
    app.dependency_overrides.pop(get_supabase_client, None)

@pytest.mark.asyncio
async def test_register_new_user_supabase_error(test_client: AsyncClient, mock_supabase_auth: MagicMock):
    """ Testa o registro com um erro genérico do Supabase, esperando DatabaseError """
    user_data = UserCreateFactory.build()
    user_payload = user_data.model_dump()

    # Configurar mock para simular erro genérico, usando AsyncMock
    error_message = "Supabase generic error"
    mock_supabase_auth.auth.sign_up = AsyncMock(
        side_effect=Exception(error_message)
    )

    # Aplicar override
    from app.main import app
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase_auth

    # Esperar que DatabaseError seja levantada pela rota
    with pytest.raises(DatabaseError) as exc_info:
        await test_client.post("/api/auth/register", json=user_payload)

    # Verificar a mensagem da exceção capturada
    assert f"Falha ao registrar usuário no serviço de autenticação: {error_message}" in str(exc_info.value)
    
    # Verificar que o mock assíncrono foi esperado
    mock_supabase_auth.auth.sign_up.assert_awaited_once()

    # Limpar override corretamente
    app.dependency_overrides.pop(get_supabase_client, None)

# --- Testes para /api/auth/token ---

@pytest.mark.asyncio
async def test_login_success(test_client: AsyncClient, mock_supabase_auth: MagicMock):
    """ Testa o login bem-sucedido """
    login_data = {"username": "test@example.com", "password": "password123"}
    test_token = "fake-supabase-jwt-token"
    test_user_id = uuid4() # Gerar um UUID para o usuário mockado

    # --- Configuração do Mock Corrigida --- 
    # 1. Criar um objeto mock para simular a resposta bem-sucedida
    mock_response = MagicMock() # O objeto de resposta pode ser sync
    mock_response.session.access_token = test_token
    mock_response.user.id = test_user_id

    # 2. Configurar o método sign_in_with_password para ser um AsyncMock
    #    (pois a chamada na aplicação é assíncrona com await)
    mock_supabase_auth.auth.sign_in_with_password = AsyncMock(return_value=mock_response)
    # --- Fim da Configuração Corrigida ---

    # Aplicar override
    from app.main import app
    # from app.db.supabase_client import get_supabase_client # Importar dependência
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase_auth

    response = await test_client.post("/api/auth/token", data=login_data)

    assert response.status_code == status.HTTP_200_OK
    token_data = response.json()
    assert token_data["access_token"] == test_token
    assert token_data["token_type"] == "bearer"

    # Verificar se o mock foi chamado corretamente (agora assíncrono)
    mock_supabase_auth.auth.sign_in_with_password.assert_awaited_once_with(
        {"email": login_data["username"], "password": login_data["password"]}
    )

    # Limpar override após o teste
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_login_incorrect_credentials(test_client: AsyncClient, mock_supabase_auth: MagicMock):
    """ Testa o login com credenciais incorretas """
    login_data = {"username": "wrong@example.com", "password": "wrongpassword"}

    # --- Configuração do Mock Corrigida --- 
    # Configurar mock para falha de login levantando AuthApiError, usando AsyncMock
    # AuthApiError requer (message, status, code) como args posicionais
    mock_supabase_auth.auth.sign_in_with_password = AsyncMock(
        side_effect=AuthApiError("Invalid login credentials", 400, None)
    )
    # --- Fim da Configuração Corrigida ---

    # Aplicar override
    from app.main import app
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase_auth

    response = await test_client.post("/api/auth/token", data=login_data)

    # A rota captura AuthApiError e retorna 401 com detalhe específico
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect email or password" in response.json()["detail"]
    
    # Verificar se o mock assíncrono foi esperado
    mock_supabase_auth.auth.sign_in_with_password.assert_awaited_once()

    # Limpar override corretamente
    app.dependency_overrides.pop(get_supabase_client, None)

@pytest.mark.asyncio
async def test_login_supabase_error(test_client: AsyncClient, mock_supabase_auth: MagicMock):
    """ Testa o login com erro genérico do Supabase """
    login_data = {"username": "error@example.com", "password": "password123"}

    # --- Configuração do Mock Corrigida --- 
    # Configurar mock para erro genérico, usando AsyncMock
    mock_supabase_auth.auth.sign_in_with_password = AsyncMock(
        side_effect=Exception("Supabase network error")
    )
    # --- Fim da Configuração Corrigida ---

    # Aplicar override
    from app.main import app
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase_auth

    response = await test_client.post("/api/auth/token", data=login_data)

    # Espera 401 e a mensagem de erro genérica da rota
    assert response.status_code == status.HTTP_401_UNAUTHORIZED 
    # Corrigir a asserção do detalhe para a mensagem genérica
    assert "Erro durante a autenticação." in response.json()["detail"] # <<< CORRIGIDO

    # Verificar que o mock assíncrono foi esperado
    mock_supabase_auth.auth.sign_in_with_password.assert_awaited_once() # <<< CORRIGIDO

    # Limpar override corretamente
    app.dependency_overrides.pop(get_supabase_client, None) # <<< CORRIGIDO

# --- Testes para /api/auth/users/me ---

@pytest.mark.asyncio
async def test_read_users_me_success(test_client: AsyncClient, mock_supabase_auth: MagicMock):
    """ Testa o endpoint /users/me com um token válido """
    test_token = "valid-fake-token"
    test_uuid = uuid4()
    test_email = "me@example.com"
    test_username = "me_user"

    # --- Configuração do Mock Corrigida --- 
    # 1. Criar um objeto mock para simular a resposta de get_user
    mock_response = MagicMock()
    mock_response.user = MagicMock() # Garantir que o atributo user exista
    mock_response.user.id = test_uuid
    mock_response.user.email = test_email
    mock_response.user.user_metadata = {'username': test_username}

    # 2. Configurar o método get_user para ser um AsyncMock
    #    (pois a chamada na dependência get_current_user é assíncrona)
    mock_supabase_auth.auth.get_user = AsyncMock(return_value=mock_response) # <<< CORRIGIDO
    # --- Fim da Configuração Corrigida ---

    # Aplicar override para a dependência get_supabase_client
    from app.main import app
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase_auth

    # Aplicar patch para o middleware também acessar o mesmo mock
    with patch('app.middleware.get_supabase_client', return_value=mock_supabase_auth):
        headers = {"Authorization": f"Bearer {test_token}"}
        response = await test_client.get("/api/auth/users/me", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        # Verificar se a resposta contém os dados esperados
        assert response_data["id"] == str(test_uuid)
        assert response_data["email"] == test_email
        assert response_data["username"] == test_username
        # Remover a linha abaixo se auth_uuid não existe mais em UserRead
        # assert response_data["auth_uuid"] == str(test_uuid)

        # Verificar se get_user foi chamado com o token correto (agora assíncrono)
        # O método deve ser chamado 2 vezes: uma pelo middleware e outra pelo get_current_user
        assert mock_supabase_auth.auth.get_user.await_count >= 1
        mock_supabase_auth.auth.get_user.assert_awaited_with(test_token)

    # Limpar override
    app.dependency_overrides.clear() # Usar clear()

@pytest.mark.asyncio
async def test_read_users_me_invalid_token(test_client: AsyncClient, mock_supabase_auth: MagicMock):
    """ Testa o endpoint /users/me com um token inválido """
    invalid_token = "invalid-fake-token"

    # Configurar mock de get_user para falhar (sem user)
    mock_response = MagicMock()
    mock_response.user = None
    mock_supabase_auth.auth.get_user = AsyncMock(return_value=mock_response)

    # Aplicar override para a dependência
    from app.main import app
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase_auth

    # Aplicar patch para o middleware também acessar o mesmo mock
    with patch('app.middleware.get_supabase_client', return_value=mock_supabase_auth):
        headers = {"Authorization": f"Bearer {invalid_token}"}
        response = await test_client.get("/api/auth/users/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in response.json()["detail"]
        
        # Verificar se get_user foi chamado (pelo menos uma vez)
        assert mock_supabase_auth.auth.get_user.await_count >= 1
        mock_supabase_auth.auth.get_user.assert_awaited_with(invalid_token)

    # Limpar override
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_read_users_me_no_token(test_client: AsyncClient):
    """ Testa o endpoint /users/me sem token de autenticação """
    # Não precisa de mock ou override, pois o erro ocorre antes na camada FastAPI/OAuth2

    response = await test_client.get("/api/auth/users/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED # Ou 403 dependendo da config
    assert "Not authenticated" in response.json()["detail"] # Mensagem padrão do FastAPI 