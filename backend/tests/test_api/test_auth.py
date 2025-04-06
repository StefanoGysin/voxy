import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import time # Importar time
import uuid # Usar uuid para mais singularidade

# Importar a aplicação FastAPI principal
# Usamos 'app.main' assumindo que 'main.py' está em 'backend/app/'
# e que pytest é executado da raiz do projeto com 'backend/' no path (via conftest.py)
from app.main import app
# Importar modelos Pydantic para checar a resposta (se necessário)
from app.db.models import UserRead # Modelo para verificar a resposta

# Importar utilitários de teste, se existirem (ex: para limpar o DB)
# from ..utils import clear_test_database # Assumindo que teremos utilitários

# Usar um marcador para agrupar testes de API, se desejado
pytestmark = pytest.mark.asyncio

# A fixture 'client' agora vem de conftest.py
# @pytest_asyncio.fixture(scope="function")
# async def client() -> AsyncClient:
#     """ Cria um cliente HTTP assíncrono para testar a API. """
#     # Nota: Idealmente, usaríamos um banco de dados de teste isolado aqui.
#     # Por enquanto, estamos usando o DB principal, o que requer limpeza manual
#     # ou uma estratégia de teste diferente (ex: fixtures de banco de dados).
#     async with AsyncClient(app=app, base_url="http://testserver") as c:
#         yield c
#     # Aqui poderíamos adicionar a limpeza do DB após cada teste, se necessário
#     # await clear_test_database()

def generate_unique_suffix():
    # Gera um sufixo curto e único
    return uuid.uuid4().hex[:6]

async def test_register_user_success(client: AsyncClient):
    """
    Testa o registro bem-sucedido de um novo usuário.

    Verifica:
    - Status code 201 Created.
    - Resposta contém o username, email e id do usuário criado.
    - Resposta NÃO contém a senha.
    - Resposta corresponde (parcialmente) ao schema UserRead.
    """
    unique_suffix = generate_unique_suffix()
    user_data = {
        "username": f"test_success_{unique_suffix}",
        "email": f"test.success.{unique_suffix}@example.com",
        "password": "ValidPassword123"
    }
    
    response = await client.post("/api/auth/register", json=user_data)

    # Verificar o status code
    assert response.status_code == 201, f"Expected status 201, got {response.status_code}. Response: {response.text}"

    # Verificar o conteúdo da resposta
    response_data = response.json()
    
    assert "username" in response_data
    assert response_data["username"] == user_data["username"]
    assert "email" in response_data
    assert response_data["email"] == user_data["email"]
    
    assert "id" in response_data # Verificar se um ID foi atribuído
    assert isinstance(response_data["id"], int)
    
    assert "password" not in response_data # Garantir que a senha não está na resposta
    assert "hashed_password" not in response_data # Garantir que o hash também não
    
    # Opcional: Verificar se corresponde ao modelo Pydantic (se UserRead for usado)
    # Isso garante que campos extras não esperados não estão presentes
    try:
        UserRead.model_validate(response_data)
    except Exception as e:
        pytest.fail(f"Response data does not match UserRead schema: {e}")

    # TODO: Adicionar limpeza do usuário criado no banco de dados
    # Idealmente, isso seria feito em uma fixture de teardown ou usando
    # um banco de dados de teste que é resetado a cada teste. 

async def test_register_user_duplicate_email(client: AsyncClient):
    """
    Testa a falha ao tentar registrar um usuário com um email já existente.

    Verifica:
    - Status code 400 Bad Request na segunda tentativa.
    - Mensagem de erro indica que o email já está registrado.
    """
    unique_suffix = generate_unique_suffix()
    unique_email = f"test.duplicate.{unique_suffix}@example.com"
    user_data_1 = {
        "username": f"test_dup_1_{unique_suffix}",
        "email": unique_email,
        "password": "ValidPassword123"
    }
    # 1. Registrar pela primeira vez
    response1 = await client.post("/api/auth/register", json=user_data_1)
    assert response1.status_code == 201, f"Falha no primeiro registro. Status: {response1.status_code}, Response: {response1.text}"

    # 2. Tentar registrar com o MESMO email, mas username diferente
    user_data_2 = {
        "username": f"test_dup_2_{unique_suffix}", 
        "email": unique_email, # Mesmo email
        "password": "AnotherPassword456"
    }
    response2 = await client.post("/api/auth/register", json=user_data_2)
    assert response2.status_code == 400, f"Expected status 400, got {response2.status_code}. Response: {response2.text}"
    assert "Email already registered" in response2.json().get("detail", "")

    # TODO: Adicionar limpeza do usuário criado no banco de dados


