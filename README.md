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

### Configuração do Backend

1.  Clone o repositório.
2.  Navegue até a pasta `backend`.
3.  Crie e ative um ambiente virtual Python.
4.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```
    *Nota: `requirements.txt` inclui `passlib==1.7.4` e `bcrypt==3.2.0` fixos por questões de compatibilidade.*
5.  Crie um arquivo `.env` a partir de `backend/.env.example`.
6.  **Edite o arquivo `.env` e preencha TODAS as variáveis:**
    *   `OPENAI_API_KEY`: Sua chave OpenAI.
    *   `OPENWEATHERMAP_API_KEY`: Sua chave OpenWeatherMap.
    *   `SUPABASE_CONNECTION_STRING`: A **Connection String** do seu banco de dados Supabase (formato `postgresql://postgres:[YOUR-PASSWORD]@[AWS-REGION].pooler.supabase.com:6543/postgres?pgbouncer=true`). Você encontra na seção Database -> Settings -> Connection string do seu projeto Supabase.
    *   `SECRET_KEY`: Uma string longa e aleatória para assinar os tokens JWT (ex: gerada com `openssl rand -hex 32`).
    *   `ALGORITHM`: O algoritmo JWT (geralmente `HS256`).
    *   `ACCESS_TOKEN_EXPIRE_MINUTES`: Tempo de expiração do token em minutos (ex: `30`).
7.  Execute o servidor de desenvolvimento:
    ```bash
    uvicorn app.main:app --reload
    ```
    O backend estará disponível em `http://localhost:8000`.

### Configuração do Frontend

1.  Navegue até a pasta `frontend`.
2.  Instale as dependências:
    ```bash
    npm install
    ```
3.  (Opcional) Crie um arquivo `.env` em `frontend/` se precisar sobrescrever a URL da API padrão (`http://localhost:8000/api`). Veja `frontend/.env.example`.
4.  Execute o servidor de desenvolvimento:
    ```bash
    npm run dev
    ```
    O frontend estará disponível em um endereço como `http://localhost:5173` (verifique a saída do terminal).

## Uso

1.  Acesse o frontend no seu navegador.
2.  Você será redirecionado para a página de Login.
3.  **Registre uma nova conta** ou faça login com uma conta existente.
4.  Após o login, você será direcionado para a interface de chat.
5.  Converse com Voxy! Tente pedir para ele:
    *   Lembrar de algo: "Lembre-se que minha cor favorita é roxo."
    *   Verificar o clima: "Qual o tempo em Londres?"
    *   Perguntar sobre o que ele lembra: "Qual minha cor favorita?"

## Executando os Testes (Backend)

1.  Certifique-se de estar na pasta `backend` com o ambiente virtual ativado.
2.  Execute o Pytest:
    ```bash
    python -m pytest
    ```
    *Nota: Alguns testes podem depender de variáveis de ambiente configuradas (ex: para `mem0`). Pode ser necessário configurar um DB de teste ou usar mocks mais extensos.*

## Estrutura do Projeto

```
voxy/
├── backend/
│   ├── app/
│   │   ├── agents/       # Agente Brain, Ferramentas (clima, memória)
│   │   ├── api/          # Endpoints (chat, auth)
│   │   ├── core/         # Configuração, Segurança (JWT)
│   │   ├── db/           # Modelos (User), Sessão DB
│   │   ├── memory/       # Gerenciador Mem0
│   │   └── main.py       # App FastAPI
│   ├── tests/            # Testes Pytest
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/   # UI (Chat, Auth, Layout)
│   │   ├── contexts/     # AuthContext
│   │   ├── hooks/
│   │   ├── lib/          # Utilitários (shadcn)
│   │   ├── pages/        # Páginas (Login, Register, ChatPage)
│   │   ├── services/     # api.js (fetch)
│   │   └── App.jsx       # Roteamento Principal
│   ├── .env.example
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── memory-bank/          # Documentação interna para IA
├── docs/                 # Documentação geral (arquitetura, etc.)
├── .gitignore
└── README.md
```

## Contribuindo

Consulte `PLANNING.md` e `TASK.md` na pasta `docs` e os arquivos no `memory-bank`.

## Licença

[MIT](LICENSE) 