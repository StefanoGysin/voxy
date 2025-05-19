from agents import Agent, tool, OpenAIChatCompletionsModel
from pydantic import BaseModel
from typing import Literal, Dict, Any, Optional
from openai import AsyncOpenAI

from ..core.models import VisioScanRequest
from ..core.config import settings
# Import the model name configuration
from ..core.models_config import VISIOSCAN_DEFAULT_MODEL

# TODO: Refinar instruções com exemplos e formatação de saída esperada.
VISION_INSTRUCTIONS = """
# Instruções para o Agente Visual (Vision)

## Função e Capacidades
Você é o Vision, um agente especializado em análise visual. Sua função é interpretar imagens enviadas pelo usuário e responder perguntas sobre o que está sendo exibido, utilizando suas capacidades de processamento visual e conhecimento geral.

## Comportamento Geral
- Responda SEMPRE em português do Brasil, a menos que seja solicitado outro idioma.
- Quando for solicitado a traduzir texto na imagem, priorize traduzir do idioma original para o português.
- Descreva com precisão os elementos visuais presentes na imagem.
- Quando não conseguir identificar algo claramente, indique sua incerteza.
- Mantenha um tom profissional, respeitoso e informativo.

## Processamento de Imagens
- Analise elementos visuais como objetos, pessoas, textos, cenários, cores e composições.
- Identifique relacionamentos espaciais entre elementos.
- Reconheça expressões faciais, emoções e contextos sociais quando presentes.
- Interprete gráficos, diagramas ou visualizações de dados quando aplicável.
- Extraia e traduza texto quando solicitado.

## Tipos de Análise Suportados
- **description**: Descreva a imagem em detalhes - cores, objetos, cenário, ambiente, características visíveis.
- **text_extraction**: Extraia todo o texto visível na imagem e, se solicitado, traduza para português.
- **object_detection**: Liste os principais objetos detectados na imagem e suas localizações (se possível).
- **contextual_analysis**: Interprete o significado geral, contexto ou sentimento da imagem.
- **text_translation**: Extraia o texto da imagem, traduza para português e explique seu significado/contexto.

## Formato de Resposta
1. **Para tradução de texto**: 
   - Original: [texto extraído na língua original]
   - Tradução: [tradução para português]
   - Explicação: [explicação sobre o conteúdo/contexto do texto]

2. **Para outros tipos de análise**:
   - Forneça descrições claras e bem estruturadas
   - Use parágrafos para separar diferentes aspectos da análise
   - Seja conciso e direto, focando no que é mais relevante

## Limitações
- Esclareça quando não conseguir ver detalhes muito pequenos ou textos pouco legíveis.
- Não faça suposições que vão muito além do que é visível na imagem.

IMPORTANTE: A imagem é fornecida a você através do contexto, onde existe um objeto `image_request` contendo os dados da imagem.
Você receberá a URL da imagem e deverá analisá-la com precisão.

LEMBRE-SE:
- Seja preciso na sua análise, observe detalhes que definam corretamente o conteúdo.
- Identifique corretamente animais, pessoas e objetos na imagem.
- Não invente detalhes que não estão visíveis na imagem.
"""

# --- Configuração do Modelo --- 
# 1. Instanciar o cliente OpenAI Async
# Obter a API key das configurações
openai_async_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# 2. Configurar e instanciar o modelo para o Agente
# Configurar com parâmetros específicos para processamento de imagens
vision_model = OpenAIChatCompletionsModel(
    model=VISIOSCAN_DEFAULT_MODEL, # Use configured model name
    openai_client=openai_async_client,
)
# --- Fim da Configuração do Modelo ---

class VisionAgent(Agent):
    """ Agente especializado em analisar imagens. """
    def __init__(self):
        super().__init__(
            name="Vision",
            instructions=VISION_INSTRUCTIONS,
            model=vision_model,
            tools=[],  # Vision não precisa de ferramentas próprias inicialmente.
        )
    
    async def process_image(self, request: VisioScanRequest, context: Optional[Dict[str, Any]] = None):
        """
        Processa uma imagem com base no tipo de análise solicitado.
        
        Args:
            request: VisioScanRequest contendo a imagem e o tipo de análise.
            context: Contexto opcional da execução.
            
        Returns:
            str: Resultado da análise da imagem.
        """
        image_request = request.image
        analysis_type = request.analysis_type # Manter por enquanto, pode ser útil para log ou fallback
        detail_level = request.detail if request.detail else "high" # Usar detail da request ou default
        refined_query = getattr(request, 'refined_query', None) # Obter a query refinada (será adicionada ao modelo)

        # Construir o prompt usando a refined_query ou um fallback
        if refined_query:
            prompt = refined_query
        else:
            # Fallback se refined_query não for fornecida (comportamento antigo de descrição)
            prompt = "Analise esta imagem com atenção aos detalhes. Descreva TUDO que você vê: identifique TODOS os sujeitos principais (animais, pessoas), suas características (cores, raças se aplicável), o ambiente (objetos, cores de fundo), e a cena geral."
        
        # Para debug (atualizado para mostrar a query usada)
        print(f"Processando imagem: {image_request.source}:{image_request.content[:50]}... com prompt: {prompt[:100]}...")
        
        try:
            if image_request.source == 'url':
                # Usar a API da OpenAI com o formato específico para imagens
                response = await openai_async_client.chat.completions.create(
                    model=VISIOSCAN_DEFAULT_MODEL, # Use configured model name
                    messages=[
                        {"role": "system", "content": VISION_INSTRUCTIONS},
                        {"role": "user", "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url", 
                                "image_url": {
                                    "url": image_request.content,
                                    "detail": "high"  # Solicitar alta resolução para melhor análise
                                }
                            }
                        ]}
                    ],
                    max_tokens=1000,
                    temperature=0.2,
                )
                
                # Extrair e retornar a resposta
                if response.choices and len(response.choices) > 0:
                    analysis_result = response.choices[0].message.content
                    return analysis_result
                else:
                    return "Não foi possível analisar a imagem: resposta vazia do modelo."
                    
            elif image_request.source == 'base64':
                # Formato similar para base64, mudando apenas o campo url para data
                response = await openai_async_client.chat.completions.create(
                    model=VISIOSCAN_DEFAULT_MODEL, # Use configured model name
                    messages=[
                        {"role": "system", "content": VISION_INSTRUCTIONS},
                        {"role": "user", "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url", 
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_request.content}",
                                    "detail": "high"
                                }
                            }
                        ]}
                    ],
                    max_tokens=1000,
                    temperature=0.2,
                )
                
                # Extrair e retornar a resposta
                if response.choices and len(response.choices) > 0:
                    analysis_result = response.choices[0].message.content
                    return analysis_result
                else:
                    return "Não foi possível analisar a imagem: resposta vazia do modelo."
            else:
                # Outros formatos não implementados ainda
                return f"Formato de imagem '{image_request.source}' não suportado ainda. Atualmente suportamos apenas 'url' e 'base64'."
                
        except Exception as e:
            print(f"Erro ao processar imagem com a API Vision: {str(e)}")
            return f"Erro ao analisar a imagem: {str(e)}"

# Instância do agente para ser importada em VoxyBrain
vision_agent = VisionAgent() 