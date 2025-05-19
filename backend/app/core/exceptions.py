"""Classes de exceção personalizadas para a aplicação Voxy."""

import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class BaseAppError(Exception):
    """Erro base para todas as exceções da aplicação"""
    pass


class DatabaseError(BaseAppError):
    """Erros relacionados às operações do Supabase/banco de dados"""
    pass


class ExternalServiceError(BaseAppError):
    """Erros de serviços externos (ex.: APIs)"""
    pass


class ImageAnalysisError(BaseAppError):
    """Erros relacionados à análise de imagens pelo VisioScan"""
    pass


@asynccontextmanager
async def error_boundary(operation_name: str, fallback_value=None):
    """Gerenciador de contexto assíncrono para tratar e registrar erros específicos da aplicação."""
    try:
        yield
    except DatabaseError as e:
        logger.error(f"Erro de banco de dados durante {operation_name}: {str(e)}", exc_info=True)
        if fallback_value is not None:
            # Se um valor de fallback for fornecido, retorne-o em vez de levantar a exceção
            # Isso é útil para operações não críticas
            # O gerenciador de contexto precisa retornar o valor, o que não é padrão
            # Um padrão diferente pode ser melhor se fallbacks forem comuns
            # Por enquanto, nos concentramos principalmente em registrar e re-levantar
            pass # Ou tratar de forma diferente se fallback for necessário
        raise # Re-levanta a exceção capturada
    except ExternalServiceError as e:
        logger.warning(f"Erro de serviço externo durante {operation_name}: {str(e)}")
        if fallback_value is not None:
            pass
        raise # Re-levanta a exceção capturada
    except Exception as e:
        # Captura quaisquer outras exceções inesperadas
        logger.critical(f"Erro não tratado durante {operation_name}: {str(e)}", exc_info=True)
        raise # Re-levanta a exceção original