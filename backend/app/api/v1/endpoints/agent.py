"""
Endpoints da API para interação com o agente de chat e gerenciamento de sessões.
"""

import uuid
import logging # Adicionado
from fastapi import APIRouter, Depends, HTTPException, Body, status # Adicionar status
from typing import List, Dict, Any, Tuple
# Importar Runner e agente brain
from agents import Runner
from app.voxy_agents.brain import brain_agent
import copy

from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    SessionListResponse,
    MessageListResponse,
    Session as SessionSchema,
    Message as MessageSchema
)
from app.services import agent_service
from app.db.supabase_client import get_supabase_client # Retorna AsyncClient
from app.core.security import get_current_user # Já é async
from supabase import Client, AsyncClient # Importar AsyncClient
# Importar o contextvar do gerenciador de memória
from app.memory.mem0_manager import current_user_id_var
from app.core.exceptions import DatabaseError # Importar exceção customizada

logger = logging.getLogger(__name__) # Adicionado
router = APIRouter()

@router.post("/chat", response_model=AgentChatResponse)
async def handle_chat_message(
    request: AgentChatRequest = Body(...),
    # Injetar AsyncClient
    supabase: AsyncClient = Depends(get_supabase_client),
    current_supabase_user: Any = Depends(get_current_user),
) -> AgentChatResponse:
    """
    Recebe uma mensagem do usuário, processa (cria/recupera sessão, salva msg),
    chama o agente 'brain' para obter uma resposta, salva a resposta e retorna.
    """
    user_uuid = getattr(current_supabase_user, 'id', None)
    if not user_uuid:
        # get_current_user já levanta 401 se o token for inválido/ausente
        # Este erro indica um problema inesperado após validação bem-sucedida
        logger.error("ID do usuário (UUID) não encontrado no objeto User do Supabase retornado por get_current_user")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao obter ID do usuário autenticado.")

    session_id_to_use: uuid.UUID
    assistant_message_id: uuid.UUID | None = None
    messages_data: List[Dict[str, Any]] = []
    agent_history: List[Dict[str, str]] = []

    try:
        # 1. Determinar/Validar a Sessão
        if request.session_id:
            # Sessão existente: Verificar propriedade e buscar histórico
            # Usar await na chamada Supabase
            session_response = await supabase.table("sessions") \
                .select("id, user_id") \
                .eq("id", str(request.session_id)) \
                .maybe_single() \
                .execute()

            # Verificar erro do Supabase - versão atualizada para Supabase 2.15.0
            # A propriedade error não existe mais no objeto SingleAPIResponse
            session_data = session_response.data
            if not session_data:
                logger.warning(f"Sessão {request.session_id} não encontrada para usuário {user_uuid}.")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sessão {request.session_id} não encontrada")
            if session_data.get("user_id") != str(user_uuid):
                logger.warning(f"Usuário {user_uuid} tentou acessar sessão {request.session_id} de outro usuário ({session_data.get('user_id')}).")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado a esta sessão")
            
            try:
                # Outras operações que podem lançar exceções gerais (não HTTP)
                session_id_to_use = uuid.UUID(session_data['id']) # Converter string para UUID
            except Exception as e:
                # Capturar apenas exceções genéricas na manipulação de dados
                logger.error(f"Erro ao processar dados da sessão {request.session_id}: {e}")
                raise DatabaseError(f"Falha ao processar dados da sessão: {e}")
            
            logger.info(f"Usando sessão existente: {session_id_to_use} para usuário {user_uuid}")

            # Buscar histórico da conversa (agent_service já usa await)
            messages_data = await agent_service.get_messages_by_session(
                supabase=supabase, session_id=session_id_to_use
            )
            agent_history = [{'role': msg['role'], 'content': msg['content']} for msg in messages_data]
            logger.info(f"Histórico da sessão {session_id_to_use} recuperado ({len(agent_history)} msgs)." )
        else:
            # Nova sessão: Criar (agent_service já usa await)
            logger.info(f"Criando nova sessão para usuário: {user_uuid}")
            created_session = await agent_service.create_session(
                supabase=supabase, 
                user_id=user_uuid, # Passar UUID diretamente
            )
            # Usar o ID diretamente, pois create_session já retorna um dicionário com UUID
            session_id_to_use = created_session['id']
            logger.info(f"Nova sessão criada: {session_id_to_use}")

        # 2. Adicionar mensagem do usuário (agent_service já usa await)
        user_message = await agent_service.add_message(
            supabase=supabase,
            session_id=session_id_to_use,
            role="user",
            content=request.query,
            user_id=user_uuid
        )
        # Usar o ID diretamente, pois add_message já retorna um dicionário com UUID
        user_message_id = user_message['id']
        logger.info(f"Mensagem do usuário salva (ID: {user_message_id}) na sessão {session_id_to_use}")

        # 3. Definir ContextVar e Executar o agente 'brain'
        token = current_user_id_var.set(str(user_uuid))
        assistant_response_content = "Erro: Não foi possível obter a resposta do agente." 
        try:
            logger.info(f"Executando agente 'brain' para user {user_uuid}, session {session_id_to_use}...")
            runner = Runner()
            
            # Injetar histórico nas instruções
            history_string = "\n\nHistórico da Conversa Atual:\n"
            if agent_history:
                for msg in agent_history:
                    history_string += f"- {msg['role']}: {msg['content']}\n"
            else:
                history_string += "- Nenhuma mensagem anterior nesta sessão.\n"
            history_string += "--- Fim do Histórico ---\n"
            
            original_instructions = brain_agent.instructions or ""
            dynamic_instructions = original_instructions + history_string
            
            temp_agent_for_run = copy.deepcopy(brain_agent)
            temp_agent_for_run.instructions = dynamic_instructions
            
            # Executar com await
            assistant_run_result = await runner.run(temp_agent_for_run, request.query)
            logger.info(f"Agente 'brain' respondeu para user {user_uuid}, session {session_id_to_use}.")

            # 4. Extrair o conteúdo da resposta (lógica existente mantida)
            if isinstance(assistant_run_result, list) and len(assistant_run_result) > 0:
                last_message = assistant_run_result[-1]
                if hasattr(last_message, 'content') and isinstance(last_message.content, str):
                    assistant_response_content = last_message.content
                elif isinstance(last_message, str):
                    assistant_response_content = last_message
            elif hasattr(assistant_run_result, 'final_output') and isinstance(assistant_run_result.final_output, str):
                 assistant_response_content = assistant_run_result.final_output
            elif hasattr(assistant_run_result, 'content') and isinstance(assistant_run_result.content, str):
                 assistant_response_content = assistant_run_result.content
            elif isinstance(assistant_run_result, str):
                assistant_response_content = assistant_run_result
            else:
                 logger.warning(f"Não foi possível extrair conteúdo da resposta do agente para user {user_uuid}, session {session_id_to_use}. Tipo: {type(assistant_run_result)}, Conteúdo: {assistant_run_result}")

        finally:
            current_user_id_var.reset(token)
            logger.debug(f"ContextVar resetado para usuário {user_uuid}.")

        logger.debug(f"Conteúdo da resposta do assistente para user {user_uuid}, session {session_id_to_use}: '{assistant_response_content[:50]}...'")

        # 5. Salvar Mensagem do Assistente (agent_service já usa await)
        assistant_message = await agent_service.add_message(
            supabase=supabase,
            session_id=session_id_to_use,
            role="assistant",
            content=assistant_response_content,
            user_id=user_uuid
        )
        # Usar o ID diretamente, pois add_message já retorna um dicionário com UUID
        assistant_message_id = assistant_message['id']
        logger.info(f"Mensagem do assistente salva (ID: {assistant_message_id}) na sessão {session_id_to_use}")

        # 6. Retornar resposta
        return AgentChatResponse(
            success=True,
            session_id=session_id_to_use,
            user_message_id=user_message_id,
            assistant_content=assistant_response_content,
            assistant_message_id=assistant_message_id
        )

    except HTTPException as http_exc:
        # Relança exceções HTTP já tratadas (404, 403)
        raise http_exc
    except DatabaseError as db_err:
        # Erros do agent_service ou da validação da sessão
        logger.error(f"Erro de banco de dados no endpoint /chat para user {user_uuid}: {db_err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro de banco de dados: {db_err}")
    except Exception as e:
        # Outros erros inesperados (ex: erro no Runner)
        logger.exception(f"Erro inesperado no endpoint /chat para user {user_uuid}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno ao processar mensagem: {e}")

