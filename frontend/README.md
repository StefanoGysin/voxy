# Frontend Voxy (React + Vite)

Este diretório contém o frontend da aplicação Voxy, construído com React, Vite, Tailwind CSS e shadcn/ui.

## Funcionalidades

*   Interface de chat interativa.
*   Comunicação em tempo real (básica) com o backend via Supabase Realtime.
*   Gerenciamento de sessões de chat (listagem, seleção, criação).
*   Autenticação de usuários (Registro e Login) via API do backend.
*   Gerenciamento de estado local (Auth, Chat) usando React Context API.
*   Persistência do token de autenticação via `localStorage`.

## Tecnologias Principais

*   React (~18/19)
*   Vite
*   JavaScript (JSX)
*   Tailwind CSS
*   shadcn/ui (Biblioteca de componentes)
*   `lucide-react` (Ícones)
*   `react-router-dom` (Roteamento)
*   React Context API (Gerenciamento de estado)
*   Fetch API (Comunicação HTTP)
*   `@supabase/supabase-js` (Cliente Supabase para Realtime)
*   `date-fns` (Formatação de datas)

## Configuração

1.  **Pré-requisitos:** Certifique-se de ter Node.js (versão ~20.x ou compatível) e npm/yarn instalados.

2.  **Dependências:** Navegue até o diretório `frontend/` e instale as dependências:
    ```bash
    npm install
    # ou
    yarn install
    ```

3.  **Variáveis de Ambiente:** Copie o arquivo `.env.example` para `.env` na raiz do diretório `frontend/` e preencha as variáveis necessárias:
    *   `VITE_API_BASE_URL`: URL base da sua API backend FastAPI (ex: `http://localhost:8000`).
    *   `VITE_SUPABASE_URL`: URL do seu projeto Supabase.
    *   `VITE_SUPABASE_ANON_KEY`: Chave pública (anon) do seu projeto Supabase (usada para conexão Realtime).

## Execução

*   **Servidor de Desenvolvimento:**
    Execute o seguinte comando na raiz do diretório `frontend/`:
    ```bash
    npm run dev
    # ou
    yarn dev
    ```
    A aplicação estará disponível geralmente em `http://localhost:5173`.

## Estrutura

Consulte o `PLANNING.md` na raiz do projeto para uma visão detalhada da arquitetura e estrutura de diretórios do frontend.

## Mais Informações

Consulte o [README Principal](../../README.md) para informações gerais sobre o projeto Voxy.
