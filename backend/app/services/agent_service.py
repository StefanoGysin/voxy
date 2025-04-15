"""
Serviços para interagir com as sessões de chat e mensagens no Supabase.
"""

import uuid
import logging # Adicionado para logging
from typing import Optional, Dict, Any, List
from supabase import Client, AsyncClient # Importar AsyncClient
from app.db.supabase_client import get_supabase_client # Dependência que retorna AsyncClient
from app.core.exceptions import DatabaseError # Importar exceção customizada
# Importaremos os schemas Pydantic quando forem criados

logger = logging.getLogger(__name__) # Inicializar logger

async def create_session(supabase: AsyncClient, user_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
    """
    Cria uma nova sessão de chat no banco de dados Supabase de forma assíncrona.

    Args:
        supabase (AsyncClient): A instância do cliente Supabase assíncrono.
        user_id (Optional[uuid.UUID]): O ID do usuário associado.

    Returns:
        Dict[str, Any]: A sessão criada.
        
    Raises:
        DatabaseError: Se ocorrer um erro durante a inserção.
    """
    try:
        session_data = {"user_id": str(user_id) if user_id else None}
        
        # Usar await na chamada execute()
        response = await supabase.table("sessions").insert(session_data).execute()
        
        # Verificar se há erro na resposta - versão atualizada para Supabase 2.15.0
        try:
            # Verificar se data está presente
            if not response.data or len(response.data) == 0:
                logger.error(f"Nenhum dado retornado ao criar sessão para user_id='{user_id}', embora nenhum erro tenha sido reportado.")
                raise DatabaseError("Falha ao criar sessão de chat: Supabase não retornou dados.")
                
            created_session = response.data[0]
            logger.info(f"Sessão criada com ID: {created_session.get('id')}")
            return created_session
        except Exception as e:
            # Captura exceções genéricas não esperadas (ex: problema de rede, erro na resposta)
            logger.exception(f"Erro inesperado ao processar resposta de criação de sessão para user_id='{user_id}': {e}", exc_info=True)
            raise DatabaseError(f"Erro inesperado ao criar sessão: {e}")
    except Exception as e:
        # Captura exceções genéricas não esperadas (ex: problema de rede antes da chamada)
        logger.exception(f"Erro inesperado ao criar sessão para user_id='{user_id}': {e}", exc_info=True)
        raise DatabaseError(f"Erro inesperado ao criar sessão: {e}")

# --- Funções adicionais a serem implementadas --- 

async def add_message(supabase: AsyncClient, session_id: uuid.UUID, role: str, content: str, user_id: uuid.UUID) -> Dict[str, Any]:
    """
    Adiciona uma nova mensagem a uma sessão existente no Supabase de forma assíncrona.

    Args:
        supabase (AsyncClient): A instância do cliente Supabase assíncrono.
        session_id (uuid.UUID): O ID da sessão.
        role (str): Papel do autor ('user' ou 'assistant').
        content (str): Conteúdo da mensagem.
        user_id (uuid.UUID): O ID do usuário associado.

    Returns:
        Dict[str, Any]: A mensagem criada.
        
    Raises:
        ValueError: Se o 'role' for inválido.
        DatabaseError: Se ocorrer um erro durante a inserção.
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
        
        # Usar await na chamada execute()
        response = await supabase.table("messages").insert(message_data).execute()
        
        # Verificar se há erro na resposta - versão atualizada para Supabase 2.15.0
        try:
            if not response.data or len(response.data) == 0:
                logger.error(f"Nenhum dado retornado ao adicionar mensagem para session_id='{session_id}', embora nenhum erro tenha sido reportado.")
                raise DatabaseError("Falha ao adicionar mensagem: Supabase não retornou dados.")
                
            created_message = response.data[0]
            logger.info(f"Mensagem adicionada à sessão {session_id} com ID: {created_message.get('id')}")
            return created_message
        except Exception as e:
            logger.exception(f"Erro inesperado ao processar resposta de adição de mensagem para session_id='{session_id}': {e}", exc_info=True)
            raise DatabaseError(f"Erro inesperado ao adicionar mensagem: {e}")
        
    except Exception as e:
        logger.exception(f"Erro inesperado ao adicionar mensagem para session_id='{session_id}': {e}", exc_info=True)
        raise DatabaseError(f"Erro inesperado ao adicionar mensagem: {e}")

async def get_messages_by_session(supabase: AsyncClient, session_id: uuid.UUID, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Recupera mensagens de uma sessão específica de forma assíncrona.

    Args:
        supabase (AsyncClient): A instância do cliente Supabase assíncrono.
        session_id (uuid.UUID): O ID da sessão.
        limit (int): Máximo de mensagens a retornar.

    Returns:
        List[Dict[str, Any]]: Lista de mensagens.
        
    Raises:
        DatabaseError: Se ocorrer um erro durante a consulta.
    """
    try:
        # Usar await na chamada execute()
        response = await (
            supabase.table("messages")
            .select("*") 
            .eq("session_id", str(session_id))
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
        
        # Verificar se há erro na resposta - versão atualizada para Supabase 2.15.0
        try:
            # response.data já é a lista, retorna diretamente
            logger.debug(f"{len(response.data)} mensagens recuperadas para sessão {session_id}.")
            return response.data
        except Exception as e:
            logger.exception(f"Erro inesperado ao processar resposta de busca de mensagens da sessão {session_id}: {e}", exc_info=True)
            raise DatabaseError(f"Erro inesperado ao buscar mensagens: {e}")
        
    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar mensagens da sessão {session_id}: {e}", exc_info=True)
        raise DatabaseError(f"Erro inesperado ao buscar mensagens: {e}")

async def get_sessions_by_user(supabase: AsyncClient, user_id: uuid.UUID, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Recupera as sessões de um usuário específico de forma assíncrona.

    Args:
        supabase (AsyncClient): A instância do cliente Supabase assíncrono.
        user_id (uuid.UUID): O ID do usuário.
        limit (int): Máximo de sessões a retornar.

    Returns:
        List[Dict[str, Any]]: Lista de sessões.
        
    Raises:
        DatabaseError: Se ocorrer um erro durante a consulta.
    """
    try:
        # Usar await na chamada execute()
        response = await (
            supabase.table("sessions")
            .select("id, created_at, updated_at, title")
            .eq("user_id", str(user_id))
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        
        # Verificar se há erro na resposta - versão atualizada para Supabase 2.15.0
        try:
            # response.data já é a lista, retorna diretamente
            logger.debug(f"{len(response.data)} sessões recuperadas para usuário {user_id}.")
            return response.data
        except Exception as e:
            logger.exception(f"Erro inesperado ao processar resposta de busca de sessões do usuário {user_id}: {e}", exc_info=True)
            raise DatabaseError(f"Erro inesperado ao buscar sessões: {e}")
        
    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar sessões do usuário {user_id}: {e}", exc_info=True)
        raise DatabaseError(f"Erro inesperado ao buscar sessões: {e}")

# async def get_sessions_by_user(supabase: Client, user_id: uuid.UUID) -> List[Dict[str, Any]]:
#     ... 