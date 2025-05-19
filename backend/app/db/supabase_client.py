"""
Gerencia a inicialização e o acesso ao cliente Supabase.
"""

import os
import uuid
import logging
from typing import Dict, Any
# Importa AsyncClient e acreate_client para uso assíncrono
from supabase import AsyncClient, acreate_client
from app.core.config import settings

# Ajusta a anotação de tipo para AsyncClient
supabase_client: AsyncClient | None = None

logger = logging.getLogger(__name__)

async def initialize_supabase_client():
    """
    Inicializa o cliente Supabase assíncrono global usando as configurações.
    
    Raises:
        ValueError: Se as variáveis de ambiente SUPABASE_URL ou 
                    SUPABASE_SERVICE_ROLE_KEY não estiverem definidas.
    """
    global supabase_client
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY devem ser definidos "
            "nas variáveis de ambiente ou no arquivo .env"
        )
    
    # Usa acreate_client para criar cliente assíncrono
    supabase_client = await acreate_client(
        settings.SUPABASE_URL, 
        settings.SUPABASE_SERVICE_ROLE_KEY
    )
    print("Cliente Supabase Assíncrono inicializado.") # Log para confirmação


def get_supabase_client() -> AsyncClient:
    """
    Retorna a instância inicializada do cliente Supabase assíncrono.
    
    Útil como dependência FastAPI.
    
    Returns:
        AsyncClient: A instância do cliente Supabase assíncrono.
        
    Raises:
        RuntimeError: Se o cliente não foi inicializado.
    """
    if supabase_client is None:
        # A inicialização deve ocorrer no lifespan do FastAPI.
        # Levantar um erro aqui é mais seguro do que inicializar sob demanda.
        raise RuntimeError("Cliente Supabase Assíncrono não inicializado. Verifique o lifespan da aplicação.")
         
    return supabase_client

# A inicialização deve ocorrer no lifespan de main.py 

# --- Novas Funções para Storage ---

async def upload_image(supabase: AsyncClient, file_content: bytes, file_name: str, content_type: str, user_id: str = None) -> str:
    """
    Faz upload de um arquivo de imagem para o bucket 'chat-images' do Supabase Storage.

    Args:
        supabase (AsyncClient): A instância do cliente Supabase assíncrono.
        file_content (bytes): O conteúdo do arquivo em bytes.
        file_name (str): O nome original do arquivo (usado para extensão).
        content_type (str): O tipo MIME do arquivo (ex: 'image/jpeg').
        user_id (str, optional): O ID do usuário que está fazendo o upload. Necessário para RLS.

    Returns:
        str: O caminho do arquivo no storage (ex: 'user_id/uuid_aleatorio.jpg') em caso de sucesso.
        
    Raises:
        ValueError: Se o content_type não for suportado (começar com 'image/').
        Exception: Para outros erros de upload do Supabase.
    """
    if not content_type.startswith("image/"):
        raise ValueError(f"Tipo de conteúdo não suportado: {content_type}. Deve ser uma imagem.")

    bucket_name: str = "chat-images"
    # Gera um nome de arquivo único preservando a extensão
    file_ext = file_name.split('.')[-1] if '.' in file_name else 'png' # Default para png se sem extensão
    
    # Se user_id for fornecido, cria um caminho que respeita as políticas RLS do Supabase
    if user_id:
        # O formato deve seguir a estrutura esperada pela política RLS: user_id/arquivo.ext
        storage_file_path: str = f"{user_id}/{uuid.uuid4()}.{file_ext}"
    else:
        # Caminho sem user_id (pode não funcionar com políticas RLS estritas)
        storage_file_path: str = f"{uuid.uuid4()}.{file_ext}" 

    try:
        # file_options para definir o content-type correto
        file_options = {"content-type": content_type, "cache-control": "3600", "upsert": "false"}
        
        response = await supabase.storage.from_(bucket_name).upload(
            path=storage_file_path, 
            file=file_content, 
            file_options=file_options
        )
        
        # A biblioteca supabase-py (v2+) não levanta exceção em caso de falha, 
        # mas o objeto retornado pode indicar erro ou não conter 'path'.
        # Precisamos verificar a resposta de forma mais robusta ou capturar logs.
        # Por enquanto, vamos assumir sucesso se não houver exceção e retornar o path.
        # Nota: A API do Supabase Storage pode retornar um 200 OK mesmo com falha (ex: RLS negando).
        # Idealmente, verificaríamos o status code ou a presença do path na resposta se a lib o expusesse.
        logger.info(f"Imagem '{storage_file_path}' enviada para o bucket '{bucket_name}'. Resposta: {response}") # Log da resposta
        
        # TODO: Melhorar a verificação de sucesso do upload baseado na resposta da API ou logs futuros.
        #       A API parece retornar um dict com 'path' em caso de sucesso: {'path': 'bucket/uuid.ext'}
        
        # Se response for um dict e tiver a chave 'path' (ou outra indicação de sucesso), 
        # ou simplesmente se não houve exceção:
        # (Assumindo sucesso por enquanto se não houver exceção)
        return storage_file_path # Retorna apenas o nome do arquivo/path relativo dentro do bucket

    except Exception as e:
        logger.exception(f"Erro ao fazer upload do arquivo '{storage_file_path}' para o bucket '{bucket_name}': {e}", exc_info=True)
        # Re-levantar a exceção para ser tratada pela camada superior (API endpoint)
        raise Exception(f"Falha no upload da imagem para o Supabase Storage: {e}")


async def create_signed_url(supabase: AsyncClient, file_path: str, expires_in: int = 3600) -> Dict[str, Any]:
    """
    Cria uma URL assinada para um arquivo no bucket 'chat-images'.

    Args:
        supabase (AsyncClient): A instância do cliente Supabase assíncrono.
        file_path (str): O caminho do arquivo no bucket (retornado por upload_image).
        expires_in (int): Tempo de validade da URL em segundos (padrão: 3600 = 1 hora).

    Returns:
        Dict[str, Any]: Um dicionário contendo a URL assinada ou um erro.
                        Ex: {'signedURL': 'http://...', 'error': None} ou {'error': '...', 'signedURL': None}
    
    Raises:
        Exception: Para erros inesperados durante a criação da URL.
    """
    bucket_name: str = "chat-images"
    try:
        response = await supabase.storage.from_(bucket_name).create_signed_url(file_path, expires_in)
        # A resposta é um dicionário com 'signedURL' ou 'error'
        logger.info(f"URL assinada criada para '{file_path}' no bucket '{bucket_name}'. Expira em {expires_in}s.")
        
        # Verifica se a chave 'signedURL' está presente e não é None/vazia
        if response and response.get('signedURL'):
            return response # Retorna o dict {'signedURL': '...', 'error': None}
        else:
            error_message = response.get('error', 'Erro desconhecido ao criar URL assinada.')
            logger.error(f"Falha ao criar URL assinada para '{file_path}': {error_message}")
            # Retorna o dicionário de erro como recebido da lib
            return {'signedURL': None, 'error': error_message}

    except Exception as e:
        logger.exception(f"Erro inesperado ao criar URL assinada para '{file_path}': {e}", exc_info=True)
        raise Exception(f"Falha ao criar URL assinada no Supabase Storage: {e}") 