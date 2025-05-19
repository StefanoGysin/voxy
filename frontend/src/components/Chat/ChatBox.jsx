import React from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import ChatMessage from './ChatMessage';

/**
 * Componente que renderiza a caixa de chat com todas as mensagens.
 * 
 * @param {Object} props - Propriedades do componente.
 * @param {Array} props.messages - Lista de mensagens para renderizar.
 * @param {React.RefObject} props.chatBoxRef - Referência para o elemento de scroll.
 * @param {boolean} props.isLoading - Indica se está carregando mensagens.
 */
const ChatBox = ({ messages = [], chatBoxRef, isLoading = false }) => {
  return (
    <ScrollArea className="h-full p-4" ref={chatBoxRef}>
      <div className="flex flex-col space-y-4">
        {messages.length === 0 && !isLoading ? (
          <div className="text-center text-muted-foreground p-4">
            Sua conversa com o Voxy aparecerá aqui.
          </div>
        ) : (
          <>
            {isLoading && messages.length === 0 ? (
              <div className="text-center text-muted-foreground p-4">
                Carregando mensagens...
              </div>
            ) : (
              messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))
            )}
          </>
        )}
      </div>
    </ScrollArea>
  );
};

export default ChatBox; 