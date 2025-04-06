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
    # Verificar se o usuário já existe pelo EMAIL (que é único)
    existing_user = session.exec(
        select(User).where(User.email == user_in.email) # Mudar para User.email
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            # Mensagem de erro mais precisa
            detail="Email already registered", 
        )
    
    # Criar hash da senha
    hashed_password = get_password_hash(user_in.password)
    
    # Criar novo objeto User (incluirá username e email de user_in)
    # Excluir a senha do dump para não tentar salvar no modelo User
    user_data = user_in.model_dump(exclude={"password"})
    new_user = User(**user_data, hashed_password=hashed_password)
    
    # Adicionar ao banco de dados (SEM commit ou refresh aqui)
    # A fixture override_get_db gerenciará a transação.
    session.add(new_user)
    # session.commit() # REMOVIDO
    # session.refresh(new_user) # REMOVIDO

    # SQLModel ainda não tem o usuário com ID aqui, pois o commit não ocorreu.
    # Para retornar o UserRead com ID, precisamos fazer flush para obter o ID
    # antes do rollback da fixture.
    session.flush()
    session.refresh(new_user) # Agora o refresh funciona após o flush
    
    # Retorna UserRead validado
    # Precisamos garantir que o objeto retornado não expire após a sessão fechar
    # model_validate pode lidar com isso, mas verificar se há problemas
    return UserRead.model_validate(new_user)


@router.post("/token", response_model=Token)
async def login_for_access_token(
    *, 
    session: Session = Depends(get_db), 
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Token: 
    """
    Autentica um usuário e retorna um token de acesso (JWT).
    Usa OAuth2PasswordRequestForm para receber username (neste caso, o email) e password.
    Corresponde à URL definida no OAuth2PasswordBearer.
    """
    # Buscar usuário pelo EMAIL
    user = session.exec(
        select(User).where(User.email == form_data.username)
    ).first()
    
    # 1. Verificar se o usuário existe
    if not user:
        raise HTTPException(
            # Status correto se usuário não encontrado
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found",
            # Não incluir WWW-Authenticate para 404
        )

    # 2. Verificar se a senha está correta (só se o usuário existe)
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password", 
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Gerar e retornar token JWT
    access_token = create_access_token(
        data={"sub": user.email}
    )
    return Token(access_token=access_token, token_type="bearer")

# TODO: Adicionar este router ao app principal em main.py 