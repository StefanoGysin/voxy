# backend/tests/test_agents/test_tools/test_weather.py
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
from unittest.mock import patch

# Importar a função auxiliar e as configurações
from app.agents.tools.weather import _get_weather_logic
# Importar o módulo weather para patching
from app.agents.tools import weather as weather_tool_module

# --- Fixtures e Mocks ---

@pytest.fixture
def mock_httpx_client(monkeypatch):
    """Fixture para mockar o httpx.AsyncClient."""
    mock_response = AsyncMock(spec=httpx.Response)
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = mock_response
    # Para que o contexto `async with` funcione
    mock_client.__aenter__.return_value = mock_client 
    
    # Patch no módulo weather
    monkeypatch.setattr("app.agents.tools.weather.httpx.AsyncClient", lambda: mock_client)
    return mock_client, mock_response

@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Mocka as configurações para fornecer uma chave de API válida por padrão."""
    mock_settings_obj = MagicMock()
    mock_settings_obj.OPENWEATHERMAP_API_KEY = "fake_api_key"
    mock_settings_obj.DEBUG = True # Habilitar DEBUG para logs nos testes
    # CORRIGIR: Aplicar o patch no objeto settings DENTRO do módulo weather
    monkeypatch.setattr(weather_tool_module, "settings", mock_settings_obj)
    yield mock_settings_obj # Retorna o objeto mockado se necessário

# --- Testes para _get_weather_logic --- 

@pytest.mark.asyncio
async def test_get_weather_logic_success(mock_httpx_client, mock_settings):
    """Testa o caminho de sucesso de _get_weather_logic."""
    mock_client, mock_response = mock_httpx_client
    city = "London"
    
    # Resposta simulada da API OpenWeatherMap
    fake_api_response = {
        "weather": [{"description": "nuvens dispersas"}],
        "main": {"temp": 15.5, "feels_like": 14.8, "temp_min": 13.0, "temp_max": 17.0, "humidity": 60},
        "wind": {"speed": 3.5},
        "name": "Londres" # Nome pode ser diferente da entrada
    }
    mock_response.status_code = 200
    mock_response.json.return_value = fake_api_response
    # Configurar raise_for_status para não levantar exceção
    mock_response.raise_for_status = MagicMock() 

    result = await _get_weather_logic(city=city)

    # Verificar se a chamada HTTP foi feita com os parâmetros corretos
    mock_client.get.assert_called_once()
    call_args, call_kwargs = mock_client.get.call_args
    assert call_args[0] == "https://api.openweathermap.org/data/2.5/weather"
    assert call_kwargs["params"] == {
        "q": city,
        "appid": "fake_api_key",
        "units": "metric",
        "lang": "pt_br"
    }
    
    # Verificar o conteúdo da resposta formatada
    assert "Tempo em Londres: nuvens dispersas." in result
    assert "Temperatura atual: 15.5°C" in result
    assert "sensação térmica: 14.8°C" in result
    assert "Min/Max hoje: 13.0°C/17.0°C" in result
    assert "Umidade: 60%" in result
    assert "Vento: 3.5 m/s" in result

@pytest.mark.asyncio
async def test_get_weather_logic_no_api_key(mock_settings):
    """Testa o caso onde a chave de API não está configurada."""
    mock_settings.OPENWEATHERMAP_API_KEY = None
    result = await _get_weather_logic(city="TestCity")
    assert result == "Erro: Chave de API do OpenWeatherMap não configurada."

@pytest.mark.asyncio
async def test_get_weather_logic_city_not_found(mock_httpx_client):
    """Testa o caso de erro 404 (Cidade não encontrada)."""
    mock_client, mock_response = mock_httpx_client
    city = "NonExistentCity"
    
    mock_response.status_code = 404
    # Simular que raise_for_status levanta a exceção correta
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not Found", request=MagicMock(), response=mock_response
    )

    result = await _get_weather_logic(city=city)
    assert result == f"Erro: Cidade '{city}' não encontrada."

@pytest.mark.asyncio
async def test_get_weather_logic_invalid_api_key(mock_httpx_client):
    """Testa o caso de erro 401 (Chave inválida)."""
    mock_client, mock_response = mock_httpx_client
    city = "ValidCity"
    
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Unauthorized", request=MagicMock(), response=mock_response
    )
    
    result = await _get_weather_logic(city=city)
    assert result == "Erro: Chave de API inválida ou não autorizada."

@pytest.mark.asyncio
async def test_get_weather_logic_other_http_error(mock_httpx_client):
    """Testa outros erros HTTP (ex: 500)."""
    mock_client, mock_response = mock_httpx_client
    city = "ValidCity"
    
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server Error", request=MagicMock(), response=mock_response
    )
    
    result = await _get_weather_logic(city=city)
    # A mensagem correta para erro HTTP 500
    expected_error_message = f"Ocorreu um erro técnico (500) ao buscar a previsão do tempo para {city}."
    assert result == expected_error_message

@pytest.mark.asyncio
async def test_get_weather_logic_request_error(mock_httpx_client):
    """Testa erros de conexão/request."""
    mock_client, mock_response = mock_httpx_client
    city = "ValidCity"
    
    # Simular erro na chamada .get()
    mock_client.get.side_effect = httpx.RequestError("Connection refused")
    
    result = await _get_weather_logic(city=city)
    # Corrigir a mensagem de erro esperada
    expected_error_message = f"Não foi possível conectar ao serviço de previsão do tempo para {city}."
    assert result == expected_error_message

@pytest.mark.asyncio
async def test_get_weather_logic_http_error(mock_httpx_client):
    """Testa o tratamento de erro HTTP genérico (não 404 ou 401)."""
    mock_client, mock_response = mock_httpx_client
    city = "Test City"
    
    # Simula um erro HTTP genérico (não 404 ou 401)
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    # Usar MagicMock pois raise_for_status não é awaited
    mock_response.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError(
        "Server Error", request=MagicMock(), response=mock_response
    ))
    mock_client.get.return_value = mock_response
    
    result = await _get_weather_logic(city=city)
    # A mensagem de erro esperada JÁ estava correta aqui
    expected_error_message = f"Ocorreu um erro técnico (500) ao buscar a previsão do tempo para {city}."
    assert result == expected_error_message
    mock_client.get.assert_called_once()

@pytest.mark.asyncio
async def test_get_weather_logic_connection_error(mock_settings):
    """ Testa o tratamento de erro de conexão com a API. """
    with patch('backend.app.agents.tools.weather.httpx.AsyncClient') as mock_async_client:
        mock_client = AsyncMock()
        mock_async_client.return_value.__aenter__.return_value = mock_client 
        # Configura o mock get para levantar um RequestError
        mock_client.get.side_effect = httpx.RequestError("Connection failed")
        
        result = await _get_weather_logic(city="Test City")
        # A mensagem correta para erro de conexão
        expected_error_message = f"Não foi possível conectar ao serviço de previsão do tempo para Test City."
        assert result == expected_error_message
        mock_client.get.assert_called_once()

# Não precisamos mais dos testes originais que verificavam o valor fixo
# def test_get_weather_logic_returns_fixed_string(): ...
# def test_get_weather_logic_with_different_city(): ...

# Adicione mais testes se necessário, por exemplo, para casos de borda
# da lógica real (embora com valor fixo, as opções são limitadas agora). 