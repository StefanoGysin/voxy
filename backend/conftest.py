import os
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from supabase import create_client, Client, create_async_client
import logging
import uuid
from faker import Faker
from app.db.models import UserRead  # Importar UserRead do local correto
from app.core.config import settings # Para obter URL da API nos testes
from app.main import app # Importar a instância do app FastAPI
from app.db.supabase_client import get_supabase_client # Importar a dependência original
from unittest.mock import MagicMock, AsyncMock

# Carrega variáveis de .env.test (se pytest-dotenv estiver instalado)
# As variáveis SUPABASE_TEST_URL e SUPABASE_TEST_KEY devem estar definidas lá

# Fixture para o cliente Supabase de teste (executada uma vez por sessão)
@pytest.fixture(scope="session")
def supabase_test_url() -> str:
    url = os.getenv("SUPABASE_TEST_URL")
    if not url:
        pytest.fail("Variável de ambiente SUPABASE_TEST_URL não definida. Verifique o .env.test")
    return url

@pytest.fixture(scope="session")
def supabase_test_key() -> str:
    key = os.getenv("SUPABASE_TEST_SERVICE_ROLE_KEY")
    if not key:
        pytest.fail("Variável de ambiente SUPABASE_TEST_SERVICE_ROLE_KEY não definida. Verifique o .env.test")
    return key

# Fixture principal para o cliente Supabase (AGORA ASSÍNCRONA)
@pytest.fixture(scope="function")
async def supabase_test_client(supabase_test_url: str, supabase_test_key: str) -> AsyncClient: # Mudança para async def e AsyncClient
    """
    Fixture para criar e fornecer um cliente Supabase ASSÍNCRONO (`AsyncClient`)
    configurado para o ambiente de teste. Limpa os dados após o uso.
    Escopo de função para garantir isolamento entre testes.
    """
    # --- Setup: Código executado ANTES do teste ---
    print(f"\nCriando cliente Async Supabase de teste para: {supabase_test_url}")
    # Usar create_async_client COM await
    client: AsyncClient = await create_async_client(supabase_test_url, supabase_test_key)

    yield client # O teste executa aqui com o cliente assíncrono

    # --- Teardown: Código executado APÓS o teste (ASSÍNCRONO) ---
    # Limpeza agora está na fixture cleanup_test_data, apenas fechamos o cliente se necessário
    # A biblioteca supabase-py geralmente gerencia conexões automaticamente, mas podemos adicionar um close se encontrarmos problemas
    # await client.aclose() # Descomentar se necessário
    print("\nTeardown do cliente Async Supabase de teste concluído (limpeza delegada).")

