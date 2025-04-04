# Projeto Voxy - Plano de Implementação

## Visão Geral

Voxy é um sistema de agentes inteligentes baseado no OpenAI Agents SDK, composto por um backend Python com FastAPI e um frontend em React com Tailwind CSS. O sistema permitirá a interação com um agente principal (brain) que poderá coordenar outros agentes especializados no futuro.

**Nota Importante sobre Integração:** Ao usar o OpenAI Agents SDK com frameworks assíncronos como FastAPI, é crucial utilizar a execução assíncrona do agente (por exemplo, `Runner.run()`) em vez de métodos síncronos (`Runner.run_sync()`) dentro dos endpoints `async def` para evitar conflitos com o loop de eventos `asyncio`.

## Arquitetura

### Componentes Principais

```
voxy/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   └── routes.py
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── brain.py        # Agente principal
│   │   │   ├── tools/          # Ferramentas para os agentes
│   │   │   │   ├── __init__.py
│   │   │   │   └── weather.py  # Exemplo: ferramenta de clima
│   │   │   └── utils.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   └── models.py
│   │   ├── __init__.py
│   │   └── main.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_agents/
│   │   │   ├── __init__.py
│   │   │   ├── test_brain.py
│   │   │   └── test_tools/     # Testes para as ferramentas
│   │   │       ├── __init__.py
│   │   │       └── test_weather.py
│   │   └── test_api/
│   ├── .env.example
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/         # Componentes específicos do Chat (Refatorados)
│   │   │   │   ├── ChatBox.jsx
│   │   │   │   ├── ChatInput.jsx
│   │   │   │   ├── ChatMessage.jsx
│   │   │   │   └── index.jsx
│   │   │   ├── Layout/       # Componentes de layout (Header, Footer, etc.)
│   │   │   ├── UI/           # Componentes de UI reutilizáveis (shadcn/ui ou custom)
│   │   │   └── index.js
│   │   ├── contexts/
│   │   ├── hooks/
│   │   ├── lib/            # Utilitários (ex: cn para Tailwind)
│   │   │   └── utils.js
│   │   ├── pages/
│   │   ├── services/
│   │   ├── styles/         # Arquivos CSS/Globais
│   │   │   └── globals.css
│   │   ├── utils/
│   │   ├── App.jsx
│   │   └── index.jsx
│   ├── .env.example
│   ├── package.json
│   ├── tailwind.config.js # Configuração do Tailwind
│   ├── postcss.config.js  # Configuração do PostCSS
│   └── README.md
├── docs/
│   ├── PLANNING.md
│   └── TASK.md
├── .gitignore
└── README.md
```

## Backend

### Tecnologias

- **Python**: Linguagem principal
- **FastAPI**: Framework para API REST
- **OpenAI Agents SDK**: Para criação dos agentes inteligentes
- **Pydantic**: Para validação de dados
- **SQLAlchemy/SQLModel**: ORM para persistência (se necessário)
- **Pytest**: Para testes unitários

### Componentes do Backend

#### 1. Módulo de Agentes

- **brain.py**: Agente principal que coordenará outros agentes.
  - Implementará `Agent` do OpenAI Agents SDK.
  - Conterá instruções para o comportamento do agente, incluindo o uso de ferramentas.
  - Definirá ferramentas disponíveis (ex: `get_weather`).

```python
from agents import Agent, Runner, function_tool
from .tools.weather import get_weather # Importa a ferramenta

# Define as ferramentas que o agente pode usar
agent_tools = [get_weather]

# Atualiza as instruções para mencionar a capacidade de obter o clima
agent_instructions = """
Você é Voxy, um assistente inteligente projetado para ser útil, amigável e eficiente.

Suas características principais:
- Responder perguntas com informações precisas e atualizadas.
- Auxiliar na resolução de problemas.
- Manter conversas naturais e engajadoras.
- Adaptar-se ao estilo e necessidades do usuário.
- Você pode verificar a previsão do tempo para uma cidade específica usando a ferramenta disponível.

Sempre priorize a clareza, a precisão e a utilidade em suas respostas.
"""

# Inicializa o agente com as ferramentas e instruções atualizadas
initial_agent = Agent(
    name="Voxy Brain",
    instructions=agent_instructions,
    tools=agent_tools
)

async def process_message(message: str):
    """
    Processa uma mensagem recebida de forma assíncrona e retorna a resposta do agente.
    
    Args:
        message (str): Mensagem do usuário.
        
    Returns:
        str: Resposta do agente.
    """
    # Usar Runner.run() para execução assíncrona
    # O Runner gerenciará a chamada da ferramenta se o LLM decidir usá-la
    result = await Runner.run(initial_agent, message)
    return result.final_output
```

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

- **chat.py**: Endpoints para comunicação com o agente (sem alterações necessárias para adicionar ferramentas ao agente).

