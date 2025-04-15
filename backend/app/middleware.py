from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp
import logging
from supabase import AsyncClient, AuthApiError
from .db.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

# Rotas que não exigem autenticação
PUBLIC_PATHS = [
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/auth/token",
    "/api/auth/register",
    "/public",
    "/",
    "/health"
]

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        
        # --- Adicionado: Ignorar requisições OPTIONS (usadas pelo CORS preflight) ---
        if request.method == "OPTIONS":
            logger.debug(f"Requisição OPTIONS para {request.url.path}, pulando AuthMiddleware.")
            response = await call_next(request) # Deixa o CORSMiddleware tratar
            return response
        # --- Fim da adição ---

        # Verificar se a rota é pública - usando verificação exata em vez de startswith
        path = request.url.path
        
        # Verificar correspondência exata com as rotas públicas
        if path in PUBLIC_PATHS or path.startswith("/docs/") or path.startswith("/redoc/"):
            logger.debug(f"Rota pública acessada: {path}, pulando autenticação.")
            response = await call_next(request)
            return response

        # Tentar extrair o token Bearer
        auth_header = request.headers.get("Authorization")
        token = None
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]

        if not token:
            logger.warning(f"Token de autenticação ausente para rota protegida: {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Not authenticated"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Tentar validar o token com Supabase
        try:
            logger.debug(f"Validando token para: {request.url.path}")
            # Obter cliente Supabase sob demanda
            supabase = get_supabase_client()
            user_response = await supabase.auth.get_user(token)
            
            if user_response.user:
                # Anexar usuário ao estado da requisição para uso posterior nas rotas
                request.state.user = user_response.user 
                logger.info(f"Token válido. Usuário {user_response.user.id} autenticado para: {request.url.path}")
                response = await call_next(request)
                return response
            else:
                # Token pode ser inválido ou expirado, mas get_user não levantou exceção
                logger.warning(f"Falha na validação do token (usuário não retornado) para: {request.url.path}")
                raise AuthApiError("Token inválido ou expirado.", status=401, code="invalid_token")

        except AuthApiError as e:
            logger.warning(f"Erro de autenticação Supabase ({e.status if hasattr(e, 'status') else 'N/A'}): {e.message if hasattr(e, 'message') else str(e)} para rota: {request.url.path}")
            return JSONResponse(
                status_code=401, # Usar 401 explicitamente
                content={"detail": "Could not validate credentials"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.exception(f"Erro inesperado durante validação de token para {request.url.path}: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error during authentication"},
            )

# Remover ou comentar ExampleMiddleware se não for mais necessário
# class ExampleMiddleware(BaseHTTPMiddleware):
#     async def dispatch(
#         self, request: Request, call_next: RequestResponseEndpoint
#     ) -> Response:
#         # Lógica do middleware antes da requisição ser processada
#         logger.info(f"Middleware: Recebendo requisição para {request.url.path}")

#         # Processa a requisição
#         response = await call_next(request)

#         # Lógica do middleware após a requisição ser processada
#         logger.info(f"Middleware: Retornando resposta com status {response.status_code}")

#         return response

# Adicione outras classes de middleware aqui conforme necessário 