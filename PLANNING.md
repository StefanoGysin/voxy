# Projeto Voxy - Plano de Implementação

## Visão Geral

Voxy é um sistema de agentes inteligentes baseado no OpenAI Agents SDK, composto por um backend Python com FastAPI e um frontend em React com Tailwind CSS (usando Vite). O sistema permite interação com um agente principal (`brain`) que pode coordenar ferramentas, suporta autenticação de usuários e memória persistente por usuário via `mem0ai` e Supabase.

**Nota Importante sobre Integração:** Ao usar o OpenAI Agents SDK com frameworks assíncronos como FastAPI, é crucial utilizar a execução assíncrona do agente (por exemplo, `Runner.run()`) em vez de métodos síncronos (`Runner.run_sync()`) dentro dos endpoints `async def` para evitar conflitos com o loop de eventos `asyncio`.

## Arquitetura

### Componentes Principais

```
voxy/
├── backend/
│   ├── app/
│   │   ├── api/         # Endpoints FastAPI (chat, auth)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   └── routes.py
│   │   ├── agents/      # Lógica do Agente e Ferramentas
│   │   │   ├── __init__.py
│   │   │   ├── brain.py       # Agente principal (com instruções proativas)
│   │   │   ├── tools/         # Ferramentas (weather, memory)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── memory_tools.py
│   │   │   │   └── weather.py
│   │   │   └── utils.py
│   │   ├── core/        # Configurações, Segurança (JWT, hash)
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── db/          # Banco de Dados (Modelos, Sessão)
│   │   │   ├── __init__.py
│   │   │   ├── models.py      # Modelo User (SQLModel)
│   │   │   └── session.py
│   │   ├── memory/      # Gerenciador de Memória (mem0ai)
│   │   │   ├── __init__.py
│   │   │   └── mem0_manager.py
│   │   ├── __init__.py
│   │   └── main.py        # Aplicação FastAPI principal
│   ├── tests/             # Testes Pytest
│   │   ├── __init__.py
│   │   ├── test_agents/
│   │   │   ├── __init__.py
│   │   │   ├── test_brain.py
│   │   │   └── test_tools/
│   │   │       ├── __init__.py
│   │   │       ├── test_memory_tools.py
│   │   │       └── test_weather.py
│   │   └── test_api/      # Testes para endpoints (chat, auth - a criar)
│   ├── .env.example       # Exemplo de variáveis de ambiente
│   ├── requirements.txt   # Dependências Python atualizadas
│   └── README.md          # README específico do Backend (pode ser criado)
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/    # UI (Chat, Auth, Layout, shadcn)
│   │   │   ├── Auth/
│   │   │   │   ├── LoginForm.jsx
│   │   │   │   └── RegisterForm.jsx
│   │   │   ├── Chat/
│   │   │   │   ├── ChatBox.jsx
│   │   │   │   ├── ChatInput.jsx
│   │   │   │   ├── ChatMessage.jsx
│   │   │   │   └── index.jsx
│   │   │   ├── Layout/
│   │   │   ├── UI/           # Componentes base shadcn/ui
│   │   │   └── index.js
│   │   ├── contexts/      # AuthContext
│   │   ├── hooks/
│   │   ├── lib/           # Utilitários (cn)
│   │   ├── pages/         # Páginas (ChatPage, LoginPage, RegisterPage)
│   │   ├── services/      # api.js (fetch)
│   │   ├── styles/        # CSS Global
│   │   │   └── globals.css
│   │   ├── utils/
│   │   ├── App.jsx        # Roteamento principal
│   │   └── index.jsx
│   ├── .env.example
│   ├── package.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── README.md          # README específico do Frontend (pode ser criado)
├── docs/
│   ├── PLANNING.md
│   ├── TASK.md
│   ├── architecture.md    # Documentos atualizados
│   ├── goals.md
│   ├── tech_stack.md
│   └── ...
├── memory-bank/           # Banco de memória para IA (atualizado)
├── .gitignore
└── README.md              # README Principal (atualizado)
```

## Backend

### Tecnologias

