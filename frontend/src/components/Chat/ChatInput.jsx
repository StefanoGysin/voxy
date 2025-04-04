// Conteúdo copiado de frontend_old/src/components/Chat/ChatInput.jsx
import React, { useState } from 'react';
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Send } from 'lucide-react';

/**
 * Componente para entrada de mensagens no chat, usando componentes shadcn/ui.
 * 
 * @param {Object} props - Propriedades do componente
 * @param {Function} props.onSendMessage - Função chamada quando uma mensagem é enviada
 * @param {boolean} props.disabled - Se o input deve estar desabilitado
 */
const ChatInput = ({ onSendMessage, disabled = false }) => {
  const [message, setMessage] = useState('');

  const sendMessageHandler = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessageHandler();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessageHandler();
  };

  return (
    <form 
      onSubmit={handleSubmit} 
      className="border-t border bg-background p-4"
    >
      <div className="flex w-full items-center space-x-2">
        <Input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Digite sua mensagem..."
          disabled={disabled}
          className="flex-1"
          autoComplete="off"
        />
        <Button
          type="submit"
          size="icon"
          disabled={!message.trim() || disabled}
        >
          <Send className="h-4 w-4" />
          <span className="sr-only">Enviar</span>
        </Button>
      </div>
    </form>
  );
};

export default ChatInput; 