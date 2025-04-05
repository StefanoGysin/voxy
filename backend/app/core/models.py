from pydantic import BaseModel


class Token(BaseModel):
    """ Modelo Pydantic para a resposta do token JWT. """
    access_token: str
    token_type: str = "bearer" # Default para o tipo Bearer


class TokenData(BaseModel):
    """ Modelo Pydantic para os dados contidos no payload do token JWT. """
    username: str | None = None
    # Adicionar outros campos se necessário (ex: user_id, roles)

# Adicionar outros modelos Pydantic de Core se necessário. 