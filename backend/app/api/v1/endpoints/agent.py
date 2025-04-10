"""
Endpoints da API para interação com o agente de chat e gerenciamento de sessões.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any, Tuple
# Importar Runner e agente brain
from agents import Runner
from app.agents.brain import brain_agent
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
from app.db.supabase_client import get_supabase_client
from app.core.security import get_current_user
from supabase import Client
# Importar o contextvar do gerenciador de memória
from app.memory.mem0_manager import current_user_id_var

router = APIRouter()

@router.post("/chat", response_model=AgentChatResponse)
async def handle_chat_message(
    request: AgentChatRequest = Body(...),
    supabase: Client = Depends(get_supabase_client),
    current_supabase_user: Any = Depends(get_current_user),
) -> AgentChatResponse:
    """
    Recebe uma mensagem do usuário, processa (cria/recupera sessão, salva msg),
    chama o agente 'brain' para obter uma resposta, salva a resposta e retorna.
    """
    user_uuid = getattr(current_supabase_user, 'id', None)
    if not user_uuid:
        raise HTTPException(status_code=401, detail="ID do usuário (UUID) não encontrado no token validado")

    session_id_to_use: uuid.UUID
    assistant_message_id: uuid.UUID | None = None
    messages_data: List[Dict[str, Any]] = []
    agent_history: List[Dict[str, str]] = []

    try:
        # 1. Determinar/Validar a Sessão
        if request.session_id:
            # Sessão existente: Verificar propriedade e buscar histórico
            session_response = supabase.table("sessions") \
                .select("id, user_id") \
                .eq("id", str(request.session_id)) \
                .maybe_single() \
                .execute()

            session_data = session_response.data
            if not session_data:
                raise HTTPException(status_code=404, detail=f"Sessão {request.session_id} não encontrada")
            if session_data.get("user_id") != str(user_uuid):
                raise HTTPException(status_code=403, detail="Acesso não autorizado a esta sessão")
            
            session_id_to_use = request.session_id
            print(f"Usando sessão existente: {session_id_to_use}") # Log

            # Buscar histórico da conversa para sessões existentes
            messages_data = await agent_service.get_messages_by_session(
                supabase=supabase, session_id=session_id_to_use
            )
            # Formatar o histórico para o agente
            agent_history = [{'role': msg['role'], 'content': msg['content']} for msg in messages_data]
            print(f"Histórico da sessão {session_id_to_use} recuperado e formatado ({len(agent_history)} mensagens).") # Log
        else:
            # Nova sessão: Criar
            print(f"Criando nova sessão para usuário (UUID): {user_uuid}") # Log com UUID
            created_session = await agent_service.create_session(
                supabase=supabase, user_id=str(user_uuid)
            )
            session_id_to_use = created_session['id']
            print(f"Nova sessão criada: {session_id_to_use}") # Log
            # agent_history já está inicializado como []

        # 2. Adicionar mensagem do usuário ao banco de dados
        user_message = await agent_service.add_message(
            supabase=supabase,
            session_id=session_id_to_use,
            role="user",
            content=request.query,
            user_id=user_uuid
        )
        user_message_id = user_message['id']
        print(f"Mensagem do usuário salva: {user_message_id}") # Log

        # --- Início da Modificação: ContextVar e Chamada do Agente ---
        # 3. Definir o ContextVar do User ID e Executar o agente 'brain'
        token = current_user_id_var.set(str(user_uuid))
        assistant_response_content = "Erro: Não foi possível obter a resposta do agente." # Valor padrão
        try:
            print(f"Executando agente 'brain_agent' para usuário {user_uuid} na sessão {session_id_to_use} com histórico...") # Log com UUID
            runner = Runner()
            
            # --- CORREÇÃO: Injetar histórico nas instruções --- 
            # 1. Formatar o histórico como string
            history_string = "\n\nHistórico da Conversa Atual:\n"
            if agent_history:
                for msg in agent_history:
                    history_string += f"- {msg['role']}: {msg['content']}\n"
            else:
                history_string += "- Nenhuma mensagem anterior nesta sessão.\n"
            history_string += "--- Fim do Histórico ---\n"
            
            # 2. Obter instruções originais e adicionar histórico
            original_instructions = brain_agent.instructions or ""
            dynamic_instructions = original_instructions + history_string
            
            # 3. Criar uma cópia temporária do agente com as instruções dinâmicas
            # (Evita modificar o agente global)
            temp_agent_for_run = copy.deepcopy(brain_agent)
            temp_agent_for_run.instructions = dynamic_instructions
            
            # 4. Executar com o agente temporário e sem passar history/context
            # assistant_run_result = await runner.run(brain_agent, request.query, context={'history': agent_history})
            assistant_run_result = await runner.run(temp_agent_for_run, request.query)
            # --- FIM DA CORREÇÃO ---
            
            print(f"Agente 'brain_agent' respondeu.") # Log

            # 4. Extrair o conteúdo da resposta do assistente
            # A estrutura da resposta pode variar, ajuste conforme necessário
            # Tentativa de extração mais robusta (baseada em exemplos comuns)
            if isinstance(assistant_run_result, list) and len(assistant_run_result) > 0:
                # Tenta pegar a última mensagem se for uma lista de mensagens
                last_message = assistant_run_result[-1]
                if hasattr(last_message, 'content') and isinstance(last_message.content, str):
                    assistant_response_content = last_message.content
                elif isinstance(last_message, str):
                    assistant_response_content = last_message
            elif hasattr(assistant_run_result, 'final_output') and isinstance(assistant_run_result.final_output, str):
                 assistant_response_content = assistant_run_result.final_output
            elif hasattr(assistant_run_result, 'content') and isinstance(assistant_run_result.content, str):
                 assistant_response_content = assistant_run_result.content
            elif isinstance(assistant_run_result, str): # Se a resposta for diretamente uma string
                assistant_response_content = assistant_run_result
            else:
                 print(f"WARN: Não foi possível extrair conteúdo da resposta do agente. Tipo: {type(assistant_run_result)}, Conteúdo: {assistant_run_result}")


        finally:
            # Garante que o contextvar seja resetado, mesmo em caso de erro
            current_user_id_var.reset(token)
            print(f"ContextVar resetado para usuário {user_uuid}.") # Log com UUID
        # --- Fim da Modificação ---

        print(f"Conteúdo da resposta do assistente: '{assistant_response_content[:50]}...'") # Log

        # 5. Salvar Mensagem do Assistente
        assistant_message = await agent_service.add_message(
            supabase=supabase,
            session_id=session_id_to_use,
            role="assistant",
            content=assistant_response_content, # Usar o conteúdo extraído
            user_id=user_uuid
        )
        # A resposta de add_message agora é um dicionário
        assistant_message_id = assistant_message['id']
        print(f"Mensagem do assistente salva: {assistant_message_id}") # Log

        # 6. Retornar resposta indicando sucesso e IDs relevantes
        return AgentChatResponse(
            success=True,
            session_id=session_id_to_use,
            user_message_id=user_message_id,
            assistant_content=assistant_response_content,
            assistant_message_id=assistant_message_id # Incluir o ID da mensagem do assistente
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        import traceback
        print(f"Erro detalhado no endpoint /chat: {traceback.format_exc()}") # Logger com traceback
        # Log específico para erros do agente pode ser útil aqui
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar mensagem: {e}")

@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    supabase: Client = Depends(get_supabase_client),
    current_supabase_user: Any = Depends(get_current_user)
) -> SessionListResponse:
    """
    Lista as sessões de chat do usuário logado.
    """
    user_uuid = getattr(current_supabase_user, 'id', None)
    if not user_uuid:
        raise HTTPException(status_code=401, detail="ID do usuário (UUID) não encontrado no token validado")

    try:
        sessions_data = await agent_service.get_sessions_by_user(
            supabase=supabase, user_id=user_uuid
        )
        # Converte os dicionários retornados em instâncias do schema Pydantic
        sessions_list = [SessionSchema.model_validate(s) for s in sessions_data]
        return SessionListResponse(sessions=sessions_list)
        
    except Exception as e:
        # Logar o erro e retornar um erro HTTP adequado
        print(f"Erro ao listar sessões para usuário {user_uuid}: {e}") # Log com UUID
        raise HTTPException(status_code=500, detail=f"Erro interno ao buscar sessões: {e}")

@router.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
async def get_session_messages(
    session_id: uuid.UUID,
    supabase: Client = Depends(get_supabase_client),
    current_supabase_user: Any = Depends(get_current_user)
) -> MessageListResponse:
    """
    Lista as mensagens de uma sessão de chat específica do usuário logado.
    """
    user_uuid = getattr(current_supabase_user, 'id', None)
    if not user_uuid:
        raise HTTPException(status_code=401, detail="ID do usuário (UUID) não encontrado no token validado")

    try:
        # 1. Verificar se a sessão pertence ao usuário atual (usando UUID)
        session_response = supabase.table("sessions")\
                                       .select("id, user_id")\
                                       .eq("id", str(session_id))\
                                       .maybe_single()\
                                       .execute()
        
        session_data = session_response.data
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
            
        if session_data.get("user_id") != str(user_uuid):
            raise HTTPException(status_code=403, detail="Acesso não autorizado a esta sessão")

        # 2. Se a verificação passar, buscar as mensagens
        messages_data = await agent_service.get_messages_by_session(
            supabase=supabase, session_id=session_id
        )
        
        messages_list = [MessageSchema.model_validate(m) for m in messages_data]
        return MessageListResponse(messages=messages_list)
        
    except HTTPException as http_exc: # Relança exceções HTTP conhecidas
        raise http_exc
    except Exception as e:
        print(f"Erro ao buscar mensagens da sessão {session_id} para usuário {user_uuid}: {e}") # Log com UUID
        raise HTTPException(status_code=500, detail=f"Erro interno ao buscar mensagens: {e}") 