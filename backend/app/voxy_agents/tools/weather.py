# backend/app/agents/tools/weather.py
from agents import function_tool
import httpx
import asyncio # Para o cliente httpx assíncrono
# Usar importação relativa para acessar config dentro do mesmo pacote backend
from ...core.config import settings # Importar as configurações

# Função auxiliar com a lógica real (continua async)
async def _get_weather_logic(city: str) -> str:
    """Lógica interna assíncrona para obter a previsão do tempo da API OpenWeatherMap."""
    api_key = settings.OPENWEATHERMAP_API_KEY
    # DEBUG: Log da verificação da chave API
    if settings.DEBUG:
        print(f"--- DEBUG: Chave API OpenWeatherMap {'encontrada' if api_key else 'NÃO encontrada'}. ")
    if not api_key:
        return "Erro: Chave de API do OpenWeatherMap não configurada."
    
    # URL base da API OpenWeatherMap (usando Current Weather Data API v2.5)
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric", # Para obter temperatura em Celsius
        "lang": "pt_br"   # Para obter descrições em português
    }
    
    # DEBUG: Log dos detalhes da requisição
    if settings.DEBUG:
        print(f"--- DEBUG: Chamando API OpenWeatherMap - URL: {base_url}, Params: {params} ---")
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, params=params)
            # DEBUG: Log do status da resposta
            if settings.DEBUG:
                print(f"--- DEBUG: Resposta recebida da API OpenWeatherMap - Status: {response.status_code} ---")
            response.raise_for_status() # Levanta exceção para erros HTTP (4xx ou 5xx)
            
            data = response.json()
            
            # Extrair informações relevantes
            weather_description = data.get("weather", [{}])[0].get("description", "N/A")
            temp = data.get("main", {}).get("temp", "N/A")
            feels_like = data.get("main", {}).get("feels_like", "N/A")
            temp_min = data.get("main", {}).get("temp_min", "N/A")
            temp_max = data.get("main", {}).get("temp_max", "N/A")
            humidity = data.get("main", {}).get("humidity", "N/A")
            wind_speed = data.get("wind", {}).get("speed", "N/A")
            city_name = data.get("name", city) # Usar o nome retornado pela API
            
            # DEBUG: Log dos dados extraídos
            if settings.DEBUG:
                print(f"--- DEBUG: Dados extraídos - Desc: {weather_description}, Temp: {temp}, Cidade: {city_name} ---")
            
            # Formatar a resposta
            final_response_string = (
                f"Tempo em {city_name}: {weather_description}. "
                f"Temperatura atual: {temp}°C (sensação térmica: {feels_like}°C). "
                f"Min/Max hoje: {temp_min}°C/{temp_max}°C. "
                f"Umidade: {humidity}%. "
                f"Vento: {wind_speed} m/s."
            )
            # DEBUG: Log do retorno final
            if settings.DEBUG:
                print(f"--- DEBUG: Retorno formatado da ferramenta: {final_response_string} ---")
            return final_response_string

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"Erro: Cidade '{city}' não encontrada."
        elif e.response.status_code == 401:
            return "Erro: Chave de API inválida ou não autorizada."
        else:
            # Retornar uma mensagem de erro mais genérica para o LLM
            print(f"Erro HTTP na API OpenWeatherMap: {e.response.status_code} - {e.response.text}")
            return f"Ocorreu um erro técnico ({e.response.status_code}) ao buscar a previsão do tempo para {city}."
    except httpx.RequestError as e:
        # Erros de conexão, timeout, etc.
        print(f"Erro de conexão com OpenWeatherMap: {str(e)}")
        return f"Não foi possível conectar ao serviço de previsão do tempo para {city}."
    except Exception as e:
        # Outros erros inesperados (ex: erro ao analisar JSON)
        print(f"Erro inesperado na ferramenta get_weather: {type(e).__name__} - {e}")
        return "Ocorreu um erro inesperado ao processar a previsão do tempo."

@function_tool
async def get_weather(city: str) -> str: # Tornar esta função async
    """
    Obtém a previsão do tempo atual para uma cidade específica usando OpenWeatherMap.
    (Esta função é o wrapper para o SDK de Agentes e DEVE ser async se a lógica for async).

    Args:
        city (str): O nome da cidade (e opcionalmente estado/país) para
                    obter a previsão do tempo.

    Returns:
        str: Uma string descrevendo o tempo na cidade especificada ou uma mensagem de erro.
    """
    # Log de depuração para indicar que a ferramenta foi chamada pelo agente
    if settings.DEBUG:
        print(f"--- DEBUG: Ferramenta 'get_weather' ativada para a cidade: {city} ---")
        
    # Chamar diretamente a função de lógica assíncrona com await
    # O Runner do SDK cuidará de aguardar esta função 'get_weather'
    return await _get_weather_logic(city=city) 