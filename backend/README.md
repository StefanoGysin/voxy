# Backend Voxy

Este diretório contém o backend da aplicação Voxy, construído com FastAPI e Python.

## Funcionalidades

*   API RESTful para interação com o agente inteligente.
*   Agente principal (`brain`) com ferramentas para clima e memória.
*   Sistema de autenticação de usuários via JWT.
*   Memória persistente por usuário utilizando `mem0ai` e Supabase.
*   Testes unitários e de integração com `pytest`.

## Configuração

1.  **Ambiente Virtual:** Certifique-se de ter um ambiente virtual Python ativado.
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # ou
    .\venv\Scripts\activate    # Windows
    ```
2.  **Dependências:** Instale as dependências listadas em `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```
    **⚠️ IMPORTANTE:** Este projeto utiliza versões específicas de `passlib` (1.7.4) e `bcrypt` (3.2.0) devido a problemas de compatibilidade conhecidos. Certifique-se de que estas versões estão instaladas e não as atualize inadvertidamente, a menos que a compatibilidade com versões mais recentes seja confirmada.

3.  **Variáveis de Ambiente:** Copie o arquivo `.env.example` para `.env` e preencha as variáveis necessárias:
    *   `SECRET_KEY`: Chave secreta para JWT (gere uma chave segura).
    *   `ALGORITHM`: Algoritmo JWT (ex: HS256).
    *   `ACCESS_TOKEN_EXPIRE_MINUTES`: Tempo de expiração do token.
    *   `DATABASE_URL`: Connection string do seu banco de dados PostgreSQL (ex: Supabase).
    *   `MEM0_API_KEY`: Sua chave de API do `mem0.ai`.
    *   `OPENAI_API_KEY`: Sua chave de API da OpenAI (para o agente).
    *   `OPENWEATHERMAP_API_KEY`: Sua chave de API do OpenWeatherMap (para a ferramenta de clima).

## Execução

*   **Servidor de Desenvolvimento:**
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
*   **Testes:**
    Execute os testes a partir do diretório raiz do projeto (`voxy/`) para garantir que os paths sejam resolvidos corretamente:
    ```bash
    python -m pytest backend
    ```

## Estrutura

Consulte o `PLANNING.md` na raiz do projeto para uma visão detalhada da arquitetura e estrutura de diretórios. 