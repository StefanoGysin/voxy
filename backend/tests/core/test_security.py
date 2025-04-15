import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

from app.core.security import (
    verify_password,
    get_password_hash,
    get_current_user,
    oauth2_scheme, # Necessário para simular a extração do token
)
from app.db.supabase_client import get_supabase_client # Para override

# --- Testes para Hashing de Senha ---

def test_verify_password():
    password = "secretpassword"
    hashed_password = get_password_hash(password)
    assert verify_password(password, hashed_password) is True
    assert verify_password("wrongpassword", hashed_password) is False

def test_get_password_hash():
    password = "anothers3cret"
    hashed_password = get_password_hash(password)
    # Verifica se é uma string e se não é a senha original
    assert isinstance(hashed_password, str)
    assert hashed_password != password
    # Verifica se a verificação funciona
    assert verify_password(password, hashed_password) is True

# --- Testes para get_current_user (mockando Supabase) ---

@pytest.mark.asyncio
async def test_get_current_user_success():
    """ Testa get_current_user com token válido e mock de Supabase bem-sucedido """
    # 1. Definir dados de teste e token placeholder
    test_email = "test@example.com"
    test_uuid = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11" # Exemplo de UUID
    # Não precisamos mais gerar um token JWT real localmente
    valid_token_placeholder = "valid_token_for_test"

    # 2. Mockar a resposta bem-sucedida do Supabase Auth (usando MagicMock)
    mock_supabase_client = MagicMock() # Usar MagicMock para síncrono/assíncrono simples
    mock_user_response = MagicMock()
    mock_user_response.user = MagicMock() # Certificar que 'user' existe
    mock_user_response.user.id = test_uuid
    mock_user_response.user.email = test_email
    # Mockamos a chamada assíncrona get_user
    mock_supabase_client.auth.get_user = AsyncMock(return_value=mock_user_response)

    # 3. Chamar a função de dependência com o token placeholder e o mock
    current_user = await get_current_user(supabase=mock_supabase_client, token=valid_token_placeholder)

    # 4. Verificar o resultado
    assert current_user is not None
    assert current_user.id == test_uuid
    assert current_user.email == test_email
    # Verificar chamada assíncrona
    mock_supabase_client.auth.get_user.assert_called_once_with(valid_token_placeholder)

@pytest.mark.asyncio
async def test_get_current_user_supabase_failure():
    """ Testa get_current_user quando Supabase Auth falha em retornar um usuário """
    # Usar placeholder
    test_token_placeholder = "test_token_supabase_failure"

    # Mockar falha do Supabase Auth (retorna None no user)
    mock_supabase_client = AsyncMock()
    mock_failure_response = MagicMock()
    mock_failure_response.user = None # Indica falha
    mock_supabase_client.auth.get_user = AsyncMock(return_value=mock_failure_response)

    # Chamar e verificar a exceção
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(supabase=mock_supabase_client, token=test_token_placeholder)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in exc_info.value.detail
    mock_supabase_client.auth.get_user.assert_called_once_with(test_token_placeholder)

@pytest.mark.asyncio
async def test_get_current_user_supabase_exception():
    """ Testa get_current_user quando Supabase Auth levanta uma exceção """
    # Usar placeholder
    test_token_placeholder = "test_token_supabase_exception"

    # Mockar Supabase Auth levantando exceção
    mock_supabase_client = AsyncMock()
    mock_supabase_client.auth.get_user = AsyncMock(side_effect=Exception("Supabase network error"))

    # Chamar e verificar a exceção
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(supabase=mock_supabase_client, token=test_token_placeholder)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in exc_info.value.detail
    mock_supabase_client.auth.get_user.assert_called_once_with(test_token_placeholder)

@pytest.mark.asyncio
async def test_get_current_user_invalid_token_format():
    """ Testa get_current_user com token JWT mal formatado (deve falhar antes de chamar Supabase) """
    # Este teste é mais teórico, pois a validação JWT local foi removeda.
    # A exceção agora virá do Supabase Auth. Vamos simular isso.
    invalid_token_placeholder = "this_is_not_a_valid_jwt_but_doesnt_matter_for_mock"

    # Mockar Supabase Auth levantando exceção (simulando erro de token inválido)
    mock_supabase_client = AsyncMock()
    # A biblioteca Supabase pode levantar um erro específico, mas Exception cobre
    mock_supabase_client.auth.get_user = AsyncMock(side_effect=Exception("Invalid token format"))

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(supabase=mock_supabase_client, token=invalid_token_placeholder)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    mock_supabase_client.auth.get_user.assert_called_once_with(invalid_token_placeholder)

# Nota: O teste de token expirado agora é tratado pelo Supabase Auth.
# Seria difícil mockar o tempo dentro do Supabase, então confiamos na validação deles.
# Poderíamos criar um token expirado e passá-lo, esperando a falha do Supabase.
@pytest.mark.asyncio
async def test_get_current_user_expired_token():
    """ Testa get_current_user com token expirado (espera falha do Supabase) """
    # Usar placeholder
    expired_token_placeholder = "expired_token_placeholder"

    # Mockar Supabase Auth falhando (simulando falha por token expirado)
    mock_supabase_client = AsyncMock()
    mock_failure_response = MagicMock()
    mock_failure_response.user = None
    mock_supabase_client.auth.get_user = AsyncMock(return_value=mock_failure_response) # Ou side_effect=Exception(...)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(supabase=mock_supabase_client, token=expired_token_placeholder)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    mock_supabase_client.auth.get_user.assert_called_once_with(expired_token_placeholder) 