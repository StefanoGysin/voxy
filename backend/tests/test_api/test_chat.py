"""
Testes para os endpoints de API do chat.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from backend.app.main import app
import backend.app.api.chat as chat_api # Para mockar

# Não precisamos mais do mock complexo do SDK aqui
# from ..test_agents.test_brain import mock_openai_sdk 


@pytest.mark.asyncio
async def test_chat_endpoint_success(monkeypatch):
    """
    Testa o endpoint /api/chat com uma solicitação bem-sucedida.
    Mocka diretamente a função process_message.
    """
    # Mock para process_message
    async def mock_process(message_content):
        return f"Resposta mockada para: {message_content}"
    
    monkeypatch.setattr(chat_api, "process_message", mock_process)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.post("/api/chat", json={"content": "Olá"})
        
    assert response.status_code == 200
    assert response.json() == {"response": "Resposta mockada para: Olá"}


@pytest.mark.asyncio
async def test_chat_endpoint_empty_message(monkeypatch):
    """
    Testa o endpoint /api/chat com uma mensagem vazia.
    Mocka diretamente a função process_message.
    """
    async def mock_process(message_content):
        return f"Resposta mockada para: {message_content}" 
        
    monkeypatch.setattr(chat_api, "process_message", mock_process)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.post("/api/chat", json={"content": ""})
        
    assert response.status_code == 200
    assert response.json() == {"response": "Resposta mockada para: "}


@pytest.mark.asyncio
async def test_chat_endpoint_agent_error(monkeypatch):
    """
    Testa o endpoint /api/chat quando o processamento do agente falha.
    Mocka process_message para levantar uma exceção.
    """
    # Mock assíncrono para simular uma exceção
    async def mock_process_message_error(message):
        raise Exception("Erro simulado no process_message")
    
    monkeypatch.setattr(chat_api, "process_message", mock_process_message_error)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.post("/api/chat", json={"content": "Testar erro"})
        
    assert response.status_code == 500
    assert "Erro ao processar mensagem" in response.json()["detail"]
    assert "Erro simulado no process_message" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_chat_history_endpoint():
    """
    Testa o endpoint /api/chat/history.
    """
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