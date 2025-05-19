"""
Endpoints da API para interação com o agente de chat e gerenciamento de sessões.
"""

import uuid
import logging # Adicionado
import re # Adicionado para regex de URL
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Body, status, Form, File, UploadFile # Adicionado Form, File, UploadFile
from typing import List, Dict, Any, Tuple, Optional # Adicionado Optional
# Importar Runner e agente brain
from agents import Runner
from app.voxy_agents.brain import brain_agent
import copy

from app.schemas.agent import (
    # AgentChatRequest, # Não usado mais diretamente como Body
    AgentChatResponse,
    SessionListResponse,
    MessageListResponse,
    Session as SessionSchema,
    Message as MessageSchema
)
from app.services import agent_service
from app.db.supabase_client import get_supabase_client, create_signed_url # Retorna AsyncClient
from app.core.security import get_current_user # Já é async
from supabase import Client, AsyncClient # Importar AsyncClient
# Importar o contextvar do gerenciador de memória
from app.memory.mem0_manager import current_user_id_var
from app.core.exceptions import DatabaseError # Importar exceção customizada
from app.core.models import ImageRequest # Adicionado ImageRequest

logger = logging.getLogger(__name__) # Adicionado
router = APIRouter()

# Regex simples para validar a estrutura básica de uma URL HTTP/HTTPS
URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://' # http:// ou https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domínio...
    r'localhost|' # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...ou ip
    r'(?::\d+)?' # porta opcional
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

