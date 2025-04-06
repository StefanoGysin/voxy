import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
import os

# Importar e carregar .env ANTES de importar qualquer código da app
from dotenv import load_dotenv
load_dotenv()

# Adicionar o diretório 'backend' ao sys.path para que pytest encontre o pacote 'app'
# Isso é útil quando se executa pytest da raiz do projeto.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar a aplicação FastAPI e dependências de DB APÓS ajustar o path e carregar .env
from app.main import app
from app.db.session import get_db, engine # Importar engine e get_db original
from sqlmodel import Session, SQLModel, create_engine # Importar Session, SQLModel e create_engine
from app.core.config import settings # Para obter DATABASE_URL se necessário

# Usar a engine principal por enquanto. Idealmente, usar settings.TEST_DATABASE_URL
# test_engine = create_engine(settings.DATABASE_URL) # Ou TEST_DATABASE_URL

# --- Fixture de Sessão de Teste Dedicada --- 
@pytest.fixture(scope="function")
def session() -> Session:
    """
    Fixture que fornece uma sessão de banco de dados isolada para um teste.
    Cria tabelas, inicia transação, faz yield da sessão, faz rollback e dropa tabelas.
    """
    # Criar tabelas antes do teste
    SQLModel.metadata.create_all(engine) 
    
    connection = engine.connect()
    transaction = connection.begin()
    db = Session(bind=connection)
    
    try:
        yield db # Fornece a sessão para o teste
    finally:
        db.close()
        # Reverter a transação
        transaction.rollback()
        # Fechar conexão
        connection.close()
        # Dropar tabelas após o teste
        SQLModel.metadata.drop_all(engine)

# --- Fixture do Cliente HTTP --- 
@pytest_asyncio.fixture(scope="function")
async def client(session: Session) -> AsyncClient: # Depende da fixture session
    """ 
    Fixture centralizada do cliente HTTP.
    Usa a fixture 'session' para garantir que a app use a sessão de teste.
    """
    
    # Override da dependência get_db DENTRO da fixture do cliente
    # para garantir que a mesma sessão seja usada
    def override_get_db_for_client():
        yield session

    app.dependency_overrides[get_db] = override_get_db_for_client
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
        
    # Limpar o override após o cliente ser usado
    del app.dependency_overrides[get_db]

# TODO Futuro: Considerar fixtures mais robustas para criar/limpar tabelas
# e usar um banco de dados de teste separado (ex: SQLite em memória ou outro DB).

# Outras fixtures globais ou hooks podem ser adicionados aqui. 