# Documentação do Esquema SQL do Supabase para Voxy

Este documento descreve o esquema do banco de dados SQL utilizado no Supabase para armazenar as sessões de chat e mensagens do projeto Voxy, conforme definido na Fase 10 do `TASK.md`.

## Visão Geral

O esquema consiste em duas tabelas principais:

1.  `sessions`: Armazena informações sobre cada conversa individual.
2.  `messages`: Armazena cada mensagem trocada dentro de uma sessão específica.

Ele também inclui índices para otimizar consultas e uma função com um gatilho (trigger) para manter o timestamp de atualização das sessões.

## Tabela `sessions`

Esta tabela guarda os metadados de cada sessão de chat.

```sql
CREATE TABLE sessions (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id uuid NULL, -- Chave estrangeira para a tabela users
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    title TEXT NULL
);
```

### Colunas

| Coluna     | Tipo                        | Descrição                                                                                                | Restrições / Padrões                                      |
| :--------- | :-------------------------- | :------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------- |
| `id`       | `uuid`                      | Identificador único universal para a sessão.                                                             | `PRIMARY KEY`, `DEFAULT gen_random_uuid()`                |
| `user_id`  | `uuid`                      | Referência ao usuário proprietário da sessão (da tabela `users` de autenticação). Pode ser `NULL` inicialmente. | `NULL` (Será `FOREIGN KEY REFERENCES users(id)` no futuro) |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Data e hora em que a sessão foi criada.                                                                  | `DEFAULT CURRENT_TIMESTAMP`, `NOT NULL`                   |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | Data e hora da última atividade (mensagem) na sessão. Usado para ordenar sessões recentes.             | `DEFAULT CURRENT_TIMESTAMP`, `NOT NULL`                   |
| `title`    | `TEXT`                      | Um título opcional para a sessão, que pode ser gerado automaticamente ou definido pelo usuário.             | `NULL`                                                    |

### Índices

*   `idx_sessions_user_id`: Otimiza a busca de sessões pertencentes a um usuário específico.
    ```sql
    CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id);
    ```
*   `idx_sessions_updated_at`: Otimiza a ordenação das sessões pela data da última atualização (útil para mostrar as mais recentes primeiro).
    ```sql
    CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON sessions (updated_at DESC);
    ```

## Tabela `messages`

Esta tabela armazena cada mensagem individual trocada dentro de uma sessão.

```sql
CREATE TABLE messages (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    session_id uuid NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL
);
```

### Colunas

| Coluna     | Tipo                        | Descrição                                                                       | Restrições / Padrões                                                              |
| :--------- | :-------------------------- | :------------------------------------------------------------------------------ | :-------------------------------------------------------------------------------- |
| `id`       | `uuid`                      | Identificador único universal para a mensagem.                                  | `PRIMARY KEY`, `DEFAULT gen_random_uuid()`                                        |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | Data e hora em que a mensagem foi criada.                                       | `DEFAULT CURRENT_TIMESTAMP`, `NOT NULL`                                           |
| `session_id` | `uuid`                      | Chave estrangeira que referencia a sessão (`sessions.id`) à qual esta mensagem pertence. | `NOT NULL`, `REFERENCES sessions(id) ON DELETE CASCADE`                             |
| `role`     | `TEXT`                      | Indica quem enviou a mensagem: 'user' para o humano, 'assistant' para a IA.     | `NOT NULL`, `CHECK (role IN ('user', 'assistant'))`                             |
| `content`  | `TEXT`                      | O conteúdo textual da mensagem.                                                 | `NOT NULL`                                                                        |

**Nota sobre `ON DELETE CASCADE`:** Se uma linha na tabela `sessions` for deletada, todas as mensagens correspondentes (`messages`) que referenciam essa sessão também serão automaticamente deletadas.

### Índices

*   `idx_messages_session_id_created_at`: Otimiza a busca de todas as mensagens de uma sessão específica, ordenadas por data de criação (para exibir o histórico na ordem correta).
    ```sql
    CREATE INDEX IF NOT EXISTS idx_messages_session_id_created_at ON messages (session_id, created_at);
    ```

## Função e Gatilho (Trigger) `update_session_updated_at`

Este conjunto automatiza a atualização do campo `updated_at` na tabela `sessions` sempre que uma nova mensagem é inserida na tabela `messages`. Isso garante que o `updated_at` da sessão sempre reflita a hora da última mensagem.

### Função `update_session_updated_at()`

```sql
CREATE OR REPLACE FUNCTION update_session_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sessions
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.session_id; -- NEW.session_id refere-se ao session_id da mensagem que acabou de ser inserida
    RETURN NEW; -- Necessário para triggers AFTER INSERT
END;
$$ LANGUAGE plpgsql;
```

*   **Propósito:** Atualizar o campo `updated_at` da linha correspondente na tabela `sessions`.
*   **`RETURNS TRIGGER`:** Especifica que esta função será usada por um gatilho.
*   **`LANGUAGE plpgsql`:** Define a linguagem procedural padrão do PostgreSQL.
*   **`NEW`:** Uma variável especial em funções de gatilho que contém a nova linha que está sendo inserida (no caso de `INSERT` ou `UPDATE`).

### Gatilho `trigger_update_session_updated_at`

```sql
CREATE TRIGGER trigger_update_session_updated_at
AFTER INSERT ON messages -- Dispara o gatilho DEPOIS que uma linha é inserida em 'messages'
FOR EACH ROW -- O gatilho é executado para cada linha afetada pela operação INSERT
EXECUTE FUNCTION update_session_updated_at(); -- Chama a função definida acima
```

*   **Propósito:** Conectar a função `update_session_updated_at` ao evento de inserção (`INSERT`) na tabela `messages`.
*   **`AFTER INSERT`:** O gatilho é ativado após a conclusão da operação de inserção na tabela `messages`.
*   **`FOR EACH ROW`:** Garante que a função seja executada uma vez para cada mensagem inserida (mesmo que múltiplas mensagens sejam inseridas em uma única instrução SQL).

## Definição da Tabela `users` (Referência)

Embora a tabela `users` seja primariamente gerenciada pelo backend usando SQLModel, uma definição compatível para referência (especialmente para a chave estrangeira `user_id` em `sessions`) seria:

```sql
-- Nota: O backend atualmente usa SQLModel que gera uma tabela com PK 'id' do tipo INTEGER.
-- Esta definição com UUID é mantida aqui para referência histórica ou futura,
-- mas a coluna 'sessions.user_id' deve ser compatível com o tipo real em 'users.id'.
CREATE TABLE users (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY, -- Ou id INTEGER SERIAL PRIMARY KEY se gerenciado pelo SQLModel com PK int
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL
);
```

## Realtime (Opcional)

Para que o frontend receba atualizações de novas mensagens em tempo real via WebSockets, a funcionalidade Realtime do Supabase precisa estar habilitada para a tabela `messages`.

```sql
-- Verifique nas configurações do Supabase ou execute:
-- alter publication supabase_realtime add table messages;
```

Este comando adiciona a tabela `messages` à publicação `supabase_realtime`, permitindo que o Supabase envie notificações sobre inserções, atualizações ou exclusões nesta tabela para os clientes conectados. 