import React from 'react';
import ChatBox from './components/Chat/ChatBox'; // Corrigido caminho da importação
import { sendMessage } from './services/api'; // Assume que api.js será copiado

/**
 * Componente principal da aplicação Voxy.
 * Aplica layout base e integra o ChatBox.
 */
function App() {
  // Função wrapper para enviar mensagens, com tratamento de erro básico
  const handleSendMessage = async (content) => {
    try {
      const response = await sendMessage(content);
      return response; // Retorna a resposta do backend para o ChatBox
    } catch (error) {
      console.error('Erro ao enviar mensagem:', error);
      // Poderia retornar uma mensagem de erro específica para o ChatBox exibir
      return `Erro: ${error.message || 'Não foi possível conectar ao servidor.'}`;
    }
  };

  return (
    // Layout principal: Tela cheia, flex column, cor de fundo do tema
    <div className="flex flex-col h-screen bg-background text-foreground">
      {/* Cabeçalho: Cor primária do tema, texto contrastante */}
      <header className="bg-primary text-primary-foreground p-4">
        <h1 className="text-2xl font-bold">Voxy</h1>
        {/* <p className="text-sm opacity-80">Seu assistente inteligente</p> */}
      </header>
      
      {/* Conteúdo Principal: Ocupa espaço restante, scrollavel se necessário */}
      {/* Usamos container para centralizar e limitar largura em telas grandes */}
      {/* Removida a div interna com bg-white/shadow, ChatBox cuidará disso */}
      <main className="flex-1 overflow-hidden container mx-auto w-full p-4 md:p-6">
         <ChatBox sendMessage={handleSendMessage} />
      </main>
      
      {/* Rodapé: Fundo padrão, borda superior, texto suave */}
      <footer className="border-t border p-3 text-center text-muted-foreground text-sm">
        Voxy &copy; {new Date().getFullYear()}
      </footer>
    </div>
  );
}

export default App;
