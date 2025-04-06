# backend/tests/test_core/test_security.py

import pytest
from app.core.security import get_password_hash, verify_password
import uuid # Importar uuid

# --- Testes para Hashing e Verificação de Senha ---

def test_get_password_hash():
    """ Testa se o hash da senha é gerado corretamente. """
    password = "mysecretpassword"
    hashed_password = get_password_hash(password)
    
    # Verificar se o resultado é uma string
    assert isinstance(hashed_password, str)
    # Verificar se o hash não é a senha original
    assert hashed_password != password
    # Verificar se o hash parece ter o formato bcrypt (começa com $2b$)
    # Nota: Isso pode ser frágil se o algoritmo mudar, mas é um sanity check.
    assert hashed_password.startswith("$2b$") 

def test_verify_password_correct():
    """ Testa a verificação com a senha correta. """
    password = "mysecretpassword"
    hashed_password = get_password_hash(password)
    
    assert verify_password(password, hashed_password) is True

def test_verify_password_incorrect():
    """ Testa a verificação com a senha incorreta. """
    password = "mysecretpassword"
    wrong_password = "anotherpassword"
    hashed_password = get_password_hash(password)
    
    assert verify_password(wrong_password, hashed_password) is False

def test_different_passwords_different_hashes():
    """ Testa se senhas diferentes geram hashes diferentes (devido ao salt). """
    password = "mysecretpassword"
    hashed_password1 = get_password_hash(password)
    hashed_password2 = get_password_hash(password)
    
    # Mesmo com a mesma senha, os hashes devem ser diferentes por causa do salt
    assert hashed_password1 != hashed_password2
    
    # Mas ambas devem verificar corretamente com a senha original
    assert verify_password(password, hashed_password1) is True
    assert verify_password(password, hashed_password2) is True

# Próximos testes: testar create_access_token e decode_access_token 

# --- Testes para Criação e Decodificação de Token JWT ---

from datetime import timedelta
from jose import jwt, JWTError, ExpiredSignatureError # Importar exceções JWT
from app.core.config import settings # Precisamos das settings para SECRET_KEY e ALGORITHM
from app.core.security import create_access_token, decode_access_token

def test_create_access_token():
    """ Testa a criação de um token de acesso JWT. """
    test_subject = "testuser@example.com"
    token = create_access_token(data={"sub": test_subject})

    assert isinstance(token, str)
    
    # Decodificar manualmente para verificar o conteúdo básico (sem validação completa aqui)
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_signature": False, "verify_aud": False, "verify_exp": False}
    )
    assert payload.get("sub") == test_subject
    assert "exp" in payload # Verificar se a expiração está presente


def test_decode_access_token_valid():
    """ Testa a decodificação de um token JWT válido. """
    test_subject = "testuser@example.com"
    token = create_access_token(data={"sub": test_subject})
    
    payload = decode_access_token(token)
    
    assert payload is not None
    assert payload.username == test_subject


def test_decode_access_token_expired():
    """ Testa a falha ao decodificar um token JWT expirado. """
    test_subject = "testuser_expired@example.com"
    # Criar um token que expirou 5 minutos atrás
    expired_token = create_access_token(
        data={"sub": test_subject}, expires_delta=timedelta(minutes=-5)
    )
    
    # Verificar se decode_access_token retorna None ou levanta exceção específica
    # A implementação atual em decode_access_token retorna None em caso de erro.
    payload = decode_access_token(expired_token)
    assert payload is None

    # Alternativamente, se quiséssemos verificar a exceção específica da biblioteca 'jose':
    # with pytest.raises(ExpiredSignatureError):
    #     jwt.decode(
    #         expired_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    #     )


def test_decode_access_token_invalid_signature():
    """ Testa a falha ao decodificar um token JWT com assinatura inválida. """
    test_subject = "testuser_invalid_sig@example.com"
    token = create_access_token(data={"sub": test_subject})
    
    # Modificar o token para invalidar a assinatura
    invalid_token = token[:-5] + "xxxxx" 
    
    payload = decode_access_token(invalid_token)
    assert payload is None


def test_decode_access_token_invalid_format():
    """ Testa a falha ao decodificar uma string que não é um token JWT. """
    invalid_token = "this.is.not.a.jwt"
    
    payload = decode_access_token(invalid_token)
    assert payload is None

# Próximo passo: Considerar como testar get_current_user (mais complexo) 

# --- Testes para a Dependência get_current_user (via endpoint protegido) ---

import pytest
from httpx import AsyncClient # Necessário para testar a dependência via API
from app.main import app # Importar a app FastAPI para o cliente de teste
# Importar User para type hints se necessário
from app.db.models import User 
from app.core.security import get_current_user # Importar a dependência

# A fixture 'client' agora vem de conftest.py
# @pytest_asyncio.fixture(scope="function")
# async def client() -> AsyncClient:
#     ...

# --- Testes ASSÍNCRONOS para a Dependência get_current_user --- 
# (COM @pytest.mark.asyncio)

def generate_unique_suffix():
    # Gera um sufixo curto e único
    # Duplicado de test_auth.py - Idealmente em conftest.py ou utils
    return uuid.uuid4().hex[:6]

