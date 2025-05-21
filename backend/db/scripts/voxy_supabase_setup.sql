-- Arquivo de Configuração do Supabase para o Projeto Voxy
-- Este arquivo contém todos os comandos SQL necessários para configurar o banco de dados no Supabase

-- Tabelas Principais

-- 1. Tabela de Sessões de Chat
CREATE TABLE IF NOT EXISTS public.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT DEFAULT 'Nova Conversa',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Tabela de Mensagens de Chat
CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para otimizar consultas

CREATE INDEX IF NOT EXISTS idx_messages_session_id ON public.messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON public.messages(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON public.sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON public.messages(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_updated_at ON public.sessions(updated_at DESC);

-- Funções e Gatilhos

-- Função para atualizar automaticamente o campo updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Gatilho para atualizar updated_at em sessions
CREATE TRIGGER update_sessions_updated_at
    BEFORE UPDATE ON public.sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Função para atualizar updated_at na sessão quando uma mensagem é adicionada
CREATE OR REPLACE FUNCTION update_session_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.sessions
    SET updated_at = NOW()
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Gatilho para atualizar a sessão quando uma mensagem é adicionada
CREATE TRIGGER update_session_when_message_added
    AFTER INSERT ON public.messages
    FOR EACH ROW
    EXECUTE FUNCTION update_session_updated_at();

-- Configuração de Segurança (RLS - Row Level Security)

-- Habilitar RLS para as tabelas
ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- Políticas para sessions - usuários só podem acessar suas próprias sessões
CREATE POLICY sessions_select_policy ON public.sessions
    FOR SELECT USING (auth.uid() = user_id);
    
CREATE POLICY sessions_insert_policy ON public.sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);
    
CREATE POLICY sessions_update_policy ON public.sessions
    FOR UPDATE USING (auth.uid() = user_id);
    
CREATE POLICY sessions_delete_policy ON public.sessions
    FOR DELETE USING (auth.uid() = user_id);

-- Políticas para messages - usuários só podem acessar mensagens das suas sessões
CREATE POLICY messages_select_policy ON public.messages
    FOR SELECT USING (auth.uid() = user_id);
    
CREATE POLICY messages_insert_policy ON public.messages
    FOR INSERT WITH CHECK (auth.uid() = user_id);
    
CREATE POLICY messages_update_policy ON public.messages
    FOR UPDATE USING (auth.uid() = user_id);
    
CREATE POLICY messages_delete_policy ON public.messages
    FOR DELETE USING (auth.uid() = user_id);

-- Configuração de Storage para imagens

-- Criar bucket para imagens de chat (via SQL ou Interface do Supabase)
INSERT INTO storage.buckets (id, name, public, avif_autodetection)
VALUES ('chat-images', 'chat-images', false, false);

-- Políticas RLS para o bucket chat-images
-- Política para upload (usuários só podem fazer upload em suas próprias pastas)
CREATE POLICY storage_insert_policy ON storage.objects
    FOR INSERT TO authenticated
    WITH CHECK (
        bucket_id = 'chat-images' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Política para visualização (usuários só podem ver seus próprios arquivos)
CREATE POLICY storage_select_policy ON storage.objects
    FOR SELECT TO authenticated
    USING (
        bucket_id = 'chat-images' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Política para atualização (usuários só podem atualizar seus próprios arquivos)
CREATE POLICY storage_update_policy ON storage.objects
    FOR UPDATE TO authenticated
    USING (
        bucket_id = 'chat-images' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Política para exclusão (usuários só podem excluir seus próprios arquivos)
CREATE POLICY storage_delete_policy ON storage.objects
    FOR DELETE TO authenticated
    USING (
        bucket_id = 'chat-images' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Configuração da extensão pgvector (para a tabela memories)
-- Este comando deve ser executado pelo superusuário ou owner do banco de dados
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabela para armazenar memórias vetorizadas (usada pelo Mem0)
CREATE TABLE IF NOT EXISTS public.memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding VECTOR(1536), -- Dimensão para embeddings da OpenAI
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para a tabela memories
CREATE INDEX IF NOT EXISTS idx_memories_user_id ON public.memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_agent_id ON public.memories(agent_id);
CREATE INDEX IF NOT EXISTS idx_memories_created_at ON public.memories(created_at);

-- Índice para busca vetorial usando HNSW (Hierarchical Navigable Small World)
CREATE INDEX IF NOT EXISTS idx_memories_embedding ON public.memories USING hnsw (embedding vector_cosine_ops);

-- Política RLS para a tabela memories
ALTER TABLE public.memories ENABLE ROW LEVEL SECURITY;

-- Política para selecionar memórias (usuários só podem ver suas próprias memórias)
CREATE POLICY memories_select_policy ON public.memories
    FOR SELECT USING (user_id = auth.uid()::text);

-- Política para inserir memórias (usuários só podem inserir suas próprias memórias)
CREATE POLICY memories_insert_policy ON public.memories
    FOR INSERT WITH CHECK (user_id = auth.uid()::text);

-- Política para atualizar memórias (usuários só podem atualizar suas próprias memórias)
CREATE POLICY memories_update_policy ON public.memories
    FOR UPDATE USING (user_id = auth.uid()::text);

-- Política para excluir memórias (usuários só podem excluir suas próprias memórias)
CREATE POLICY memories_delete_policy ON public.memories
    FOR DELETE USING (user_id = auth.uid()::text);

-- NOVA SEÇÃO: Configuração do Realtime para as tabelas
-- Esta seção resolve o erro "Realtime connection error. Chat updates may be delayed."

-- Habilitar publicação de eventos Realtime para as tabelas
ALTER PUBLICATION supabase_realtime ADD TABLE public.sessions;
ALTER PUBLICATION supabase_realtime ADD TABLE public.messages;

-- Se a publicação ainda não existir, criá-la primeiro
-- (Descomente as linhas abaixo se necessário)
-- CREATE PUBLICATION supabase_realtime FOR TABLE public.sessions, public.messages;

-- Certifique-se de que o Realtime está configurado para o escopo correto no projeto Supabase
-- Isso deve ser verificado na interface de administração do Supabase:
-- 1. Acesse seu projeto no Supabase
-- 2. Vá para Database > Replication > Supabase Realtime
-- 3. Certifique-se de que está configurado para "Send all changes" ou pelo menos incluir as tabelas sessions e messages
-- 4. Certifique-se de que o serviço Realtime está habilitado em Project Settings > API > Realtime 