- **Python**: Linguagem principal
- **FastAPI**: Framework para API REST
- **OpenAI Agents SDK**: Para criação dos agentes inteligentes
- **SQLModel**: ORM e validação de dados (inclui Pydantic, SQLAlchemy)
- **`mem0ai`**: SDK para memória de longo prazo
- **`pydantic-settings`**: Carregamento de configuração (.env)
- **`passlib[bcrypt]`**: Hashing de senha (**Nota:** Fixado em `passlib==1.7.4` devido a compatibilidade com `bcrypt`)
- **`bcrypt`**: Dependência de hash (**Nota:** Fixado em `bcrypt==3.2.0`)
- **`python-jose[cryptography]`**: Manipulação de JWT
- **`psycopg2-binary`**: Driver PostgreSQL
- **Pytest**: Para testes unitários
- **`pytest-asyncio`**: Suporte async em testes
- **`httpx`**: Cliente HTTP assíncrono

### Componentes do Backend

#### 1. Módulo de Agentes (`agents/`)

- **`brain.py`**: Agente principal com instruções atualizadas (proatividade na memória).
- **`tools/`**: Contém as ferramentas:
    - `weather.py` (`get_weather`)
    - `memory_tools.py` (`remember_info`, `recall_info` com docstrings atualizadas).

#### 1.1. Módulo de Ferramentas (`agents/tools`)

- **weather.py**: Contém a implementação da ferramenta `get_weather`.
  - Usa o decorator `@function_tool` para registrar a função como uma ferramenta para o agente.

```python
# backend/app/agents/tools/weather.py
from agents import function_tool

@function_tool
def get_weather(city: str) -> str:
    """
    Obtém a previsão do tempo atual para uma cidade específica.
    
    Args:
        city (str): O nome da cidade (e opcionalmente estado/país) para 
                    obter a previsão do tempo.
    Returns:
        str: Uma string descrevendo o tempo na cidade especificada.
    """
    # Implementação inicial: Retorna um valor fixo
    # TODO: Implementar chamada a uma API de clima real (ex: OpenWeatherMap)
    return f"O tempo em {city} está ensolarado."
```

#### 2. Módulo de API

- **chat.py**: Endpoints para comunicação com o agente (protegido por autenticação).
- **auth.py**: Endpoints para registro (`/register`, requer `username`, `email`, `password`) e login (`/token`, usa `email` como `username` no form).

#### 2.1 Autenticação e Banco de Dados (Correções e Detalhes)

- **Retorno `/register`:** A rota `/register` retorna o schema `UserRead` (`id`, `username`, `email`).
- **Gerenciamento de Sessão (`get_db`):** A dependência `get_db` original foi corrigida (commit explícito), mas nos testes, ela é substituída por uma fixture (`conftest.py::session`) que gerencia uma sessão isolada por teste com criação/rollback/drop de tabelas.
- **Criação de Tabelas:** As tabelas do banco de dados (`user`) são criadas/removidas automaticamente pelos testes via fixture. Em produção, a criação ocorre via `SQLModel.metadata.create_all(engine)` em `main.py`.

#### 3. Módulo de Core

- **config.py**: Configurações do aplicativo
- **security.py**: Funcionalidades de segurança (se necessário)
- **Hashing de Senha:** `passlib` com `bcrypt` (**Atenção:** Versões `passlib==1.7.4` e `bcrypt==3.2.0` devem ser usadas devido a problemas de compatibilidade reportados com versões mais recentes).
- **Dependências:** Manter atualizadas, **exceto** `passlib` e `bcrypt` que devem permanecer nas versões especificadas até que a compatibilidade seja confirmada.
- **Limitação de Taxa:** Considerar adicionar à API.

#### 4. Módulo de Banco de Dados (opcional)

- **models.py**: Modelos de dados para persistência de mensagens e histórico

## Frontend

### Tecnologias

- **React**: Biblioteca para UI
- **Vite**: Ferramenta de build e servidor de desenvolvimento
- **Tailwind CSS**: Framework CSS
- **shadcn/ui**: Biblioteca de componentes UI
- **`lucide-react`**: Ícones
- **`react-router-dom`**: Roteamento
- **React Context API**: Para gerenciamento de estado (ex: `AuthContext`)
- **`localStorage`**: Para persistência do token JWT
- **Fetch API**: Cliente HTTP

### Componentes do Frontend

#### 1. Chat UI

