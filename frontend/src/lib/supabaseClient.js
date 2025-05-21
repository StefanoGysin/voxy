import { createClient } from '@supabase/supabase-js';

// Lê as variáveis de ambiente do Vite (devem começar com VITE_)
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// Verifica se as variáveis estão definidas
if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error("Supabase URL and Anon Key must be defined in .env file with VITE_ prefix");
}

// Cria e exporta o cliente Supabase com configuração explícita do Realtime
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  realtime: {
    enabled: true,
    params: {
      eventsPerSecond: 10
    }
  }
}); 