# Helper para registrar e logar, retorna o token
@pytest.mark.asyncio
async def register_and_login_user(client: AsyncClient, username: str, email: str, password: str) -> str | None:
    """Registra e faz login de um usuário, retornando o token de acesso."""
    reg_data = {"username": username, "email": email, "password": password} # Incluir username
    reg_response = await client.post("/api/auth/register", json=reg_data)
    # Ignorar falha no registro se o usuário já existir (status 400)? 
    # Ou verificar se foi 201 ou 400 (já existe)? Melhor falhar se não for 201.
    if reg_response.status_code != 201 and reg_response.status_code != 400:
         pytest.fail(f"Falha inesperada no registro do helper: {reg_response.status_code} {reg_response.text}")
    
    # Usar email para login
    login_data = {"username": email, "password": password} 
    login_response = await client.post("/api/auth/token", data=login_data)
    
    if login_response.status_code == 200:
        return login_response.json().get("access_token")
    # Adicionar log ou falha se o login falhar inesperadamente
    print(f"WARN: Falha no login dentro do helper register_and_login_user. Status: {login_response.status_code}, Response: {login_response.text}")
    return None

@pytest.mark.asyncio
async def test_get_current_user_valid_token(client: AsyncClient):
    """ Testa o acesso a endpoint protegido com token válido. """
    unique_suffix = generate_unique_suffix()
    test_username = f"valid_user_{unique_suffix}"
    email = f"test.valid.token.{unique_suffix}@example.com"
    password = "Password123"
    token = await register_and_login_user(client, test_username, email, password)
    assert token is not None, f"Falha ao obter token para teste. User: {email}"
    
    headers = {"Authorization": f"Bearer {token}"}
    chat_response = await client.post("/api/chat", headers=headers, json={"content": "test message"}) 
    
    assert chat_response.status_code != 401, f"Expected non-401 status, got 401. Response: {chat_response.text}"

@pytest.mark.asyncio
async def test_get_current_user_invalid_token_format(client: AsyncClient):
    """ Testa o acesso a endpoint protegido com token mal formatado. """
    headers = {"Authorization": "Bearer this.is.not.a.jwt"}
    chat_response = await client.post("/api/chat", headers=headers, json={"content": "test"})
    assert chat_response.status_code == 401, f"Expected 401, got {chat_response.status_code}. Response: {chat_response.text}"
    assert "Could not validate credentials" in chat_response.json().get("detail", "") 

@pytest.mark.asyncio
async def test_get_current_user_invalid_signature(client: AsyncClient):
    """ Testa o acesso a endpoint protegido com token de assinatura inválida. """
    unique_suffix = generate_unique_suffix()
    test_username = f"invalid_sig_{unique_suffix}"
    email = f"test.invalid.sig.{unique_suffix}@example.com"
    password = "Password123"
    token = await register_and_login_user(client, test_username, email, password)
    assert token is not None, f"Falha ao obter token para teste. User: {email}"
    
    invalid_token = token[:-5] + "xxxxx" 
    headers = {"Authorization": f"Bearer {invalid_token}"}
    chat_response = await client.post("/api/chat", headers=headers, json={"content": "test"})
    assert chat_response.status_code == 401, f"Expected 401, got {chat_response.status_code}. Response: {chat_response.text}"
    assert "Could not validate credentials" in chat_response.json().get("detail", "")

@pytest.mark.asyncio
async def test_get_current_user_expired_token(client: AsyncClient):
    """ Testa o acesso a endpoint protegido com token expirado. """
    unique_suffix = generate_unique_suffix()
    test_username = f"expired_user_{unique_suffix}"
    email = f"test.expired.token.{unique_suffix}@example.com"
    password = "Password123"
    await register_and_login_user(client, test_username, email, password)
    
    # Criar token expirado manualmente (usando email no sub)
    expired_token = create_access_token(
        data={"sub": email}, expires_delta=timedelta(minutes=-5)
    )
    
    headers = {"Authorization": f"Bearer {expired_token}"}
    chat_response = await client.post("/api/chat", headers=headers, json={"content": "test"})
    assert chat_response.status_code == 401, f"Expected 401, got {chat_response.status_code}. Response: {chat_response.text}"
    assert "Could not validate credentials" in chat_response.json().get("detail", "") # 'jose' levanta JWTError, pego no get_current_user

@pytest.mark.asyncio
async def test_get_current_user_no_token(client: AsyncClient):
    """ Testa o acesso a endpoint protegido sem enviar token. """
    chat_response = await client.post("/api/chat", json={"content": "test"})
    assert chat_response.status_code == 401, f"Expected 401, got {chat_response.status_code}. Response: {chat_response.text}"
    assert "Not authenticated" in chat_response.json().get("detail", "")

@pytest.mark.asyncio
async def test_get_current_user_token_for_nonexistent_user(client: AsyncClient):
    """ Testa acesso com token válido para usuário que não existe mais no DB. """
    email_nonexistent = "deleted.user@example.com"
    # Criar um token válido para um usuário hipotético (sem registrá-lo ou após deletá-lo)
    # Isso simula um token que era válido, mas o usuário foi removido.
    valid_token_for_ghost = create_access_token(data={"sub": email_nonexistent})

    headers = {"Authorization": f"Bearer {valid_token_for_ghost}"}
    chat_response = await client.post("/api/chat", headers=headers, json={"content": "test"})
    
    # get_current_user deve falhar ao buscar o usuário no DB e levantar HTTPException(401)
    assert chat_response.status_code == 401, f"Expected 401, got {chat_response.status_code}. Response: {chat_response.text}"
    assert "Could not validate credentials" in chat_response.json().get("detail", "") # Mensagem lançada se o user for None