# backend/app/api/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
# Importar AsyncSession e select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import timedelta # Importar timedelta
from typing import Tuple, Any
import uuid # Importar uuid

# Importar get_db que agora retorna AsyncSession
from app.db.session import get_db 

from app.db.models import User, UserCreate, UserRead
# Importar também get_current_user de security
from app.core.security import get_password_hash, verify_password, get_current_user

# Importar função de criação de token JWT
from app.core.security import create_access_token
# Importar modelo de resposta Token
from app.core.models import Token 

# Importar cliente Supabase e dependência
from supabase import Client 
from app.db.supabase_client import get_supabase_client

router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_new_user(
    *,
    # session: AsyncSession = Depends(get_db), # Remover dependência do DB local
    supabase: Client = Depends(get_supabase_client),
    user_in: UserCreate # Mantém para receber dados
# ) -> UserRead: # Remover tipo de retorno antigo
) -> Any: # Retornar a resposta do Supabase ou um dict simples
    """
    Registra um novo usuário APENAS no Supabase Auth.
    """
    # 1. Tentar registrar o usuário no Supabase Auth
    try:
        print(f"Attempting Supabase Auth sign up for: {user_in.email}")
        supabase_response = supabase.auth.sign_up({
            "email": user_in.email,
            "password": user_in.password,
            "options": {
                "data": {
                    'username': user_in.username
                 }
             }
        })
        print(f"Supabase Auth sign up response received.")

        # Verificar resposta do Supabase
        if supabase_response.user is None:
            error_detail = "Supabase registration failed: User object not returned."
            print(f"Supabase Auth Error: {error_detail}")
            # Verificar se é erro de usuário já existente (pode variar)
            # Exemplo genérico, ajuste se a lib supabase der outra msg
            # if 'User already registered' in str(supabase_response): # Verificar como a lib reporta isso
            #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)

        # Extrair dados relevantes para retornar (ex: UUID e email)
        auth_uuid = supabase_response.user.id
        email = supabase_response.user.email
        print(f"Supabase Auth User ID (UUID): {auth_uuid}, Email: {email}")

        # Retornar uma resposta simples de sucesso com dados básicos
        # O Supabase pode requerer confirmação de email dependendo das config.
        return {"message": "User registered successfully. Please check email for confirmation if required.", "user_id": auth_uuid, "email": email}

    except HTTPException as http_exc:
            # Relança exceções HTTP que já foram tratadas (como usuário existente)
            raise http_exc
    except Exception as e:
        print(f"Exception during Supabase sign_up: {e}")
        # Verifica se o erro é por usuário já existente no Supabase Auth
        if "User already registered" in str(e) or "user already exists" in str(e).lower():
             raise HTTPException(
                 status_code=status.HTTP_400_BAD_REQUEST,
                 detail="Email already registered in authentication system."
             )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user with authentication service: {e}"
        )

    # O código antigo de verificação local e salvamento local foi removido.

@router.post("/token", response_model=Token)
async def login_for_access_token(
    *,
    # session: AsyncSession = Depends(get_db), # Remover dependência do DB local
    supabase: Client = Depends(get_supabase_client), # Adicionar cliente Supabase
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    """
    Autentica um usuário via Supabase Auth e retorna um token JWT.
    """
    try:
        print(f"Attempting Supabase Auth sign in for: {form_data.username}")
        # Autenticar diretamente com Supabase Auth
        response = supabase.auth.sign_in_with_password(
            {"email": form_data.username, "password": form_data.password}
        )
        print(f"Supabase Auth sign in response received.")

        # Verificar se o login foi bem-sucedido e temos o usuário
        if response.user is None or response.session is None:
            # O erro pode estar em response.error, mas a ausência de user/session já indica falha
            print(f"Supabase Auth sign in failed. Response: {response}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extrair o UUID do usuário do Supabase Auth
        user_uuid = response.user.id
        if not user_uuid:
             print("Error: Supabase Auth User ID (UUID) not found in response.")
             raise HTTPException(
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                 detail="Authentication successful but failed to retrieve user ID."
             )

        print(f"Supabase Auth sign in successful. User UUID: {user_uuid}")
        
        # Obter o token de acesso diretamente da sessão Supabase
        access_token = response.session.access_token
        if not access_token:
             print("Error: Supabase Auth access token not found in session.")
             raise HTTPException(
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                 detail="Authentication successful but failed to retrieve access token."
             )
        
        return Token(access_token=access_token, token_type="bearer")

    except Exception as e:
        # Capturar erros genéricos ou específicos do Supabase
        print(f"Exception during Supabase sign_in: {e}")
        # Retornar um erro genérico de não autorizado para segurança
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Adicionar endpoint /users/me para que os testes de segurança funcionem
# Modificar para usar o novo get_current_user e retornar dados do Supabase User
# Ajustar o response_model se necessário, ou manter UserRead se os campos essenciais coincidirem
# @router.get("/users/me", response_model=UserRead)
@router.get("/users/me") # Remover response_model temporariamente ou ajustar
async def read_users_me(current_supabase_user: Any = Depends(get_current_user)):
    """Retorna os dados do usuário autenticado obtidos do Supabase Auth."""
    # O objeto current_supabase_user tem atributos como id, email, created_at, etc.
    # Pode ser necessário mapear para UserRead se quiser manter esse schema de resposta.
    # Por enquanto, apenas retornamos o objeto como está (ou um dict)
    if not current_supabase_user:
         raise HTTPException(status_code=404, detail="User not found via token")
    # Mapeamento simples para exemplo (ajuste conforme necessário)
    return {
        "id": getattr(current_supabase_user, 'id', None), # Este será o UUID
        "email": getattr(current_supabase_user, 'email', None),
        "username": getattr(current_supabase_user.user_metadata, 'username', None), # Pega do metadata se salvamos lá
        "auth_uuid": getattr(current_supabase_user, 'id', None) # Mapeia id para auth_uuid se UserRead for usado
    }
    # return current_supabase_user # Ou retornar o objeto inteiro

# TODO: Adicionar este router ao app principal em main.py 