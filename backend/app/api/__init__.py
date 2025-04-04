"""
Pacote api do Voxy.

Este pacote contém os endpoints da API REST do Voxy.
"""

from .chat import router as chat_router

__all__ = ['chat_router'] 