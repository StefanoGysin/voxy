from typing import Optional
import uuid # Importar uuid
from sqlmodel import Field, SQLModel
from pydantic import EmailStr, Field as PydanticField


class UserBase(SQLModel):
    """ Modelo base com campos comuns, sem ID e sem segredos. """
    username: str = Field(index=True)
    email: EmailStr = Field(unique=True, index=True)
    # Adicionar outros campos públicos se necessário (ex: full_name)


class User(UserBase, table=True):
    """ Modelo de tabela do banco de dados, inclui ID e campos secretos. """
    id: Optional[int] = Field(default=None, primary_key=True)
    # Adiciona o UUID de autenticação do Supabase
    auth_uuid: Optional[uuid.UUID] = Field(default=None, index=True, unique=True)
    hashed_password: str
    # Definir nome da tabela explicitamente (opcional, mas bom)
    # __tablename__ = "users" 


class UserCreate(UserBase):
    """ Modelo Pydantic para criar um novo usuário (recebe senha). """
    password: str = PydanticField(..., min_length=8)


class UserRead(UserBase):
    """ Modelo Pydantic para ler/retornar dados de usuário (sem senha). """
    id: int
    auth_uuid: Optional[uuid.UUID] = None # Incluir no modelo de leitura também

# Adicionar outros modelos conforme necessário (ex: Token, Message, etc.) 