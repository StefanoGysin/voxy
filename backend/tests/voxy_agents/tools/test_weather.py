import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import json

from app.voxy_agents.tools.weather import get_weather, _get_weather_logic
from app.core.config import Settings # Para mockar a chave API

# Marcar todos os testes neste módulo para usar asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_settings():
    """Fixture para mockar as configurações, incluindo a chave API."""
    with patch('app.voxy_agents.tools.weather.settings') as mock:
        mock.OPENWEATHERMAP_API_KEY = "fake_api_key"
        mock.DEBUG = False # Desabilitar logs de debug nos testes por padrão
        yield mock

# --- Testes para get_weather (e sua lógica interna _get_weather_logic) ---

@patch('app.voxy_agents.tools.weather.httpx.AsyncClient')
async def test_get_weather_success(mock_async_client, mock_settings):
    """Testa o caso de sucesso de obter o clima."""
    # Configurar o mock da resposta da API
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "weather": [{"description": "céu limpo"}],
        "main": {
            "temp": 25.5,
            "feels_like": 26.0,
            "temp_min": 24.0,
            "temp_max": 27.0,
            "humidity": 60
        },
        "wind": {"speed": 3.5},
        "name": "Cidade Teste"
    }
    mock_response.raise_for_status.return_value = None # Não levanta erro

    # Configurar o mock do cliente HTTP para retornar a resposta mockada
    mock_client_instance = AsyncMock()
    mock_client_instance.get.return_value = mock_response
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance # Para o context manager 'async with'

    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Preparar os argumentos em formato JSON
    city = "Cidade Teste"
    args_json = json.dumps({"city": city})
    
    # Chamar a função usando on_invoke_tool
    result = await get_weather.on_invoke_tool(mock_context, args_json)

    # Verificar se o cliente HTTP foi chamado corretamente
    mock_client_instance.get.assert_awaited_once()
    call_args, call_kwargs = mock_client_instance.get.call_args
    assert call_args[0] == "https://api.openweathermap.org/data/2.5/weather"
    assert call_kwargs['params'] == {
        "q": city,
        "appid": "fake_api_key",
        "units": "metric",
        "lang": "pt_br"
    }

    # Verificar o resultado formatado
    expected_result = (
        "Tempo em Cidade Teste: céu limpo. "
        "Temperatura atual: 25.5°C (sensação térmica: 26.0°C). "
        "Min/Max hoje: 24.0°C/27.0°C. "
        "Umidade: 60%. "
        "Vento: 3.5 m/s."
    )
    assert result == expected_result

@patch('app.voxy_agents.tools.weather.settings')
async def test_get_weather_api_key_not_configured(mock_settings):
    """Testa o caso em que a chave API não está configurada."""
    mock_settings.OPENWEATHERMAP_API_KEY = None # Simular chave não configurada

    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Preparar os argumentos em formato JSON
    city = "Qualquer Cidade"
    args_json = json.dumps({"city": city})
    
    # Chamar a função usando on_invoke_tool
    result = await get_weather.on_invoke_tool(mock_context, args_json)

    assert result == "Erro: Chave de API do OpenWeatherMap não configurada."

@patch('app.voxy_agents.tools.weather.httpx.AsyncClient')
async def test_get_weather_city_not_found(mock_async_client, mock_settings):
    """Testa o caso em que a cidade não é encontrada (HTTP 404)."""
    # Configurar o mock da resposta para simular 404
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 404
    mock_response.text = '{"cod": "404", "message": "city not found"}' # Exemplo de corpo
    # Configurar raise_for_status para levantar o erro apropriado
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="Not Found", request=MagicMock(), response=mock_response
    )

    # Configurar o cliente HTTP mock
    mock_client_instance = AsyncMock()
    mock_client_instance.get.return_value = mock_response
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Preparar os argumentos em formato JSON
    city = "Cidade Inexistente"
    args_json = json.dumps({"city": city})
    
    # Chamar a função usando on_invoke_tool
    result = await get_weather.on_invoke_tool(mock_context, args_json)

    # Verificar se o cliente HTTP foi chamado
    mock_client_instance.get.assert_awaited_once()

    # Verificar a mensagem de erro retornada
    assert result == f"Erro: Cidade '{city}' não encontrada."