```python
# Nenhuma mudança necessária aqui para a ferramenta
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from ..agents.brain import process_message

router = APIRouter()

class ChatMessage(BaseModel):
    content: str

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Envia uma mensagem para o agente e retorna sua resposta.
    Chama diretamente a função assíncrona process_message.
    """
    try:
        response = await process_message(message.content)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar mensagem: {str(e)}")
```

#### 3. Módulo de Core

- **config.py**: Configurações do aplicativo
- **security.py**: Funcionalidades de segurança (se necessário)

#### 4. Módulo de Banco de Dados (opcional)

- **models.py**: Modelos de dados para persistência de mensagens e histórico

## Frontend

### Tecnologias

- **React**: Biblioteca para UI
- **Vite**: Ferramenta de build e servidor de desenvolvimento rápido
- **Tailwind CSS**: Framework CSS
- **shadcn/ui:** Biblioteca de componentes reutilizáveis (instalados via CLI ou manualmente)
- **Framer Motion (Opcional):** Para animações e transições suaves.
- **Lucide React:** Biblioteca de ícones SVG.
- **Fetch API / Axios**: Cliente HTTP para comunicação com o backend

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

### Fase 1: Configuração Inicial

1. Configurar estrutura de pastas do projeto
2. Configurar ambiente de desenvolvimento
3. Inicializar repositório Git

### Fase 2: Backend Básico

1. Criar estrutura básica do aplicativo FastAPI
2. Implementar o agente brain usando OpenAI Agents SDK (com execução assíncrona)
3. Criar endpoints básicos da API
4. Implementar testes unitários (adaptados para async)

### Fase 3: Frontend Básico

1. Configurar projeto React com Tailwind CSS
2. Implementar componentes básicos da UI
3. Criar interface de chat
4. Integrar com o backend

### **Fase 4: Melhoria da UI/UX do Frontend (Atual)**

1.  **Configurar Bibliotecas de UI:** Instalar e configurar `shadcn/ui` e `lucide-react`.
2.  **Refatorar Componentes:** Atualizar `App.jsx`, `ChatBox.jsx`, `ChatMessage.jsx`, `ChatInput.jsx` usando os novos componentes e estilos.
3.  **Aplicar Estilos Globais:** Definir paleta de cores, fontes e estilos base em `globals.css`/`index.css`.
4.  **Adicionar Animações (Opcional):** Integrar `framer-motion` para feedback visual.

### Fase 5: Funcionalidades do Agente

1.  **Implementar Ferramentas:**
    *   Criar ferramentas úteis (ex: `get_weather`) em `backend/app/agents/tools/`.
    *   Usar `@function_tool` para registrar as ferramentas.
    *   Integrar APIs externas (ex: **OpenWeatherMap para `get_weather`**) se necessário. Utilizar `httpx` para chamadas assíncronas.
    *   Escrever testes unitários para as ferramentas (mockando chamadas externas).
2.  **Integrar Ferramentas ao Agente:**
    *   Importar e adicionar ferramentas à lista `tools` na inicialização do `Agent` em `brain.py`.
    *   Atualizar as `instructions` do agente para informá-lo sobre as novas ferramentas.

### Fase 6: Refinamento

1. Melhorar a experiência do usuário
2. Adicionar mais ferramentas/agentes
3. Reforçar a segurança
4. Otimizar desempenho

## Considerações de Segurança

- Armazenar chaves de API (ex: `OPENAI_API_KEY`, **`OPENWEATHERMAP_API_KEY`**) em variáveis de ambiente (`.env` no backend).
- Implementar validação de entrada rigorosa
- Considerar a adição de autenticação de usuário
- Limitar taxa de solicitações à API

## Teste e Qualidade de Código

- Implementar testes unitários para todas as funcionalidades principais (incluindo ferramentas)
- Implementar testes de componentes para o frontend, se possível.
- Seguir PEP8 e formatação com Black (backend).
- Usar linters (ESLint/Prettier) para o frontend.
- Utilizar dicas de tipo em todas as funções (backend).
- Documentar adequadamente todas as classes e funções.

## Tecnologias e Dependências

### Backend

```
fastapi # Usar versão mais recente ou especificar >=1.0
uvicorn # Usar versão mais recente ou especificar >=0.22.0
pydantic # Usar versão mais recente ou especificar >=2.0.0
openai-agents # Usar versão mais recente (ex: >=0.0.7)
python-dotenv>=1.0.0
pytest>=7.3.1
pytest-asyncio # Necessário para testes async com pytest
httpx>=0.24.0 # Para chamadas HTTP assíncronas (incluindo API de clima)
# requests # Alternativa síncrona, mas httpx é preferível para async
# sqlalchemy>=2.0.0  # Opcional
# python-jose>=3.3.0 # Opcional
```

### Frontend

```
react>=18.0.0
react-dom>=18.0.0
react-scripts>=5.0.0
tailwindcss>=3.3.0
# shadcn/ui (via CLI)
# lucide-react 
# framer-motion (Opcional)
# @radix-ui/* (Dependências do shadcn)
# class-variance-authority 
# clsx 
# tailwind-merge 
# tailwindcss-animate 
# axios (Opcional)
```
