import pytest
import httpx
from httpx import AsyncClient
from fastapi import status
from io import BytesIO
from unittest.mock import patch, AsyncMock, MagicMock
from app.core.models import TokenData
from app.core.security import get_current_user

# Fixtures de conftest.py (assumindo que existem)
# from .conftest import client, get_authenticated_client 

# Mocking
from unittest.mock import patch, AsyncMock

# ----- Testes para POST /api/v1/uploads/image -----

UPLOAD_URL = "/api/v1/uploads/image"

@pytest.mark.asyncio
async def test_upload_image_success(test_client: AsyncClient, test_user, mocker):
    """ Testa o upload bem-sucedido de uma imagem. """
    # Mockar get_current_user para retornar test_user sem validar o token
    from app.main import app
    
    # Criar um mock da estrutura do User do Supabase
    mock_user = MagicMock()
    mock_user.id = str(test_user.id)
    mock_user.email = test_user.email
    mock_user.user_metadata = {"username": test_user.username}
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    # Mock da função de upload do Supabase 
    # A função upload_image é importada diretamente no endpoint, então precisamos mockar esse caminho específico
    mocked_upload = mocker.patch(
        'app.api.v1.endpoints.uploads.upload_image',
        new_callable=AsyncMock,
        return_value="mocked/path/image.png"
    )
    
    # Criar um arquivo de imagem em memória (simulado)
    image_content = b"fake image data"
    files = {'file': ('test_image.png', BytesIO(image_content), 'image/png')}
    
    # Adicionar token fictício ao header para passar pelo middleware
    headers = {"Authorization": "Bearer test-token"}
    
    # Mockar o middleware de autenticação
    with patch("app.middleware.get_supabase_client") as mock_middleware_client:
        # Configurar o mock para pular a validação do token
        mock_auth = MagicMock()
        mock_auth.auth.get_user = AsyncMock(return_value=MagicMock())
        mock_middleware_client.return_value = mock_auth
        
        response = await test_client.post(UPLOAD_URL, files=files, headers=headers)
    
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data["image_path"] == "mocked/path/image.png"
        
        # Verificar se o mock foi chamado corretamente
        mocked_upload.assert_awaited_once() 
        # Verificar argumentos específicos
        args, kwargs = mocked_upload.await_args
        assert kwargs['file_content'] == image_content
        assert kwargs['file_name'] == 'test_image.png'
        assert kwargs['content_type'] == 'image/png'
    
    # Limpar override
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_upload_image_unauthenticated(test_client: AsyncClient):
    """ Testa o upload sem autenticação (deve falhar com 401). """
    image_content = b"fake image data"
    files = {'file': ('test_image.png', BytesIO(image_content), 'image/png')}
    
    response = await test_client.post(UPLOAD_URL, files=files)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_upload_image_invalid_file_type(test_client: AsyncClient, test_user, mocker):
    """ Testa o upload com um tipo de arquivo inválido (não imagem). """
    # Mockar get_current_user para retornar test_user sem validar o token
    from app.main import app
    
    # Criar um mock da estrutura do User do Supabase
    mock_user = MagicMock()
    mock_user.id = str(test_user.id)
    mock_user.email = test_user.email
    mock_user.user_metadata = {"username": test_user.username}
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    # Criar um arquivo de texto em memória
    text_content = b"this is not an image"
    files = {'file': ('test.txt', BytesIO(text_content), 'text/plain')}
    
    # Adicionar token fictício ao header para passar pelo middleware
    headers = {"Authorization": "Bearer test-token"}
    
    # Mockar o middleware de autenticação
    with patch("app.middleware.get_supabase_client") as mock_middleware_client:
        # Configurar o mock para pular a validação do token
        mock_auth = MagicMock()
        mock_auth.auth.get_user = AsyncMock(return_value=MagicMock())
        mock_middleware_client.return_value = mock_auth
        
        response = await test_client.post(UPLOAD_URL, files=files, headers=headers)
    
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Tipo de arquivo inválido" in response.json()["detail"]
    
    # Limpar override
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_upload_image_too_large(test_client: AsyncClient, test_user, mocker):
    """ Testa o upload com um arquivo maior que o limite permitido. """
    # Mockar get_current_user para retornar test_user sem validar o token
    from app.main import app
    
    # Criar um mock da estrutura do User do Supabase
    mock_user = MagicMock()
    mock_user.id = str(test_user.id)
    mock_user.email = test_user.email
    mock_user.user_metadata = {"username": test_user.username}
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    # Mock para evitar a chamada real ao Supabase (embora a validação ocorra antes)
    mocker.patch(
        'app.api.v1.endpoints.uploads.upload_image',
        new_callable=AsyncMock
    )

    # Criar conteúdo maior que 5MB (limite definido no endpoint)
    large_content = b"a" * (6 * 1024 * 1024) # 6MB
    files = {'file': ('large_image.png', BytesIO(large_content), 'image/png')}
    
    # Adicionar token fictício ao header para passar pelo middleware
    headers = {"Authorization": "Bearer test-token"}
    
    # Mockar o middleware de autenticação
    with patch("app.middleware.get_supabase_client") as mock_middleware_client:
        # Configurar o mock para pular a validação do token
        mock_auth = MagicMock()
        mock_auth.auth.get_user = AsyncMock(return_value=MagicMock())
        mock_middleware_client.return_value = mock_auth
        
        response = await test_client.post(UPLOAD_URL, files=files, headers=headers)
    
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        assert "Arquivo muito grande" in response.json()["detail"]
    
    # Limpar override
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_upload_image_supabase_error(test_client: AsyncClient, test_user, mocker):
    """ Testa o cenário onde o upload para o Supabase falha. """
    # Mockar get_current_user para retornar test_user sem validar o token
    from app.main import app
    
    # Criar um mock da estrutura do User do Supabase
    mock_user = MagicMock()
    mock_user.id = str(test_user.id)
    mock_user.email = test_user.email
    mock_user.user_metadata = {"username": test_user.username}
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    # Mock da função de upload para levantar uma exceção
    mocked_upload = mocker.patch(
        'app.api.v1.endpoints.uploads.upload_image',
        new_callable=AsyncMock,
        side_effect=Exception("Supabase connection failed") # Simula falha
    )
    
    image_content = b"fake image data"
    files = {'file': ('test_image.png', BytesIO(image_content), 'image/png')}
    
    # Adicionar token fictício ao header para passar pelo middleware
    headers = {"Authorization": "Bearer test-token"}
    
    # Mockar o middleware de autenticação
    with patch("app.middleware.get_supabase_client") as mock_middleware_client:
        # Configurar o mock para pular a validação do token
        mock_auth = MagicMock()
        mock_auth.auth.get_user = AsyncMock(return_value=MagicMock())
        mock_middleware_client.return_value = mock_auth
        
        response = await test_client.post(UPLOAD_URL, files=files, headers=headers)
    
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Erro interno do servidor ao processar o upload" in response.json()["detail"]
        mocked_upload.assert_awaited_once()
    
    # Limpar override
    app.dependency_overrides.clear() 