"""
Rotas de API para interação com o agente Voxy.
"""

import asyncio
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
# Remover import não utilizado se houver: from starlette.concurrency import run_in_threadpool 
from ..agents.brain import process_message # Agora importa a versão async
from typing import List, Optional

router = APIRouter()


class ChatMessage(BaseModel):
    """Modelo para mensagens de chat."""
    content: str


class ChatResponse(BaseModel):
    """Modelo para respostas do chat."""
    response: str


class ChatHistoryItem(BaseModel):
    """Modelo para itens do histórico de chat."""
    role: str  # "user" ou "assistant"
    content: str
    timestamp: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Envia uma mensagem para o agente e retorna sua resposta.
    Chama diretamente a função assíncrona process_message.
    
    Args:
        message: A mensagem enviada pelo usuário.
        
    Returns:
        A resposta do agente.
    """
    try:
        # Chama diretamente a função assíncrona
        response_content = await process_message(message.content)
        return ChatResponse(response=response_content)
    except Exception as e:
        # Logar o erro real no backend seria útil aqui
        # import logging
        # logger = logging.getLogger(__name__)
        # logger.exception("Erro ao processar mensagem no agente") 
        raise HTTPException(status_code=500, detail=f"Erro ao processar mensagem: {str(e)}")


@router.get("/chat/history", response_model=List[ChatHistoryItem])
async def get_chat_history():
    """
    Obtém o histórico de chat do usuário atual.
    
    Esta é uma implementação básica que retorna um histórico vazio.
    Em uma implementação completa, você recuperaria o histórico do 
    armazenamento (banco de dados, etc.)
    
    Returns:
        Uma lista de mensagens do histórico de chat.
    """
    # Implementação futura: recuperar o histórico real
    return [] 