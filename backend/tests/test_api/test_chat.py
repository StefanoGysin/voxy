"""
Testes para os endpoints de API do chat.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from app.main import app
from app.api.chat import ChatMessage, ChatResponse
from unittest.mock import patch, AsyncMock, MagicMock
from app.db.models import User
from app.core.security import get_current_user

# Não precisamos mais do mock complexo do SDK aqui
# from ..test_agents.test_brain import mock_openai_sdk 

# Mock para a função process_message
# Usamos AsyncMock porque process_message é uma função async
mock_process_message = AsyncMock()

# Fixture para garantir que o engine não seja None durante os testes de API
@pytest.fixture(autouse=True)
def mock_db_engine_for_api(monkeypatch):
    """ Mocks the database engine in session.py to prevent NameError during dependency resolution. """
    mock_engine = MagicMock() # Só precisa não ser None
    monkeypatch.setattr("app.db.session.engine", mock_engine)
    # Não precisa de yield/teardown complexo, monkeypatch gerencia


async def mock_override_get_current_user() -> User:
    # Retorna um objeto User mockado ou com dados fixos para teste
    return User(id=1, username="testuser", hashed_password="fakehash")

# Sobrescrever a dependência ANTES de rodar os testes que a usam
# REMOVER: Override global removido
# app.dependency_overrides[get_current_user] = mock_override_get_current_user

@pytest.mark.asyncio
async def test_chat_endpoint_success(monkeypatch):
    """
    Testa o endpoint /api/chat com uma solicitação bem-sucedida.
    Mocka diretamente a função process_message.
    """
    # Aplicar override da dependência especificamente para este teste
    app.dependency_overrides[get_current_user] = mock_override_get_current_user
    try:
        # Mock para process_message - precisa aceitar user_id agora
        async def mock_process(message_content, user_id: int | None = None):
            return f"Resposta mockada para: {message_content}"
        
        monkeypatch.setattr("app.api.chat.process_message", mock_process)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            # Enviar um token JWT dummy (mesmo que não seja validado pelo mock)
            # para passar da camada inicial do OAuth2PasswordBearer
            headers = {"Authorization": "Bearer dummytokenthatisnotchecked"}
            response = await client.post("/api/chat", json={"content": "Olá"}, headers=headers)
            
        assert response.status_code == 200
        assert response.json() == {"response": "Resposta mockada para: Olá"}
    finally:
        # Limpar o override
        del app.dependency_overrides[get_current_user]


@pytest.mark.asyncio
async def test_chat_endpoint_empty_message(monkeypatch):
    """
    Testa o endpoint /api/chat com uma mensagem vazia.
    Mocka diretamente a função process_message.
    """
    # Aplicar override da dependência especificamente para este teste
    app.dependency_overrides[get_current_user] = mock_override_get_current_user
    try:
        # Mock para process_message - precisa aceitar user_id agora
        async def mock_process(message_content, user_id: int | None = None):
            return f"Resposta mockada para: {message_content}" 
        
        monkeypatch.setattr("app.api.chat.process_message", mock_process)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            headers = {"Authorization": "Bearer dummytokenthatisnotchecked"}
            response = await client.post("/api/chat", json={"content": ""}, headers=headers)
            
        assert response.status_code == 200
        assert response.json() == {"response": "Resposta mockada para: "}
    finally:
        # Limpar o override
        del app.dependency_overrides[get_current_user]


@pytest.mark.asyncio
async def test_chat_endpoint_agent_error(monkeypatch):
    """
    Testa o endpoint /api/chat quando o processamento do agente falha.
    Mocka process_message para levantar uma exceção.
    """
    # Aplicar override da dependência especificamente para este teste
    app.dependency_overrides[get_current_user] = mock_override_get_current_user
    try:
        # Mock assíncrono para simular uma exceção - precisa aceitar user_id agora
        async def mock_process_message_error(message, user_id: int | None = None):
            raise Exception("Erro simulado no process_message")
        
        monkeypatch.setattr("app.api.chat.process_message", mock_process_message_error)
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            headers = {"Authorization": "Bearer dummytokenthatisnotchecked"}
            response = await client.post("/api/chat", json={"content": "Testar erro"}, headers=headers)
            
        assert response.status_code == 500
        assert "Erro ao processar mensagem" in response.json()["detail"]
        assert "Erro simulado no process_message" in response.json()["detail"]
    finally:
        # Limpar o override
        del app.dependency_overrides[get_current_user]


@pytest.mark.asyncio
async def test_get_chat_history_endpoint():
    """
    Testa o endpoint /api/chat/history.
    """
    # Este endpoint NÃO está protegido, não precisa de override nem token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/api/chat/history")
        
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_health_check_endpoint():
    """
    Testa o endpoint /health.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_root_endpoint():
    """
    Testa o endpoint raiz (/).
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/")
    
    assert response.status_code == 200
    assert "name" in response.json()
    assert response.json()["name"] == "Voxy API"
    assert "version" in response.json()
    # Limpa os overrides após os testes se necessário (boa prática em conftest.py, mas aqui para clareza)
    app.dependency_overrides = {} 