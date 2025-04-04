# Tech Stack e Configuração do Ambiente Voxy

Este documento detalha as tecnologias usadas no projeto Voxy e como configurar o ambiente de desenvolvimento.

## 1. Tecnologias Principais

### Backend

*   **Linguagem:** Python (v3.12.8)
*   **Framework Web:** FastAPI (>=1.0)
*   **Servidor ASGI:** Uvicorn (>=0.22.0)
*   **SDK de Agentes:** OpenAI Agents SDK (>=0.0.7)
*   **Validação/Configuração:** Pydantic (>=2.0.0) / `pydantic-settings`
*   **Testes:** Pytest (>=7.3.1) com `pytest-asyncio`
*   **Cliente HTTP Async:** `httpx` (>=0.24.0)
*   **Formatação:** Black

### Frontend

*   **Biblioteca UI:** React (>=18.0.0)
*   **Build Tool:** Vite
*   **Linguagem:** JavaScript (JSX)
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
*   **Ambiente Virtual (Python):** Requer um ambiente virtual (ex: `venv`) para isolar dependências do backend.
*   **Variáveis de Ambiente:**
    *   **Backend (`backend/.env`):**
        *   `OPENAI_API_KEY`: Obrigatória (OpenAI).
        *   `OPENWEATHERMAP_API_KEY`: Obrigatória (OpenWeatherMap).
        *   `SECRET_KEY`: Para segurança JWT (opcional para dev, mas recomendado).
        *   `DEBUG`: (Opcional) Definir como `True` para habilitar logs de depuração.
    *   **Frontend (`frontend/.env`):**
        *   `VITE_API_URL`: (Opcional) Define a URL do backend se diferente do padrão `http://localhost:8000/api`.
*   **Arquivos de Exemplo:** Os arquivos `.env.example` nos diretórios `backend/` e `frontend/` servem como templates.

## 3. Restrições Técnicas Importantes

*   **Assincronicidade no Backend:** Devido ao uso de FastAPI e OpenAI Agents SDK, é crucial usar `async def` para endpoints e ferramentas que realizam operações de I/O. O `Runner.run()` do SDK deve ser usado para executar agentes de forma assíncrona.
*   **CORS:** O backend FastAPI precisa ter a configuração de CORS (Cross-Origin Resource Sharing) adequada para aceitar requisições do servidor de desenvolvimento do frontend. 