# Fixture para limpar dados após cada teste (AGORA ASSÍNCRONA)
@pytest.fixture(autouse=True)
async def cleanup_test_data(supabase_test_client: AsyncClient): # Recebe AsyncClient
    """
    Fixture executada automaticamente após cada teste (`autouse=True`).
    Limpa as tabelas principais e os usuários de teste criados no Supabase Auth.
    Usa o cliente ASSÍNCRONO com privilégios de service_role.
    """
    yield  # O teste executa aqui

    # Código de limpeza executado após o teste (ASSÍNCRONO)
    print("\nLimpando dados de teste (async)...")
    try:
        # 1. Limpar tabelas dependentes primeiro (chamadas assíncronas com await)
        await supabase_test_client.from_("messages").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        await supabase_test_client.from_("sessions").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print("Tabelas 'messages' e 'sessions' limpas (async).")

        # 2. Limpar usuários de teste do Supabase Auth (chamadas assíncronas com await)
        print("Tentando limpar usuários de teste do Supabase Auth (async)...")
        try:
            # Listar todos os usuários (assíncrono com await)
            list_response = await supabase_test_client.auth.admin.list_users()

            # O acesso aos usuários pode variar ligeiramente na resposta assíncrona, verificar documentação se falhar
            users_data = list_response.users if hasattr(list_response, 'users') else [] # Ajuste defensivo

            users_to_delete = [
                user.id for user in users_data
                if user.email and '_test_' in user.email
            ]

            if users_to_delete:
                print(f"Encontrados {len(users_to_delete)} usuários de teste para excluir:")
                for user_id in users_to_delete:
                    print(f"  - Excluindo usuário com ID: {user_id}")
                    try:
                        # delete_user (assíncrono com await)
                        await supabase_test_client.auth.admin.delete_user(user_id)
                        print(f"    Usuário {user_id} excluído com sucesso.")
                    except Exception as delete_error:
                        # Usar logging.warning para erros não críticos no teardown
                        logging.warning(f"    AVISO ao excluir usuário de teste {user_id} (async): {delete_error}")
                        print(f"    AVISO ao excluir usuário {user_id}: {delete_error}")
                print("Limpeza de usuários de teste do Supabase Auth concluída (async).")
            else:
                print("Nenhum usuário de teste encontrado para excluir do Supabase Auth (async).")

        except Exception as auth_cleanup_error:
            # Usar logging.warning para erros não críticos no teardown
            logging.warning(f"AVISO: Erro durante a limpeza de usuários do Supabase Auth (async): {auth_cleanup_error}")
            print(f"AVISO: Erro durante a limpeza de usuários do Supabase Auth (async): {auth_cleanup_error}")

    except Exception as e:
        # Usar logging.error para erros críticos no teardown
        logging.error(f"Erro crítico durante a limpeza geral de dados de teste (async): {e}")
        print(f"ERRO ao limpar dados de teste (async): {e}")

# Fixture para o cliente de teste FastAPI (recebe AsyncClient)
@pytest.fixture(scope="function")
async def test_client(supabase_test_client: AsyncClient) -> AsyncClient: # Recebe AsyncClient
    """
    Fixture para criar um cliente de teste para a aplicação FastAPI.
    SOBRESVREVE a dependência get_supabase_client para usar o cliente ASSÍNCRONO de teste.
    """
    def override_get_supabase_client():
        return supabase_test_client # Retorna o cliente ASSÍNCRONO

    app.dependency_overrides[get_supabase_client] = override_get_supabase_client

    # O cliente de teste HTTPX já é assíncrono
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    # Limpa o override após o teste
    app.dependency_overrides.clear()

fake = Faker()

# Fixture para criar usuário de teste (AGORA ASSÍNCRONA)
@pytest.fixture(scope="function")
async def test_user(supabase_test_client: AsyncClient) -> UserRead: # Recebe AsyncClient, retorna async def
    """
    Fixture para criar um usuário de teste no Supabase Auth antes de cada teste (ASSÍNCRONO)
    e retorná-lo como um objeto UserRead.
    """
    test_email = f"test_user_{uuid.uuid4()}@example.com"
    test_password = "testpassword123"
    test_username = fake.user_name() + "_test"

    print(f"\nCriando usuário de teste (async): {test_email}")
    try:
        # Usar o método create_user do admin (ASSÍNCRONO com await)
        response = await supabase_test_client.auth.admin.create_user(
            {"email": test_email, "password": test_password, "email_confirm": True,
             "user_metadata": {"username": test_username}}
        )
        # A resposta pode variar na versão async, ajustar se necessário
        user = response.user
        if not user:
             pytest.fail(f"Falha ao criar usuário de teste no Supabase Auth (async): {response}")

        print(f"Usuário de teste criado com ID: {user.id}")
        # O ID retornado já deve ser string, UUID() pode não ser necessário ou causar erro
        user_id_str = user.id
        return UserRead(
            id=uuid.UUID(user_id_str), # Tentar converter para UUID
            email=user.email,
            username=user.user_metadata.get("username") if user.user_metadata else None # Acesso seguro
        )

    except Exception as e:
        pytest.fail(f"Erro ao criar usuário de teste no Supabase Auth (async): {e}")

