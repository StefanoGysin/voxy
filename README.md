# Voxy - Agente Inteligente com Memória e Autenticação

Voxy é um sistema baseado em agentes inteligentes construído com o OpenAI Agents SDK. O sistema consiste em um backend Python com FastAPI e um frontend React (usando **Vite**) com Tailwind CSS. Ele agora suporta **autenticação de usuários** e **memória personalizada e persistente** por usuário utilizando `mem0ai` e Supabase.

## Visão Geral

O projeto Voxy utiliza o OpenAI Agents SDK para criar um assistente inteligente capaz de:

*   Conversar com usuários de forma natural.
*   Utilizar ferramentas para obter informações externas (ex: clima com OpenWeatherMap).
*   **Autenticar usuários** (registro e login via JWT).
*   **Memorizar e recordar informações específicas de cada usuário** através de interações, utilizando `mem0ai` com um backend Supabase (PostgreSQL + pgvector).
*   **Adaptar suas respostas** com base no histórico de memória do usuário logado.

### Arquitetura

- **Backend**: API FastAPI em Python que gerencia o agente `brain` (OpenAI SDK), ferramentas (`get_weather`, `remember_info`, `recall_info`), autenticação JWT (`python-jose`, `passlib`) e a interface com a memória `mem0ai`.
- **Frontend**: Interface de usuário em React (Vite) com Tailwind CSS e shadcn/ui, incluindo fluxo de autenticação (Login/Registro) e a interface de chat principal.

## Funcionalidades Implementadas

*   Chat básico com o agente.
*   Uso da ferramenta `get_weather` (requer chave OpenWeatherMap).
*   Registro de novos usuários.
*   Login de usuários existentes (recebendo um token JWT).
*   Proteção do endpoint de chat (`/api/chat`) - requer token JWT válido.
*   Memorização de informações (`remember_info`) vinculadas ao usuário autenticado.
*   Recuperação de informações (`recall_info`) da memória do usuário autenticado.
*   Uso proativo da memória pelo agente para contextualizar respostas.

## Primeiros Passos

### Pré-requisitos

- Python 3.12.8
- Node.js ~20.x (v20.14.0 ou compatível)
- **Conta Supabase:** Um projeto Supabase com a extensão `vector` habilitada (para memória `mem0ai` e banco de dados de usuários).
- Chave de API da OpenAI
- Chave de API do OpenWeatherMap

## Backend

O backend é construído com FastAPI e Python. Ele fornece a API para o frontend, gerencia o agente inteligente, a autenticação e a memória.

➡️ **Consulte o [README do Backend](./backend/README.md) para instruções detalhadas de configuração e execução.**

**⚠️ Nota Importante sobre Dependências:** O backend requer versões específicas de `passlib` (1.7.4) e `bcrypt` (3.2.0). Consulte o README do backend para mais detalhes.

## Frontend

1.  Navegue até a pasta `