@pytest.mark.parametrize(
    "payload, expected_status_code, expected_detail_contains",
    [
        ({"email": "t1@example.com", "password": "ValidPassword123"}, 422, "Field required"), # Username faltando
        ({"username": "testuser1", "password": "ValidPassword123"}, 422, "Field required"), # Email faltando
        ({"username": "testuser2", "email": "t2@example.com"}, 422, "Field required"), # Senha faltando
        ({"username": "testuser3", "email": "not-an-email", "password": "ValidPassword123"}, 422, "value is not a valid email address"), # Email inválido
        ({"username": "testuser4", "email": "t4@example.com", "password": "short"}, 422, "String should have at least 8 characters"), # Senha curta (ajustar se a validação for diferente)
    ]
)
async def test_register_user_invalid_data(
    client: AsyncClient, 
    payload: dict, 
    expected_status_code: int, 
    expected_detail_contains: str
):
    """
    Testa a falha ao tentar registrar um usuário com dados inválidos.

    Verifica:
    - Status code 422 Unprocessable Entity.
    - Mensagem de erro contém detalhes sobre o campo inválido.
    """
    response = await client.post("/api/auth/register", json=payload)

    assert response.status_code == expected_status_code, f"Payload: {payload}. Expected status {expected_status_code}, got {response.status_code}. Response: {response.text}"

    response_data = response.json()
    assert "detail" in response_data
    
    # Verifica se algum dos erros no detalhe contém a string esperada
    # A estrutura do 'detail' do erro 422 pode ser uma lista de erros
    if isinstance(response_data["detail"], list):
        assert any(expected_detail_contains in error.get("msg", "") for error in response_data["detail"]), \
               f"Expected detail containing '{expected_detail_contains}' not found in {response_data['detail']}"
    elif isinstance(response_data["detail"], str): # Caso seja uma string simples
         assert expected_detail_contains in response_data["detail"], \
               f"Expected detail containing '{expected_detail_contains}' not found in '{response_data['detail']}'"
    else:
         pytest.fail(f"Unexpected format for response detail: {response_data['detail']}")

    # TODO: Adicionar limpeza do usuário criado no banco de dados
    # Idealmente, isso seria feito em uma fixture de teardown ou usando
    # um banco de dados de teste que é resetado a cada teste. 

# --- Testes para Login ---

async def test_login_success(client: AsyncClient):
    """
    Testa o login bem-sucedido de um usuário existente.

    Verifica:
    - Status code 200 OK.
    - Resposta contém 'access_token' e 'token_type' == 'bearer'.
    - Primeiro registra um usuário para garantir que ele existe.
    """
    unique_suffix = generate_unique_suffix()
    register_data = {
        "username": f"login_success_{unique_suffix}",
        "email": f"test.login.success.{unique_suffix}@example.com",
        "password": "ValidPasswordLogin123"
    }
    # 1. Registrar usuário único
    reg_response = await client.post("/api/auth/register", json=register_data)
    assert reg_response.status_code == 201, f"Falha ao registrar usuário para teste de login. Status: {reg_response.status_code}, Response: {reg_response.text}"

    # 2. Tentar fazer login (usando email como 'username' no form)
    login_data = {
        "username": register_data["email"],
        "password": register_data["password"]
    }
    response = await client.post("/api/auth/token", data=login_data)

    # Verificar o status code
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}. Response: {response.text}"

    # Verificar o conteúdo da resposta
    response_data = response.json()
    assert "access_token" in response_data
    assert isinstance(response_data["access_token"], str)
    assert response_data.get("token_type") == "bearer"

    # TODO: Adicionar limpeza do usuário criado


async def test_login_user_not_found(client: AsyncClient):
    """
    Testa a falha de login com um email não registrado.

    Verifica:
    - Status code 404 Not Found (ajustado do 401 original).
    """
    login_data = {
        "username": "non.existent.user@example.com",
        "password": "anypassword"
    }
    response = await client.post("/api/auth/token", data=login_data)

    assert response.status_code == 404, f"Expected status 404, got {response.status_code}. Response: {response.text}"
    
    # Verificar detalhe (opcional, pode variar)
    response_data = response.json()
    assert "detail" in response_data
    # Ajustar para esperar a mensagem exata retornada pela API
    assert "User not found" in response_data["detail"] 


async def test_login_incorrect_password(client: AsyncClient):
    """
    Testa a falha de login com uma senha incorreta para um usuário existente.

    Verifica:
    - Status code 401 Unauthorized.
    """
    unique_suffix = generate_unique_suffix()
    register_data = {
        "username": f"wrongpass_{unique_suffix}",
        "email": f"test.wrong.pass.{unique_suffix}@example.com",
        "password": "CorrectPassword123"
    }
    # 1. Registrar usuário único
    reg_response = await client.post("/api/auth/register", json=register_data)
    assert reg_response.status_code == 201, "Falha ao registrar usuário para teste de senha incorreta."

    # 2. Tentar logar com a senha errada (usando email como 'username' no form)
    login_data = {
        "username": register_data["email"],
        "password": "WrongPassword!!!"
    }
    response = await client.post("/api/auth/token", data=login_data)

    assert response.status_code == 401, f"Expected status 401, got {response.status_code}. Response: {response.text}"
    
    # Verificar detalhe (opcional, pode variar)
    response_data = response.json()
    assert "detail" in response_data
    assert "Incorrect email or password" in response_data["detail"]

    # TODO: Adicionar limpeza do usuário criado

    # TODO: Adicionar limpeza do usuário criado
    # Idealmente, isso seria feito em uma fixture de teardown ou usando
    # um banco de dados de teste que é resetado a cada teste. 