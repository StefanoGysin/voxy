# backend/app/api/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select # Para interagir com o DB
from datetime import timedelta # Importar timedelta

# Placeholder para a dependência da sessão do DB
# TODO: Implementar e importar corretamente de app.db.session ou similar
from app.db.session import get_db 

from app.db.models import User, UserCreate, UserRead
from app.core.security import get_password_hash, verify_password

# Importar função de criação de token JWT
from app.core.security import create_access_token
# Importar modelo de resposta Token
from app.core.models import Token 

# TODO: Importar funções de criação de token JWT posteriormente
# from app.core.security import create_access_token

router = APIRouter()

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_new_user(
    *, 
    session: Session = Depends(get_db), 
    user_in: UserCreate
) -> UserRead:
    """
    Registra um novo usuário no sistema.
    """
    # TODO: Refatorar a lógica CRUD para um módulo app.crud.user
    # Verificar se o usuário já existe
    existing_user = session.exec(
        select(User).where(User.username == user_in.username)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Criar hash da senha
    hashed_password = get_password_hash(user_in.password)
    
    # Criar novo objeto User (sem a senha original)
    # Usamos **user_in.model_dump() para pegar os campos de UserBase
    new_user = User(**user_in.model_dump(), hashed_password=hashed_password)
    
    # Adicionar e salvar no banco de dados
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    # Retorna explicitamente um objeto UserRead para corresponder ao response_model
    # Isso evita que a senha hasheada seja incluída na resposta e previne
    # a falha de validação que causa o ROLLBACK.
    return UserRead.model_validate(new_user)


@router.post("/login", response_model=Token) # Definir response_model como Token
async def login_for_access_token(
    *, 
    session: Session = Depends(get_db), 
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Token: # Mudar tipo de retorno para Token
    """
    Autentica um usuário e retorna um token de acesso (JWT).
    Usa OAuth2PasswordRequestForm para receber username e password.
    """
    # TODO: Refatorar a lógica CRUD para um módulo app.crud.user
    # Buscar usuário pelo username
    user = session.exec(
        select(User).where(User.username == form_data.username)
    ).first()
    
    # Verificar se o usuário existe e a senha está correta
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}, # Necessário para 401
        )
    
    # Gerar e retornar token JWT
    # Usar as configurações padrão para expiração
    access_token = create_access_token(
        data={"sub": user.username} # "sub" é o campo padrão para o identificador do sujeito
        # expires_delta pode ser passado aqui se necessário
    )
    return Token(access_token=access_token, token_type="bearer")
    
    # Placeholder antigo removido
    # return {"message": "Login successful (token generation pending)", "username": user.username}

# TODO: Adicionar este router ao app principal em main.py 