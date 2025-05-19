from pydantic import BaseModel
from typing import Literal, Optional


class Token(BaseModel):
    """ Modelo Pydantic para a resposta do token JWT. """
    access_token: str
    token_type: str = "bearer" # Default para o tipo Bearer


class TokenData(BaseModel):
    """ Modelo Pydantic para os dados contidos no payload do token JWT. """
    username: str | None = None
    # Adicionar outros campos se necessário (ex: user_id, roles)

# Adicionar outros modelos Pydantic de Core se necessário.

# --- Modelos para VisioScan (Análise de Imagem) ---

class ImageRequest(BaseModel):
    source: Literal["url", "base64", "file_id"]
    content: str
    file_name: Optional[str] = None
    mime_type: Optional[str] = None

class VisioScanRequest(BaseModel):
    image: ImageRequest
    analysis_type: Literal["description", "text_extraction", "object_detection", "contextual_analysis", "text_translation"]
    # O modelo específico a ser usado pode ser inferido pelo agente VisioScan com base na configuração ou passado dinamicamente,
    # mas não precisa estar neste request inicial do VoxyBrain para o VisioScan.
    # model: Optional[str] = None # Exemplo: "gpt-4o", "gpt-4-vision-preview"
    detail: Optional[Literal["low", "high", "auto"]] = None # Adicionado para controle dinâmico
    refined_query: Optional[str] = None # Adicionado para a consulta refinada vinda do VoxyBrain

# --- Fim dos Modelos VisioScan ---

# --- Modelo para Upload de Imagem ---

class UploadResponse(BaseModel):
    """ Modelo Pydantic para a resposta do endpoint de upload de imagem. """
    image_path: str # Caminho do arquivo no Supabase Storage (ex: 'uuid.jpg')
    message: Optional[str] = "Upload bem-sucedido" # Mensagem opcional de status 