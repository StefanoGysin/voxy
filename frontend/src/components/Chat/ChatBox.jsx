// Conteúdo copiado de frontend_old/src/components/Chat/ChatBox.jsx
import React, { useState, useEffect, useRef } from 'react';
import { ScrollArea } from "@/components/ui/scroll-area";
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { cn } from "@/lib/utils";
import { Bot } from 'lucide-react';

/**
 * Componente principal do chat que gerencia mensagens, interação e exibição,
 * usando componentes shadcn/ui.
 * 
 * @param {Object} props - Propriedades do componente
 * @param {Function} props.sendMessage - Função para enviar mensagens para a API
 */
const ChatBox = ({ sendMessage }) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const scrollAreaRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (content) => {
    if (!content.trim() || loading) return;

    setLoading(true);
    const userMessage = { role: 'user', content };
    setMessages(prev => [...prev, userMessage]);
    
    await new Promise(resolve => setTimeout(resolve, 50));
    
    try {
      const response = await sendMessage(content);
      const assistantMessage = { role: 'assistant', content: response };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Erro ao enviar mensagem:', error);
      setMessages(prev => [
        ...prev, 
        { 
          role: 'assistant', 
          content: typeof error === 'string' ? error : (error?.message || 'Desculpe, ocorreu um erro ao processar sua mensagem.')
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-card border rounded-lg shadow-sm">
      <ScrollArea ref={scrollAreaRef} className="flex-1 p-4 space-y-4">
        {messages.length === 0 && !loading ? (
          <div className="text-center text-muted-foreground my-8">
            <p>Bem-vindo ao Voxy!</p>
            <p className="text-sm mt-2">Envie uma mensagem para iniciar a conversa.</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <ChatMessage key={index} message={message} />
          ))
        )}
        
        {loading && (
          <div className={cn("flex mb-4 justify-start")} >
            <div className={cn("flex items-end gap-2 max-w-[85%] flex-row")} >
              <Bot className="h-6 w-6 text-muted-foreground" />
              <div className={cn(
                  "p-3 rounded-lg flex items-center",
                  "bg-muted text-muted-foreground rounded-bl-none"
              )}>
                <div className="dot-typing"></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </ScrollArea>
      
      <ChatInput onSendMessage={handleSendMessage} disabled={loading} />
    </div>
  );
};

export default ChatBox; 