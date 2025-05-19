"""
API Endpoints para Upload de Arquivos.
"""

import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from supabase import AsyncClient
from typing import Any, Dict
from app.core.models import UploadResponse # Modelo de resposta
from app.db.supabase_client import get_supabase_client, upload_image, create_signed_url
from app.core.security import get_current_user # Dependência para obter usuário logado

logger = logging.getLogger(__name__) # Adicionar logger

router = APIRouter()

@router.post(
    "/image", 
    response_model=UploadResponse, 
    status_code=201, # Código 201 para criação bem-sucedida
    summary="Upload de Imagem",
    description="Faz upload de um arquivo de imagem para o Supabase Storage e retorna o path."
)
async def upload_image_endpoint(
    file: UploadFile = File(..., description="Arquivo de imagem a ser enviado."),
    supabase: AsyncClient = Depends(get_supabase_client),
    current_user: Any = Depends(get_current_user) # Adicionar dependência de usuário
):
    """
    Endpoint para fazer upload de uma imagem. 
    Requer autenticação.
    """
    # Validação básica (será expandida na próxima tarefa)
    if not file.content_type or not file.content_type.startswith("image/"):
        logger.warning(f"Tentativa de upload de tipo de arquivo inválido: {file.content_type} por usuário {current_user.id}")
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo de arquivo inválido: {file.content_type}. Apenas imagens são permitidas."
        )
        
    # TODO: Adicionar validação de tamanho do arquivo na próxima tarefa.

    try:
        file_content = await file.read()
        
        # Verifica o tamanho após ler (exemplo: limite de 5MB)
        MAX_FILE_SIZE = 5 * 1024 * 1024 # 5 MB
        if len(file_content) > MAX_FILE_SIZE:
            logger.warning(f"Tentativa de upload de arquivo muito grande: {len(file_content)} bytes por usuário {current_user.id}")
            raise HTTPException(
                status_code=413, # Payload Too Large
                detail=f"Arquivo muito grande. O tamanho máximo permitido é {MAX_FILE_SIZE // 1024 // 1024}MB."
            )
        
        logger.info(f"Iniciando upload de '{file.filename}' ({file.content_type}, {len(file_content)} bytes) por usuário {current_user.id}...")
        
        image_path = await upload_image(
            supabase=supabase,
            file_content=file_content,
            file_name=file.filename or "unknown_image", # Usar nome padrão se não fornecido
            content_type=file.content_type,
            user_id=current_user.id # Passar o user_id para a função de upload
        )
        
        logger.info(f"Upload de '{file.filename}' concluído. Path: {image_path} por usuário {current_user.id}")
        return UploadResponse(image_path=image_path)

    except ValueError as ve:
        # Erro vindo da validação de tipo em upload_image
        logger.error(f"Erro de validação no upload por {current_user.id}: {ve}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException as http_exc:
        # Re-levantar exceções HTTP (como validação de tamanho)
        raise http_exc
    except Exception as e:
        # Erro genérico durante o upload
        logger.exception(f"Falha no upload da imagem '{file.filename}' por usuário {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor ao processar o upload: {e}")

# --- Novo Endpoint GET para URLs Assinadas --- 
@router.get(
    "/signed-url", 
    response_model=Dict[str, str], # Retorna um dicionário simples {"signed_url": "..."}
    summary="Obter URL Assinada para Imagem",
    description="Gera uma URL assinada de curta duração (1 minuto) para um arquivo de imagem no Supabase Storage, verificando a permissão do usuário."
)
async def get_signed_image_url(
    path: str, # Receber o path como query parameter
    supabase: AsyncClient = Depends(get_supabase_client),
    current_user: Any = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Gera uma URL assinada para um image_path específico, verificando a propriedade.
    """
    user_uuid = getattr(current_user, 'id', None)
    if not user_uuid:
        logger.error("ID do usuário (UUID) não encontrado no objeto User do Supabase retornado por get_current_user em /signed-url")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao obter ID do usuário autenticado.")
        
    # Validar o formato do path e extrair o user_id do path
    # Esperado: "user_uuid/nome_arquivo.ext"
    path_parts = path.split('/', 1)
    if len(path_parts) != 2 or not path_parts[0] or not path_parts[1]:
        logger.warning(f"Formato de path inválido solicitado '{path}' por usuário {user_uuid}")
        raise HTTPException(status_code=400, detail="Formato de caminho do arquivo inválido.")
        
    owner_uuid_from_path = path_parts[0]
    
    # Verificar se o UUID no path corresponde ao UUID do usuário logado
    if str(user_uuid) != owner_uuid_from_path:
        logger.warning(f"Usuário {user_uuid} tentou obter URL assinada para recurso de outro usuário: '{path}'")
        raise HTTPException(status_code=403, detail="Acesso não autorizado a este recurso.")
        
    try:
        logger.info(f"Gerando URL assinada para '{path}' (usuário {user_uuid}) com expiração de 60s...")
        signed_url_response = await create_signed_url(
            supabase=supabase,
            file_path=path,
            expires_in=60 # Expiração curta para carregamento no navegador
        )
        signed_url = signed_url_response.get("signedURL")
        
        if not signed_url:
            error_msg = signed_url_response.get('error', 'Erro desconhecido ao gerar URL')
            logger.error(f"Falha ao gerar URL assinada para '{path}' (usuário {user_uuid}): {error_msg}")
            raise HTTPException(status_code=500, detail="Falha ao gerar URL assinada.")
            
        logger.info(f"URL assinada gerada com sucesso para '{path}' (usuário {user_uuid})")
        return {"signed_url": signed_url}
        
    except HTTPException as http_exc:
        # Re-levantar exceções HTTP já tratadas (como 403)
        raise http_exc
    except Exception as e:
        logger.exception(f"Erro inesperado ao gerar URL assinada para '{path}' (usuário {user_uuid}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro interno ao gerar URL assinada: {e}") 