@patch('app.voxy_agents.tools.weather.httpx.AsyncClient')
async def test_get_weather_invalid_api_key(mock_async_client, mock_settings):
    """Testa o caso em que a chave API é inválida (HTTP 401)."""
    # Configurar o mock da resposta para simular 401
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 401
    mock_response.text = '{"cod": 401, "message": "Invalid API key..."}' # Exemplo
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="Unauthorized", request=MagicMock(), response=mock_response
    )

    # Configurar o cliente HTTP mock
    mock_client_instance = AsyncMock()
    mock_client_instance.get.return_value = mock_response
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Preparar os argumentos em formato JSON
    city = "Qualquer Cidade"
    args_json = json.dumps({"city": city})
    
    # Chamar a função usando on_invoke_tool
    result = await get_weather.on_invoke_tool(mock_context, args_json)

    mock_client_instance.get.assert_awaited_once()
    assert result == "Erro: Chave de API inválida ou não autorizada."

@patch('app.voxy_agents.tools.weather.httpx.AsyncClient')
async def test_get_weather_http_error(mock_async_client, mock_settings):
    """Testa um erro HTTP genérico (ex: 500)."""
    # Configurar o mock da resposta para simular 500
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 500
    mock_response.text = '{"cod": 500, "message": "Internal server error"}' # Exemplo
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="Internal Server Error", request=MagicMock(), response=mock_response
    )

    # Configurar o cliente HTTP mock
    mock_client_instance = AsyncMock()
    mock_client_instance.get.return_value = mock_response
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Preparar os argumentos em formato JSON
    city = "Outra Cidade"
    args_json = json.dumps({"city": city})
    
    # Chamar a função usando on_invoke_tool
    result = await get_weather.on_invoke_tool(mock_context, args_json)

    mock_client_instance.get.assert_awaited_once()
    assert result == f"Ocorreu um erro técnico (500) ao buscar a previsão do tempo para {city}."

@patch('app.voxy_agents.tools.weather.httpx.AsyncClient')
async def test_get_weather_request_error(mock_async_client, mock_settings):
    """Testa um erro de conexão (httpx.RequestError)."""
    # Configurar o cliente HTTP mock para levantar RequestError
    mock_client_instance = AsyncMock()
    mock_client_instance.get.side_effect = httpx.RequestError("Erro de conexão simulado", request=MagicMock())
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Preparar os argumentos em formato JSON
    city = "Cidade Desconectada"
    args_json = json.dumps({"city": city})
    
    # Chamar a função usando on_invoke_tool
    result = await get_weather.on_invoke_tool(mock_context, args_json)

    mock_client_instance.get.assert_awaited_once()
    assert result == f"Não foi possível conectar ao serviço de previsão do tempo para {city}."

@patch('app.voxy_agents.tools.weather.httpx.AsyncClient')
async def test_get_weather_unexpected_exception(mock_async_client, mock_settings):
    """Testa uma exceção genérica inesperada."""
    # Configurar o cliente HTTP mock para levantar uma exceção genérica
    # após a chamada bem-sucedida (simulando erro no processamento do JSON, por exemplo)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError("Erro de parsing JSON simulado") # Simular erro

    mock_client_instance = AsyncMock()
    mock_client_instance.get.return_value = mock_response
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Preparar os argumentos em formato JSON
    city = "Cidade Bugada"
    args_json = json.dumps({"city": city})
    
    # Chamar a função usando on_invoke_tool
    result = await get_weather.on_invoke_tool(mock_context, args_json)

    mock_client_instance.get.assert_awaited_once()
    assert result == "Ocorreu um erro inesperado ao processar a previsão do tempo." 