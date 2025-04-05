"""
Rotas de API para interação com o agente Voxy.
"""

import asyncio
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
# Remover import não utilizado se houver: from starlette.concurrency import run_in_threadpool 
from ..agents.brain import process_message # Agora importa a versão async
from typing import List, Optional

# Importar dependência de autenticação e modelo User
from app.core.security import get_current_user
from app.db.models import User

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
async def chat(message: ChatMessage, current_user: User = Depends(get_current_user)):
    """
    Envia uma mensagem para o agente e retorna sua resposta.
    Requer autenticação do usuário.
    
    Args:
        message: A mensagem enviada pelo usuário.
        current_user: O usuário autenticado (injetado pela dependência).
        
    Returns:
        A resposta do agente.
    """
    try:
        # Log para verificar o usuário autenticado (opcional)
        print(f"Recebida mensagem de: {current_user.username} (ID: {current_user.id})")
        
        # TODO: Passar user_id para process_message quando ela for adaptada
        # Por agora, passamos apenas o conteúdo
        # response_content = await process_message(message.content) 
        # ATUALIZAR: Passar user_id
        response_content = await process_message(message.content, user_id=current_user.id)
        return ChatResponse(response=response_content)
    except ValueError as ve:
        # Captura o erro específico se user_id não for passado para process_message
        logger.error(f"Erro de valor em process_message: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
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