# Modificado para aceitar Form data e opcionalmente image_url
@router.post("/chat", response_model=AgentChatResponse)
async def handle_chat_message(
    # Usar Form em vez de Body(AgentChatRequest)
    query: str = Form(...),
    session_id: Optional[uuid.UUID] = Form(None), # session_id agora via Form
    image_url: Optional[str] = Form(None), # Mantido por ora, mas image_path terá prioridade
    image_path: Optional[str] = Form(None), # NOVO campo opcional para path da imagem no storage
    # TODO: Implementar suporte a UploadFile para uploads diretos
    # image_file: Optional[UploadFile] = File(None),
    supabase: AsyncClient = Depends(get_supabase_client),
    current_supabase_user: Any = Depends(get_current_user),
) -> AgentChatResponse:
    """
    Recebe uma mensagem do usuário (e opcionalmente uma URL de imagem),
    processa (cria/recupera sessão, salva msg), chama o agente 'brain'
    para obter uma resposta (passando info da imagem no prompt se houver),
    salva a resposta e retorna.
    """
    user_uuid = getattr(current_supabase_user, 'id', None)
    if not user_uuid:
        logger.error("ID do usuário (UUID) não encontrado no objeto User do Supabase retornado por get_current_user")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao obter ID do usuário autenticado.")

    session_id_to_use: uuid.UUID
    assistant_message_id: uuid.UUID | None = None
    messages_data: List[Dict[str, Any]] = []
    agent_history: List[Dict[str, str]] = []
    image_request_data: Optional[ImageRequest] = None
    message_content_for_agent: str = query # Começa com a query original

    try:
        # --- Processamento da Imagem --- (Modificado para priorizar image_path)
        signed_image_url_for_context: Optional[str] = None

        if image_path: 
            logger.info(f"Processando image_path '{image_path}' fornecido pelo usuário {user_uuid} para sessão {session_id or 'nova'}")
            # Gerar URL assinada para a imagem recém-carregada
            logger.info(f"Gerando URL assinada para o caminho: {image_path}")
            signed_url_response = await create_signed_url(
                supabase=supabase,
                file_path=image_path,
                expires_in=300 # Definir explicitamente 5 minutos
            )
            signed_image_url_for_context = signed_url_response["signedURL"]
            logger.debug(f"URL assinada gerada: {signed_image_url_for_context}")
            image_request_data = ImageRequest(source='url', content=signed_image_url_for_context)
            # Adicionar info ao prompt para o agente (opcional, mas útil para debugging)
            message_content_for_agent += f" [Image Uploaded: {image_path}]"
            logger.info(f"URL assinada gerada para '{image_path}': {signed_image_url_for_context[:50]}... expires in 300s")
        elif image_url:
            # Lógica existente para image_url (se image_path não foi fornecido)
            logger.info(f"Processando image_url fornecida pelo usuário {user_uuid} para sessão {session_id or 'nova'}: {image_url}")
            if not URL_REGEX.match(image_url):
                logger.warning(f"URL da imagem inválida fornecida pelo usuário {user_uuid}: {image_url}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de URL da imagem inválido.")
            # A URL original já será usada no ImageRequest
            signed_image_url_for_context = image_url 
            image_request_data = ImageRequest(source='url', content=signed_image_url_for_context)
            message_content_for_agent += f" [Image URL: {image_url}]"
            logger.info(f"Imagem URL '{image_url}' será usada diretamente.")
        
        # TODO: Adicionar lógica para image_file (base64 ou armazenamento temporário)
        # elif image_file:
            # ... (validar, processar, criar ImageRequest com source='base64' ou 'file_id')
            # message_content_for_agent += f" [Image Attached: {image_file.filename}]"

        # --- Determinar/Validar a Sessão ---
        if session_id:
            # Sessão existente: Verificar propriedade e buscar histórico
            session_response = await supabase.table("sessions") \
                .select("id, user_id") \
                .eq("id", str(session_id)) \
                .maybe_single() \
                .execute()

            session_data = session_response.data
            if not session_data:
                logger.warning(f"Sessão {session_id} não encontrada para usuário {user_uuid}.")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sessão {session_id} não encontrada")
            if session_data.get("user_id") != str(user_uuid):
                logger.warning(f"Usuário {user_uuid} tentou acessar sessão {session_id} de outro usuário ({session_data.get('user_id')}).")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado a esta sessão")
            
            try:
                session_id_to_use = uuid.UUID(session_data['id'])
            except Exception as e:
                logger.error(f"Erro ao processar dados da sessão {session_id}: {e}")
                raise DatabaseError(f"Falha ao processar dados da sessão: {e}")
            
            logger.info(f"Usando sessão existente: {session_id_to_use} para usuário {user_uuid}")

            messages_data = await agent_service.get_messages_by_session(
                supabase=supabase, session_id=session_id_to_use
            )
            agent_history = [{'role': msg['role'], 'content': msg['content']} for msg in messages_data]
            logger.info(f"Histórico da sessão {session_id_to_use} recuperado ({len(agent_history)} msgs)." )
        else:
            # Nova sessão: Criar
            logger.info(f"Criando nova sessão para usuário: {user_uuid}")
            created_session = await agent_service.create_session(
                supabase=supabase, 
                user_id=user_uuid,
            )
            session_id_to_use = created_session['id']
            logger.info(f"Nova sessão criada: {session_id_to_use}")

        # --- Adicionar mensagem do usuário (QUERY ORIGINAL) ---
        user_message = await agent_service.add_message(
            supabase=supabase,
            session_id=session_id_to_use,
            role="user",
            content=query, # Salva a query original, sem a info da imagem anexada
            user_id=user_uuid,
            metadata={'image_path': image_path} if image_path else None
        )
        user_message_id = user_message['id']
        logger.info(f"Mensagem do usuário salva (ID: {user_message_id}) na sessão {session_id_to_use}")

        # --- Definir ContextVar e Executar o agente 'brain' ---
        token = current_user_id_var.set(str(user_uuid))
        assistant_response_content = "Erro: Não foi possível obter a resposta do agente." 
        try:
            logger.info(f"Executando agente 'brain' para user {user_uuid}, session {session_id_to_use} com input: '{message_content_for_agent[:100]}...'")
            
            # Converter o histórico de mensagens para o formato esperado pelo SDK do OpenAI Agents
            # Formato padrão com 'role' e 'content'
            formatted_history = []
            if agent_history:
                for msg in agent_history:
                    formatted_history.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
                
                # Adicionar uma mensagem de sistema no início para enfatizar a importância do histórico
                formatted_history.insert(0, {
                    'role': 'system',
                    'content': f"O histórico a seguir contém {len(formatted_history)} mensagens da conversa atual. Use estas informações para responder às perguntas do usuário. Preste atenção especial a informações como localizações, preferências ou piadas mencionadas anteriormente."
                })
                
                logger.info(f"Formatado histórico com {len(formatted_history)} mensagens para a chamada ao agente")
            
            # Executar com await, usando o conteúdo que pode incluir a info da imagem
            run_context = {}
            if formatted_history:
                run_context['message_history'] = formatted_history
                
            if image_request_data:
                # O image_request_data agora contém a URL assinada (se gerada) ou a URL original
                run_context['image_request'] = image_request_data 
            
            # Em vez de chamar Runner.run diretamente, use a função auxiliar process_message
            # que já está preparada para lidar com o contexto e o handoff
            from app.voxy_agents.brain import process_message
            
            assistant_run_result = await process_message(
                message_content=message_content_for_agent,
                user_id=user_uuid,
                run_context=run_context
            )
            
            logger.info(f"Agente 'brain' respondeu para user {user_uuid}, session {session_id_to_use}.")

            # Já temos a resposta final em format string, então não precisamos da lógica de extração
            assistant_response_content = assistant_run_result

        finally:
            current_user_id_var.reset(token)
            logger.debug(f"ContextVar resetado para usuário {user_uuid}.")

        logger.debug(f"Conteúdo da resposta do assistente para user {user_uuid}, session {session_id_to_use}: '{assistant_response_content[:50]}...'")

        # --- Salvar Mensagem do Assistente (lógica existente mantida) ---
        assistant_message = await agent_service.add_message(
            supabase=supabase,
            session_id=session_id_to_use,
            role="assistant",
            content=assistant_response_content,
            user_id=user_uuid
        )
        assistant_message_id = assistant_message['id']
        logger.info(f"Mensagem do assistente salva (ID: {assistant_message_id}) na sessão {session_id_to_use}")

        # Criar objeto de mensagem completo para o usuário, validando com o schema Message
        # Isso garantirá que image_path seja extraído dos metadados se existir
        from app.schemas.agent import Message
        
        # Obter dados brutos da mensagem salva, incluindo metadados
        raw_user_message_data = user_message # Assumindo que add_message retorna o registro completo
        
        try:
            # Validar e criar a instância do schema Message
            # A validação chamará o model_validator para extrair image_path
            user_message_complete = Message.model_validate(raw_user_message_data)
            logger.debug(f"Objeto Message validado para user_message: ID={user_message_complete.id}, Path={user_message_complete.image_path}")
        except Exception as val_err:
            logger.error(f"Erro ao validar schema Message para user_message ID {user_message_id}: {val_err}", exc_info=True)
            # Fallback: Criar um objeto básico sem validação completa se a validação falhar
            user_message_complete = Message(
                id=user_message_id, 
                session_id=session_id_to_use,
                role="user", 
                content=query,
                created_at=raw_user_message_data.get('created_at', datetime.now()),
                metadata=raw_user_message_data.get('metadata')
                # image_path será None neste caso
            )

        # --- Retornar resposta (atualizada para incluir user_message) ---
        return AgentChatResponse(
            success=True,
            session_id=session_id_to_use,
            user_message_id=user_message_id,
            assistant_content=assistant_response_content,
            assistant_message_id=assistant_message_id,
            user_message=user_message_complete
        )

    except HTTPException as http_exc:
        # Relança exceções HTTP já tratadas
        raise http_exc
    except DatabaseError as db_err:
        logger.error(f"Erro de banco de dados no endpoint /chat para user {user_uuid}: {db_err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro de banco de dados: {db_err}")
    except Exception as e:
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