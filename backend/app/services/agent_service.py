"""
Serviços para interagir com as sessões de chat e mensagens no Supabase.
"""

import uuid
from typing import Optional, Dict, Any, List
from supabase import Client
from app.db.supabase_client import get_supabase_client # Para injetar o cliente
# Importaremos os schemas Pydantic quando forem criados

async def create_session(supabase: Client, user_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
    """
    Cria uma nova sessão de chat no banco de dados Supabase.

    Args:
        supabase (Client): A instância do cliente Supabase.
        user_id (Optional[uuid.UUID]): O ID do usuário associado a esta sessão (opcional por enquanto).

    Returns:
        Dict[str, Any]: O dicionário representando a sessão criada.
        
    Raises:
        Exception: Se ocorrer um erro durante a inserção no Supabase.
    """
    try:
        # Opcional: Adicionar um título padrão ou lógica para gerar um título inicial
        session_data = {"user_id": str(user_id) if user_id else None}
        
        response = supabase.table("sessions").insert(session_data).execute()
        
        if not response.data:
            # Logar detalhes do erro se disponíveis na resposta
            error_message = response.error.message if response.error else "Nenhum dado retornado pelo Supabase"
            print(f"Erro ao criar sessão: {error_message}") # Substituir por logger adequado
            raise Exception(f"Falha ao criar sessão de chat: {error_message}")
            
        created_session = response.data[0]
        print(f"Sessão criada: {created_session['id']}") # Log
        return created_session
    except Exception as e:
        print(f"Exceção ao criar sessão: {e}") # Substituir por logger adequado
        # Poderíamos relançar um erro mais específico ou lidar de outra forma
        raise Exception(f"Erro inesperado ao criar sessão: {e}")

# --- Funções adicionais a serem implementadas --- 

async def add_message(supabase: Client, session_id: uuid.UUID, role: str, content: str, user_id: uuid.UUID) -> Dict[str, Any]:
    """
    Adiciona uma nova mensagem a uma sessão existente no Supabase.

    Args:
        supabase (Client): A instância do cliente Supabase.
        session_id (uuid.UUID): O ID da sessão à qual adicionar a mensagem.
        role (str): O papel do autor da mensagem ('user' ou 'assistant').
        content (str): O conteúdo textual da mensagem.
        user_id (uuid.UUID): O ID do usuário associado a esta sessão.

    Returns:
        Dict[str, Any]: O dicionário representando a mensagem criada.
        
    Raises:
        ValueError: Se o 'role' for inválido.
        Exception: Se ocorrer um erro durante a inserção no Supabase.
    """
    if role not in ('user', 'assistant'):
        raise ValueError("Role inválido. Deve ser 'user' ou 'assistant'.")

    try:
        message_data = {
            "session_id": str(session_id),
            "role": role,
            "content": content,
            "user_id": str(user_id)
        }
        
        response = supabase.table("messages").insert(message_data).execute()
        
        if not response.data:
            error_message = response.error.message if response.error else "Nenhum dado retornado pelo Supabase"
            print(f"Erro ao adicionar mensagem: {error_message}") # Logger
            raise Exception(f"Falha ao adicionar mensagem: {error_message}")
            
        created_message = response.data[0]
        # A trigger 'trigger_update_session_updated_at' no DB atualizará sessions.updated_at automaticamente.
        print(f"Mensagem adicionada à sessão {session_id}: {created_message['id']}") # Log
        return created_message
        
    except Exception as e:
        print(f"Exceção ao adicionar mensagem: {e}") # Logger
        raise Exception(f"Erro inesperado ao adicionar mensagem: {e}")

async def get_messages_by_session(supabase: Client, session_id: uuid.UUID, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Recupera as mensagens de uma sessão de chat específica, ordenadas por data de criação.

    Args:
        supabase (Client): A instância do cliente Supabase.
        session_id (uuid.UUID): O ID da sessão para buscar as mensagens.
        limit (int): O número máximo de mensagens a serem retornadas (padrão: 100).

    Returns:
        List[Dict[str, Any]]: Uma lista de dicionários, cada um representando uma mensagem.
        
    Raises:
        Exception: Se ocorrer um erro durante a consulta no Supabase.
    """
    try:
        response = (
            supabase.table("messages")
            .select("*") # Seleciona todas as colunas
            .eq("session_id", str(session_id)) # Filtra pela session_id
            .order("created_at", desc=False) # Ordena da mais antiga para a mais recente
            .limit(limit) # Limita o número de resultados
            .execute()
        )
        
        return response.data
        
    except Exception as e:
        print(f"Exceção ao buscar mensagens: {e}") # Logger
        raise Exception(f"Erro inesperado ao buscar mensagens da sessão {session_id}: {e}")

async def get_sessions_by_user(supabase: Client, user_id: uuid.UUID, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Recupera as sessões de chat de um usuário específico, ordenadas pela última atualização.

    Args:
        supabase (Client): A instância do cliente Supabase.
        user_id (uuid.UUID): O ID do usuário para buscar as sessões.
        limit (int): O número máximo de sessões a serem retornadas (padrão: 50).

    Returns:
        List[Dict[str, Any]]: Uma lista de dicionários, cada um representando uma sessão.
        
    Raises:
        Exception: Se ocorrer um erro durante a consulta no Supabase.
    """
    try:
        response = await (
            supabase.table("sessions")
            .select("id, created_at, updated_at, title") # Seleciona colunas específicas
            .eq("user_id", str(user_id)) # Filtra pelo user_id
            .order("updated_at", desc=True) # Ordena pela mais recente primeiro
            .limit(limit) # Limita o número de resultados
            .execute()
        )
        
        if response.error:
             error_message = response.error.message
             print(f"Erro ao buscar sessões do usuário {user_id}: {error_message}") # Logger
             raise Exception(f"Falha ao buscar sessões do usuário {user_id}: {error_message}")

        return response.data
        
    except Exception as e:
        print(f"Exceção ao buscar sessões: {e}") # Logger
        raise Exception(f"Erro inesperado ao buscar sessões do usuário {user_id}: {e}")

# async def get_sessions_by_user(supabase: Client, user_id: uuid.UUID) -> List[Dict[str, Any]]:
#     ... 