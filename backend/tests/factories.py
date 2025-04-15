import factory
from factory.faker import Faker
from uuid import uuid4, UUID
from datetime import datetime
import random
from pydantic import EmailStr # Adicionado para UserCreateFactory
from typing import Optional # Importar Optional

# ===================================================================
# Imports reais dos schemas Pydantic de app.schemas.agent
# ===================================================================
from app.schemas.agent import Session as RealSessionSchema
from app.schemas.agent import Message as RealAgentMessageSchema
from app.db.models import UserCreate as RealUserCreateSchema # <- Importar UserCreate
# Removidos os imports de exemplo de Pydantic e BaseModel
# Se você tiver um User Schema real, importe-o aqui:
# from app.schemas.user import UserRead as RealUserReadSchema

# Exemplo de como um User Schema poderia ser, caso não exista:
from pydantic import BaseModel, Field, EmailStr # Necessário apenas para o UserReadFactory de exemplo
class UserReadSchemaExample(BaseModel):
    id: uuid4 = Field(default_factory=uuid4)
    username: str
    email: EmailStr

# Usaremos o schema de exemplo para UserRead por enquanto,
# pois a API /users/me retorna um dict simples agora.
# Poderíamos criar um schema Pydantic para a resposta de /users/me se desejado.
from pydantic import BaseModel, Field
class UserReadResponseSchema(BaseModel): # Schema para a resposta de /users/me
    id: Optional[UUID] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    auth_uuid: Optional[UUID] = None

# ===================================================================
# Factories
# ===================================================================

class BaseFactory(factory.Factory):
    class Meta:
        abstract = True # Não criar instâncias de BaseFactory diretamente

# Factory para o schema Session real de agent.py
class SessionFactory(BaseFactory):
    class Meta:
        model = RealSessionSchema # <- Usa o schema importado

    id = factory.LazyFunction(uuid4)
    user_id = factory.LazyFunction(uuid4) # Gera um UUID por padrão
    created_at = factory.LazyFunction(datetime.now)
    updated_at = factory.LazyAttribute(lambda o: o.created_at)
    title = Faker("sentence", nb_words=4)

# Factory para o schema Message real de agent.py
class AgentMessageFactory(BaseFactory):
    class Meta:
        model = RealAgentMessageSchema # <- Usa o schema importado

    id = factory.LazyFunction(uuid4)
    created_at = factory.LazyFunction(datetime.now)
    session_id = factory.LazyFunction(uuid4) # Precisa ser definido explicitamente ou via SubFactory
    role = factory.LazyFunction(lambda: random.choice(["user", "assistant"])) # role é str no schema real
    content = Faker("paragraph", nb_sentences=2)

# Factory para um schema UserRead (mantido como exemplo)
# Adapte ou remova se tiver um schema User real em outro arquivo
class UserReadFactory(BaseFactory):
     class Meta:
         model = UserReadSchemaExample # <- Usa o schema de exemplo definido acima
         # Se tiver um schema real: model = RealUserReadSchema

     id = factory.LazyFunction(uuid4)
     username = Faker("user_name")
     email = Faker("email")

# --- Factory para UserCreate ---
class UserCreateFactory(BaseFactory):
    class Meta:
        model = RealUserCreateSchema # <- Usa o schema UserCreate importado

    username = Faker("user_name")
    email = factory.LazyAttribute(lambda o: f"{o.username}_test_{uuid4().hex[:6]}@example.com") # Email único para teste
    password = "testpassword123" # Senha fixa para testes

# Factory para simular a resposta de /users/me
class UserReadResponseFactory(BaseFactory):
     class Meta:
         model = UserReadResponseSchema # <- Usa o schema de resposta definido acima

     id = factory.LazyFunction(uuid4) # Simula o UUID retornado
     auth_uuid = factory.LazyAttribute(lambda o: o.id) # id e auth_uuid são os mesmos
     username = Faker("user_name")
     email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")

# --- Adicione outras factories para seus schemas Pydantic conforme necessário ---
