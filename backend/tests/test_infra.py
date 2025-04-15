import pytest
from supabase import AsyncClient

@pytest.mark.asyncio
async def test_supabase_connection(supabase_test_client: AsyncClient):
    """
    Testa se a fixture supabase_test_client fornece uma conexão funcional
    ao banco de dados Supabase de teste, acessando uma tabela no schema public.
    """
    assert supabase_test_client is not None
    # Tenta uma operação simples para confirmar a conexão.
    # Acessar a tabela "sessions" no schema "public" (padrão).
    try:
        response = await supabase_test_client.from_("sessions").select("id").limit(1).execute()
        # Não verificamos os dados, apenas que a chamada não gerou erro.
        assert response is not None
        print("\nConexão com Supabase de teste (schema public) verificada com sucesso.")
    except Exception as e:
        pytest.fail(f"Erro ao conectar ou executar query na tabela 'sessions' (public) do Supabase de teste: {e}")

# TODO: Adicionar um teste para verificar a fixture de limpeza 'cleanup_test_data'
#       (talvez inserindo dados em 'sessions' ou 'messages' e verificando se são removidos). 