- **ChatBox**: Gerencia o estado das mensagens, usa `ScrollArea` de `shadcn/ui`.
- **ChatInput**: Usa `Input` e `Button` de `shadcn/ui` com ícones.
- **ChatMessage**: Estilização aprimorada para diferenciar papéis.

```jsx
// Exemplo Conceitual (ChatInput.jsx refatorado com shadcn/ui e lucide-react)
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, Paperclip } from "lucide-react"; // Exemplo de ícones

const ChatInput = ({ onSendMessage, disabled }) => {
  // ... (state para input) ...

  const handleSend = () => { /* ... */ };
  const handleAttach = () => { /* ... */ }; 

  return (
    <div className="relative flex items-center p-4 border-t">
      <Button variant="ghost" size="icon" className="absolute left-6">
        <Paperclip className="h-4 w-4" />
      </Button>
      <Input 
        placeholder="Digite sua mensagem..." 
        className="flex-1 pl-12 pr-12" 
        // ... (value, onChange, onKeyDown) ...
        disabled={disabled}
      />
      <Button variant="ghost" size="icon" className="absolute right-6" onClick={handleSend} disabled={disabled || !message.trim()}>
        <Send className="h-4 w-4" />
      </Button>
    </div>
  );
};
```

#### 2. Serviços

- **api.js**: Funções para comunicação com o backend

```javascript
// api.js usando Fetch API e variáveis de ambiente Vite

// No Vite, variáveis devem começar com VITE_ e são acessadas via import.meta.env
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const sendMessage = async (content) => {
  try {
    const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content }),
    });
    
    if (!response.ok) {
        let errorDetail = 'Erro desconhecido ao enviar mensagem';
        try {
          const errorData = await response.json();
          errorDetail = errorData.detail || `HTTP error! status: ${response.status}`;
        } catch(e) { /* Ignora erro no JSON */ errorDetail = `HTTP error! status: ${response.status}`}
        throw new Error(errorDetail);
    }
    
    const data = await response.json();
    return data.response; 
  } catch (error) {
      console.error('Erro na API (sendMessage):', error);
      throw error;
  }
};

// ... (getChatHistory, etc. se existir)
```

## Plano de Implementação

*As fases concluídas foram removidas para brevidade. O estado atual reflete a conclusão da Fase 9.*

**Próximos Passos (Pós-Refatoração `username`):**

1.  **Refinamento e Testes (Backend):**
    *   [ ] Considerar uso de Alembic para futuras migrações de banco de dados.
    *   [ ] Configurar e usar um banco de dados de teste dedicado (ver `TASK.md`).
    *   [ ] Revisar e potencialmente adicionar mais casos de teste para autenticação e agente.
2.  **Documentação:**
    *   [ ] Revisar `PLANNING.md` e `backend/README.md` para garantir consistência final.
    *   [ ] Atualizar outros `docs/*` se necessário.
3.  **Melhorias (Opcional / Futuro):**
    *   [ ] Frontend: Validação de formulário mais robusta.
    *   [ ] Frontend: Melhor feedback visual (loading, success, error).
    *   [ ] Backend/Frontend: Implementar refresh tokens para segurança JWT aprimorada.
    *   [ ] Explorar Handoffs, MCP, Guardrails do OpenAI SDK.
    *   [ ] Refatorar lógica DB para camada `crud`.

## Considerações de Segurança

- **Variáveis de Ambiente:** Manter `.env` seguro e NUNCA comitar `SECRET_KEY`, chaves de API, ou connection strings no Git.
- **Validação de Entrada:** Usar Pydantic/SQLModel rigorosamente.
- **Autenticação:** JWT implementado, considerar refresh tokens.
- **Hashing de Senha:** `passlib` com `bcrypt`.
- **Dependências:** Manter atualizadas (com atenção a versões fixadas como `passlib`/`bcrypt`).
- **Limitação de Taxa:** Considerar adicionar à API.

## Teste e Qualidade de Código

- **Testes Unitários/Integração (Backend):** Usar `pytest` e `pytest-asyncio`. A configuração de teste (`conftest.py`) agora inclui uma fixture `session` que gerencia o ciclo de vida do banco de dados (create/drop/rollback) para cada teste, garantindo isolamento. Testes de API usam `httpx.AsyncClient` com `ASGITransport`.

## Tecnologias e Dependências

*Refere-se ao `backend/requirements.txt` e `frontend/package.json` atualizados.*
