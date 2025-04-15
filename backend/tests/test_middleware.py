# backend/tests/test_middleware.py

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI, Request, Response, APIRouter
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# Importar o middleware e cliente Supabase (e mocks)
from app.middleware import AuthMiddleware, PUBLIC_PATHS
from app.db.supabase_client import get_supabase_client  # Importar a função que vamos patchar
from supabase import AsyncClient as SupabaseAsyncClient, AuthApiError
from unittest.mock import AsyncMock, MagicMock, patch

# --- Overrides para Fixtures de conftest.py ---
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Sobrescreve a fixture autouse cleanup_test_data de conftest.py.
    
    Os testes unitários de middleware usam mocks e não precisam
    da limpeza de banco de dados real.
    """
    print("\n[Middleware Test] Skipping Supabase DB cleanup.")
    yield # Não faz nada antes ou depois do teste


# --- Mocks --- 
# Mock do usuário Supabase retornado
class MockSupabaseUser:
    def __init__(self, id="test-user-id", email="test@example.com"):
        self.id = id
        self.email = email
        self.user_metadata = {"username": "testuser"}

class MockGetUserResponse:
    def __init__(self, user=None, error=None):
        self.user = user
        self.error = error

# --- Fixtures de Teste --- 
# Criar uma aplicação FastAPI mínima para testar o middleware
@pytest_asyncio.fixture(scope="function")
async def test_app(mock_supabase_client): # Depende do fixture do cliente mockado
    app = FastAPI(title="Test App for Middleware")

    # Adicionar uma rota pública e uma protegida para teste
    router = APIRouter()

    @router.get("/public")
    async def public_route():
        return {"message": "Public access granted"}

    @router.get("/api/protected")
    async def protected_route(request: Request):
        # Verificar se o usuário foi anexado pelo middleware
        if not hasattr(request.state, 'user') or request.state.user is None:
            return JSONResponse(status_code=500, content={"detail": "User not found in request state"})
        return {"message": "Protected access granted", "user_id": request.state.user.id}

    # Adicionar rotas públicas padrão para teste
    @router.get("/docs")
    async def docs_route(): return {"message": "docs"}
    @router.get("/api/auth/token")
    async def token_route(): return {"message": "token"}

    app.include_router(router)

    # Aplicar patch para get_supabase_client retornar o mock_client
    with patch('app.middleware.get_supabase_client', return_value=mock_supabase_client):
        # Adicionar o AuthMiddleware sem o cliente Supabase como parâmetro
        app.add_middleware(AuthMiddleware)
        yield app

# Criar um cliente HTTP assíncrono para interagir com a test_app
@pytest_asyncio.fixture(scope="function")
async def client(test_app: FastAPI) -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        yield client

# Criar um mock do cliente Supabase
@pytest.fixture(scope="function")
def mock_supabase_client():
    mock_client = MagicMock(spec=SupabaseAsyncClient)
    mock_client.auth = AsyncMock() # Mockar o objeto 'auth'
    return mock_client

# --- Testes --- 

@pytest.mark.asyncio
async def test_public_route_no_token(client: AsyncClient):
    """Testa o acesso a uma rota pública definida por nós sem token."""
    response = await client.get("/public")
    assert response.status_code == 200
    assert response.json() == {"message": "Public access granted"}

@pytest.mark.asyncio
@pytest.mark.parametrize("path", PUBLIC_PATHS)
async def test_standard_public_routes_no_token(client: AsyncClient, path: str):
    """Testa o acesso às rotas públicas padrão (docs, auth) sem token."""
    # Simular rotas que podem ou não existir na app de teste, mas o middleware deve permitir
    # Para simplificar, usamos as rotas mockadas na test_app que correspondem a algumas delas
    if path in ["/docs", "/api/auth/token"]: # Apenas testar as que existem na test_app
        response = await client.get(path)
        assert response.status_code == 200 # Middleware não deve bloquear

@pytest.mark.asyncio
async def test_protected_route_no_token(client: AsyncClient):
    """Testa o acesso a uma rota protegida sem token (deve falhar com 401)."""
    response = await client.get("/api/protected")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
    assert response.headers.get("WWW-Authenticate") == "Bearer"

@pytest.mark.asyncio
async def test_protected_route_invalid_token_format(client: AsyncClient):
    """Testa o acesso com um cabeçalho Authorization malformatado."""
    response = await client.get("/api/protected", headers={"Authorization": "Invalid Token"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.asyncio
async def test_protected_route_invalid_token_supabase(client: AsyncClient, mock_supabase_client):
    """Testa o acesso com um token que o Supabase considera inválido (retorna user=None)."""
    # Configurar mock para simular falha na validação (get_user retorna None)
    mock_supabase_client.auth.get_user.return_value = MockGetUserResponse(user=None)
    
    response = await client.get("/api/protected", headers={"Authorization": "Bearer invalid-token"})
    
    mock_supabase_client.auth.get_user.assert_awaited_once_with("invalid-token")
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_protected_route_expired_token_supabase(client: AsyncClient, mock_supabase_client):
    """Testa o acesso com um token que o Supabase considera expirado (levanta AuthApiError)."""
    # Configurar mock para levantar AuthApiError com os parâmetros obrigatórios
    mock_supabase_client.auth.get_user.side_effect = AuthApiError("Token expired", status=401, code="expired_token")
    
    response = await client.get("/api/protected", headers={"Authorization": "Bearer expired-token"})
    
    mock_supabase_client.auth.get_user.assert_awaited_once_with("expired-token")
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

@pytest.mark.asyncio
async def test_protected_route_valid_token(client: AsyncClient, mock_supabase_client):
    """Testa o acesso com um token válido."""
    test_user = MockSupabaseUser()
    # Configurar mock para retornar o usuário mockado
    mock_supabase_client.auth.get_user.return_value = MockGetUserResponse(user=test_user)
    
    response = await client.get("/api/protected", headers={"Authorization": "Bearer valid-token"})
    
    mock_supabase_client.auth.get_user.assert_awaited_once_with("valid-token")
    assert response.status_code == 200
    assert response.json() == {"message": "Protected access granted", "user_id": test_user.id}

@pytest.mark.asyncio
async def test_protected_route_supabase_unexpected_error(client: AsyncClient, mock_supabase_client):
    """Testa o tratamento de um erro inesperado do Supabase durante a validação."""
    # Configurar mock para levantar uma exceção genérica
    mock_supabase_client.auth.get_user.side_effect = Exception("Unexpected Supabase error")
    
    response = await client.get("/api/protected", headers={"Authorization": "Bearer some-token"})
    
    mock_supabase_client.auth.get_user.assert_awaited_once_with("some-token")
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error during authentication"} 