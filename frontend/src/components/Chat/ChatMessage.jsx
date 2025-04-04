import React from 'react';
import { cn } from "@/lib/utils";
import { User, Bot } from 'lucide-react';

/**
 * Componente para exibir uma mensagem individual no chat, com avatar.
 * 
 * @param {Object} props - Propriedades do componente
 * @param {Object} props.message - Objeto contendo os dados da mensagem
 * @param {string} props.message.role - Papel do remetente ('user' ou 'assistant')
 * @param {string} props.message.content - Conteúdo da mensagem
 */
const ChatMessage = ({ message }) => {
  const isUser = message.role === 'user';
  
  const messageBubbleClasses = cn(
    "max-w-full p-3 rounded-lg",
    {
      "bg-primary text-primary-foreground rounded-br-none": isUser,
      "bg-muted text-muted-foreground rounded-bl-none": !isUser,
    }
  );

  const messageContainerClasses = cn(
    "flex items-end gap-2 max-w-[85%]",
    isUser ? "flex-row-reverse" : "flex-row"
  );

  return (
    <div className={cn("flex mb-4", isUser ? 'justify-end' : 'justify-start')}>
      <div className={messageContainerClasses}>
        {isUser ? (
          <User className="h-6 w-6 text-primary" />
        ) : (
          <Bot className="h-6 w-6 text-muted-foreground" />
        )}
        <div className={messageBubbleClasses}>
          {message.content}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage; 