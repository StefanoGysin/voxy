# Tech Stack e Configuração do Ambiente Voxy

Este documento detalha as tecnologias usadas no projeto Voxy e como configurar o ambiente de desenvolvimento.

## 1. Tecnologias Principais

### Backend

*   **Linguagem:** Python (v3.12.8)
*   **Framework Web:** FastAPI (>=1.0)
*   **Servidor ASGI:** Uvicorn (>=0.22.0)
*   **SDK de Agentes:** OpenAI Agents SDK (>=0.0.7)
*   **Validação/Configuração:** SQLModel (>=0.0.14), Pydantic (via SQLModel), `pydantic-settings`
*   **ORM:** SQLModel (>=0.0.14) / SQLAlchemy (via SQLModel)
*   **Banco de Dados (Usuários):** PostgreSQL (via Supabase ou outro)
*   **Vector Store (Memória):** Supabase (PostgreSQL + pgvector)
*   **Driver DB:** `psycopg2-binary`
*   **SDK de Memória:** `mem0ai`
*   **Autenticação:**
    *   Hashing: `passlib[bcrypt]==1.7.4` (com `bcrypt==3.2.0`)
    *   JWT: `python-jose[cryptography]` (>=3.3.0)
*   **Testes:** Pytest (>=7.3.1) com `pytest-asyncio`
*   **Cliente HTTP Async:** `httpx` (>=0.24.0)
*   **Formatação:** Black

### Frontend

*   **Biblioteca UI:** React (>=18.0.0)
*   **Build Tool:** Vite
*   **Linguagem:** JavaScript (JSX)
*   **Roteamento:** `react-router-dom`
*   **Gerenciamento de Estado (Auth):** React Context API (`AuthContext`), `localStorage`
*   **Estilização:** Tailwind CSS (>=3.3.0)
*   **Biblioteca de Componentes:** shadcn/ui
*   **Ícones:** Lucide React
*   **Formatação:** Prettier / ESLint

### Geral

*   **Versionamento:** Git

## 2. Configuração do Ambiente de Desenvolvimento

Consulte o [README.md](../README.md) principal para obter os passos detalhados de instalação e execução.

**Resumo dos Requisitos:**

*   **Python:** v3.12.8
*   **Node.js:** ~20.x (ex: v20.14.0)
*   **Gerenciadores de Pacotes:** `pip` (Python), `npm` (Node.js)
*   **Ambiente Virtual (Python):** Requerido (`venv`).
*   **Banco de Dados:** Acesso a uma instância PostgreSQL (ex: Supabase) com a extensão `vector` habilitada.
*   **Variáveis de Ambiente:**
    *   **Backend (`backend/.env`):**
        *   `OPENAI_API_KEY`: Obrigatória.
        *   `OPENWEATHERMAP_API_KEY`: Obrigatória.
        *   `SUPABASE_CONNECTION_STRING`: Obrigatória (URL de conexão do Postgres/Supabase).
        *   `SECRET_KEY`: Obrigatória (para assinatura JWT).
        *   `ALGORITHM`: Obrigatória (ex: "HS256").
        *   `ACCESS_TOKEN_EXPIRE_MINUTES`: Obrigatória (ex: 30).
    *   **Frontend (`frontend/.env`):**
        *   `VITE_API_URL`: (Opcional) Padrão `http://localhost:8000/api`.
*   **Arquivos de Exemplo:** `.env.example` disponíveis.

## 3. Restrições Técnicas Importantes

*   **Assincronicidade no Backend:** Crucial usar `async def` para endpoints e ferramentas. `Runner.run()` para agentes. Usar `asyncio.to_thread` para chamadas síncronas como `mem0ai` dentro de código async.
*   **Versões `passlib`/`bcrypt`:** Fixadas em `1.7.4`/`3.2.0` por compatibilidade.
*   **CORS:** Configuração adequada no FastAPI é necessária.
*   **Contexto de Usuário para Memória:** O `user_id` é passado para `mem0ai` via `contextvars`, o que exige que as rotas que usam memória estejam protegidas por autenticação. 