# Fixture para obter cabeçalho de autenticação (AGORA USA ASYNC CLIENT E MOCK ASSÍNCRONO)
@pytest.fixture(scope="function")
async def auth_headers(
    test_client: AsyncClient, # Já é AsyncClient
    test_user: UserRead,
    supabase_test_client: AsyncClient, # Recebe AsyncClient
    mocker # pytest-mock fixture
) -> dict[str, str]:
    """
    Fixture para obter o cabeçalho de autenticação para um usuário de teste.
    Faz login (MOCKADO) usando o cliente Supabase ASSÍNCRONO e retorna o cabeçalho Bearer.
    """
    login_data = {
        "username": test_user.email, # Usa o email para login conforme OAuth2PasswordRequestForm
        "password": "testpassword123" # Senha definida na fixture test_user
    }
    print(f"\nObtendo token para usuário de teste (mockado async): {test_user.email}")

    # 1. Preparar a resposta mockada para sign_in_with_password
    test_token = f"mocked-async-token-for-{test_user.id}"
    mock_signin_response = MagicMock() # Resposta simulada
    # Simular a estrutura esperada da resposta da API Supabase Auth
    mock_user_data = MagicMock()
    mock_user_data.id = str(test_user.id) # ID como string
    mock_session_data = MagicMock()
    mock_session_data.access_token = test_token

    mock_signin_response.user = mock_user_data
    mock_signin_response.session = mock_session_data

    # 2. Criar um AsyncMock que retorna a resposta mockada quando awaited
    async_signin_mock = AsyncMock(return_value=mock_signin_response)

    # 3. Fazer o patch do método assíncrono sign_in_with_password no cliente ASSÍNCRONO
    # Usar 'new=async_signin_mock' para substituir pelo AsyncMock
    mocker.patch.object(
        supabase_test_client.auth,
        'sign_in_with_password',
        new=async_signin_mock
    )

    # 4. Chamar o endpoint /token da API FastAPI (que usa o cliente Supabase mockado via DI override)
    try:
        response = await test_client.post("/api/auth/token", data=login_data)
        response.raise_for_status() # Verifica se houve erro HTTP (4xx ou 5xx)
        token_data = response.json()
        access_token = token_data.get("access_token")
        if not access_token:
             pytest.fail("Token de acesso não encontrado na resposta de login mockada.")

        # 5. Verificar se o mock assíncrono foi chamado corretamente
        async_signin_mock.assert_awaited_once_with({
            "email": login_data["username"],
            "password": login_data["password"]
        })

        print(f"Login (mockado async) bem-sucedido, token obtido: ...{access_token[-6:]}")
        return {"Authorization": f"Bearer {access_token}"}
    except Exception as e:
        # Captura erros HTTP ou outros problemas
        pytest.fail(f"Erro durante o login mockado do usuário de teste (async): {e}")

@pytest.fixture(scope="function")
async def client(test_client) -> AsyncClient:
    """
    Alias para test_client para compatibilidade com testes existentes.
    """
    return test_client

@pytest.fixture(scope="function")
async def get_authenticated_client(test_client, auth_headers, supabase_test_client, mocker):
    """
    Fixture que retorna uma função assíncrona que produz um cliente autenticado.
    Também configura o mock para o middleware de autenticação.
    """
    # Mockar o middleware para evitar o erro de cliente não inicializado
    mocker.patch("app.middleware.get_supabase_client", return_value=supabase_test_client)
    
    # Configura o override para que todas as dependências que usam get_supabase_client
    # retornem a instância de teste
    from app.main import app
    from app.db.supabase_client import get_supabase_client
    
    app.dependency_overrides[get_supabase_client] = lambda: supabase_test_client
    
    async def _get_client():
        # Criar uma cópia do cliente e adicionar os cabeçalhos de autenticação
        test_client.headers.update(auth_headers)
        return test_client
    
    yield _get_client
    
    # Limpar os overrides após os testes
    app.dependency_overrides.clear()