@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    # Injetar AsyncClient
    supabase: AsyncClient = Depends(get_supabase_client),
    current_supabase_user: Any = Depends(get_current_user)
) -> SessionListResponse:
    """
    Lista as sessões de chat do usuário logado de forma assíncrona.
    """
    user_uuid = getattr(current_supabase_user, 'id', None)
    if not user_uuid:
        logger.error("ID do usuário (UUID) não encontrado no objeto User do Supabase retornado por get_current_user em /sessions")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao obter ID do usuário autenticado.")

    try:
        # agent_service já usa await e AsyncClient
        sessions_data = await agent_service.get_sessions_by_user(
            supabase=supabase, user_id=user_uuid
        )
        sessions_list = [SessionSchema.model_validate(s) for s in sessions_data]
        logger.info(f"Listando {len(sessions_list)} sessões para usuário {user_uuid}.")
        return SessionListResponse(sessions=sessions_list)
        
    except DatabaseError as db_err:
        logger.error(f"Erro de banco de dados ao listar sessões para usuário {user_uuid}: {db_err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao buscar sessões: {db_err}")
    except Exception as e:
        logger.exception(f"Erro inesperado ao listar sessões para usuário {user_uuid}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno ao buscar sessões: {e}")

@router.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
async def get_session_messages(
    session_id: uuid.UUID,
    # Injetar AsyncClient
    supabase: AsyncClient = Depends(get_supabase_client),
    current_supabase_user: Any = Depends(get_current_user)
) -> MessageListResponse:
    """
    Lista as mensagens de uma sessão de chat específica do usuário logado de forma assíncrona.
    """
    user_uuid = getattr(current_supabase_user, 'id', None)
    if not user_uuid:
        logger.error(f"ID do usuário (UUID) não encontrado no objeto User do Supabase retornado por get_current_user em /sessions/{session_id}/messages")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao obter ID do usuário autenticado.")

    try:
        # 1. Verificar propriedade da sessão (usar await)
        session_response = await supabase.table("sessions")\
                                       .select("id, user_id")\
                                       .eq("id", str(session_id))\
                                       .maybe_single()\
                                       .execute()
        
        # Verificar erro Supabase - versão atualizada para Supabase 2.15.0
        # A propriedade error não existe mais no objeto SingleAPIResponse
        session_data = session_response.data
        if not session_data:
            logger.warning(f"Sessão {session_id} não encontrada ao buscar mensagens para usuário {user_uuid}.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessão não encontrada")
        if session_data.get("user_id") != str(user_uuid):
            logger.warning(f"Usuário {user_uuid} tentou acessar mensagens da sessão {session_id} de outro usuário ({session_data.get('user_id')}).")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado a esta sessão")
            
        try:
            # Outras operações que podem lançar exceções gerais (não HTTP)
            # Por exemplo, processamento de dados após validação
            pass
        except Exception as e:
            # Capturar apenas exceções genéricas na manipulação de dados
            logger.error(f"Erro ao processar dados da sessão {session_id}: {e}")
            raise DatabaseError(f"Falha ao processar dados da sessão: {e}")

        # 2. Buscar mensagens (agent_service já usa await)
        messages_data = await agent_service.get_messages_by_session(
            supabase=supabase, session_id=session_id
        )
        
        messages_list = [MessageSchema.model_validate(m) for m in messages_data]
        logger.info(f"Listando {len(messages_list)} mensagens para sessão {session_id} do usuário {user_uuid}.")
        return MessageListResponse(messages=messages_list)
        
    except HTTPException as http_exc: 
        raise http_exc
    except DatabaseError as db_err:
        logger.error(f"Erro de banco de dados ao buscar mensagens para sessão {session_id} (usuário {user_uuid}): {db_err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao buscar mensagens: {db_err}")
    except Exception as e:
        logger.exception(f"Erro inesperado ao buscar mensagens para sessão {session_id} (usuário {user_uuid}): {e}", exc_info=True)
        print(f"Erro ao buscar mensagens da sessão {session_id} para usuário {user_uuid}: {e}") # Log com UUID
        raise HTTPException(status_code=500, detail=f"Erro interno ao buscar mensagens: {e}") 