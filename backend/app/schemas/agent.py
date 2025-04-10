"""
Schemas Pydantic para os endpoints do agente de chat com sessões.
"""

from pydantic import BaseModel, Field, ConfigDict
import uuid
from typing import Optional, List
from datetime import datetime

# --- Schemas para Requisição/Resposta do Endpoint de Chat --- 

class AgentChatRequest(BaseModel):
    """Schema para a requisição do endpoint de chat principal."""
    query: str = Field(..., description="Mensagem atual do usuário")
    session_id: Optional[uuid.UUID] = Field(None, description="UUID da conversa existente ou None para iniciar uma nova")
    # user_id será injetado pela dependência de autenticação, não vem no corpo da requisição.

class AgentChatResponse(BaseModel):
    """Schema para a resposta do endpoint de chat principal."""
    success: bool = Field(..., description="Indica se a mensagem foi recebida e o processamento iniciado")
    session_id: uuid.UUID = Field(..., description="O UUID da sessão (novo ou existente)")
    user_message_id: uuid.UUID = Field(..., description="O ID da mensagem do usuário recém-criada no DB")
    # A resposta do assistente virá via Realtime ou outro mecanismo, 
    # mas podemos incluir a mensagem do assistente aqui se for síncrono.
    assistant_content: str = Field(..., description="O conteúdo textual da resposta do assistente")
    assistant_message_id: Optional[uuid.UUID] = Field(None, description="ID da mensagem do assistente no DB, se criada imediatamente")


# --- Schemas para Representar Dados do Banco de Dados --- 
# Usados para retornar listas de sessões ou mensagens

class Message(BaseModel):
    """Schema para representar uma mensagem individual."""
    id: uuid.UUID
    session_id: uuid.UUID
    role: str = Field(..., description="'user' ou 'assistant'")
    content: str
    created_at: datetime
    
    # Permite criar o modelo a partir de atributos de objeto (como os retornados pelo Supabase/SQLModel)
    model_config = ConfigDict(from_attributes=True)

class Session(BaseModel):
    """Schema para representar uma sessão de chat."""
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None # Incluímos para referência, mas pode não ser sempre necessário no frontend
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# --- Schemas para Respostas de Endpoints de Listagem --- 

class SessionListResponse(BaseModel):
    """Schema para a resposta do endpoint que lista as sessões."""
    sessions: List[Session]

class MessageListResponse(BaseModel):
    """Schema para a resposta do endpoint que lista as mensagens de uma sessão."""
    messages: List[Message] 