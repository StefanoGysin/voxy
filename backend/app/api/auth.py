# backend/app/api/auth.py

import logging # Adicionado
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any
import uuid

# Remover imports não mais necessários (DB local)
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlmodel import select
# from app.db.session import get_db 
# from app.db.models import User, UserRead

# Importar schemas necessários
from app.db.models import UserCreate

# Importar get_current_user assíncrono
from app.core.security import get_current_user
# Importar modelo de resposta Token
from app.core.models import Token 
# Importar exceções customizadas
from app.core.exceptions import DatabaseError

# Importar cliente Supabase AsyncClient e dependência
from supabase import Client, AsyncClient # Importar AsyncClient
from app.db.supabase_client import get_supabase_client # Retorna AsyncClient
# Importar exceção correta do Supabase - Diretamente do pacote raiz?
from supabase import AuthApiError # <<< CORRIGIDO o caminho

logger = logging.getLogger(__name__) # Adicionado
router = APIRouter()

# Funções de senha (verify/hash) movidas para security.py

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_new_user(
    *,
    # Injetar AsyncClient
    supabase: AsyncClient = Depends(get_supabase_client),
    user_in: UserCreate
) -> Any: 
    """
    Registra um novo usuário APENAS no Supabase Auth de forma assíncrona.
    """
    try:
        logger.info(f"Tentando registro no Supabase Auth para: {user_in.email}")
        # Usar await na chamada Supabase
        supabase_response = await supabase.auth.sign_up({
            "email": user_in.email,
            "password": user_in.password,
            "options": {
                "data": {
                    'username': user_in.username
                 }
             }
        })
        logger.info(f"Resposta do Supabase Auth sign up recebida para: {user_in.email}")

        # A API do supabase-py pode retornar erro em `error` ou usuário em `user`
        if supabase_response.user is None:
            # O erro pode ou não estar populado, checar ambos
            error_detail = "Falha no registro Supabase: Usuário não retornado."
            if supabase_response.error:
                error_detail += f" Detalhe: {supabase_response.error.message}"
            logger.error(f"Erro Supabase Auth para {user_in.email}: {error_detail}")
            # Levantar exceção específica de registro (poderia ser DatabaseError ou HTTP)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)

        auth_uuid = supabase_response.user.id
        email = supabase_response.user.email
        logger.info(f"Usuário registrado no Supabase Auth com ID: {auth_uuid}, Email: {email}")

        return {"message": "Usuário registrado com sucesso. Verifique o email para confirmação se necessário.", "user_id": auth_uuid, "email": email}

    except HTTPException as http_exc:
            raise http_exc
    except Exception as e:
        logger.exception(f"Exceção durante Supabase sign_up para {user_in.email}: {e}", exc_info=True)
        # Simplificar tratamento de erro existente - a lib pode levantar exceções específicas
        if "User already registered" in str(e) or "user already exists" in str(e).lower():
             raise HTTPException(
                 status_code=status.HTTP_400_BAD_REQUEST,
                 detail="Email já registrado no sistema de autenticação."
             )
        # Para outros erros, levantamos DatabaseError
        raise DatabaseError(f"Falha ao registrar usuário no serviço de autenticação: {e}")

@router.post("/token", response_model=Token)
async def login_for_access_token(
    *,
    # Injetar AsyncClient
    supabase: AsyncClient = Depends(get_supabase_client),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    """
    Autentica um usuário via Supabase Auth de forma assíncrona e retorna um token JWT.
    """
    try:
        logger.info(f"Tentando login no Supabase Auth para: {form_data.username}")
        # Usar await na chamada Supabase
        response = await supabase.auth.sign_in_with_password(
            {"email": form_data.username, "password": form_data.password}
        )
        logger.info(f"Resposta do Supabase Auth sign in recebida para: {form_data.username}")

        if response.user is None or response.session is None:
            error_detail = "Email ou senha incorretos."
            if response.error:
                 error_detail += f" Detalhe Supabase: {response.error.message}"
            logger.warning(f"Falha no login Supabase Auth para {form_data.username}. Detalhe: {error_detail}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos", # Não expor detalhes internos
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_uuid = response.user.id
        if not user_uuid:
             logger.error(f"Erro crítico: UUID do usuário não encontrado na resposta Supabase após login bem-sucedido para {form_data.username}.")
             raise HTTPException(
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                 detail="Autenticação bem-sucedida, mas falha ao obter ID do usuário."
             )

        access_token = response.session.access_token
        if not access_token:
             logger.error(f"Erro crítico: Token de acesso não encontrado na sessão Supabase após login bem-sucedido para {form_data.username}.")
             raise HTTPException(
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                 detail="Autenticação bem-sucedida, mas falha ao obter token de acesso."
             )
        
        logger.info(f"Login bem-sucedido para {form_data.username}. User UUID: {user_uuid}")
        return Token(access_token=access_token, token_type="bearer")

    except HTTPException as http_exc:
        # Se já for uma exceção HTTP (como 401 acima), apenas relança
        raise http_exc
    # Adicionar bloco específico para AuthApiError ANTES do genérico
    except AuthApiError as auth_err:
        # Log específico para falha de autenticação conhecida
        logger.warning(f"Falha de autenticação Supabase para {form_data.username}: {auth_err}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password", # Mensagem específica
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # Captura erros inesperados (rede, etc.)
        logger.exception(f"Exceção inesperada durante Supabase sign_in para {form_data.username}: {e}", exc_info=True)
        # Levanta um erro 401 genérico por segurança
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Erro durante a autenticação.", # Mensagem genérica
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/users/me")
async def read_users_me(current_supabase_user: Any = Depends(get_current_user)):
    """Retorna os dados do usuário autenticado obtidos do Supabase Auth."""
    # get_current_user já é assíncrono e trata a exceção 401
    if not current_supabase_user:
         # Este caso não deveria ocorrer se a dependência funcionar corretamente
         logger.error("Erro inesperado: get_current_user retornou None apesar de ser uma dependência.")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao obter usuário autenticado.")

    user_metadata = getattr(current_supabase_user, 'user_metadata', {}) or {}
    logger.debug(f"Retornando dados para /users/me: user_id={getattr(current_supabase_user, 'id', None)}")
    return {
        "id": getattr(current_supabase_user, 'id', None),
        "email": getattr(current_supabase_user, 'email', None),
        "username": user_metadata.get('username', None),
        "auth_uuid": getattr(current_supabase_user, 'id', None)
    }

# TODO: Adicionar este router ao app principal em main.py 