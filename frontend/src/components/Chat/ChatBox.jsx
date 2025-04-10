// Conteúdo copiado de frontend_old/src/components/Chat/ChatBox.jsx
import React, { useEffect, useRef } from 'react';
import { ScrollArea } from "@/components/ui/scroll-area";
import ChatMessage from './ChatMessage';
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { Bot } from 'lucide-react';

/**
 * Displays the list of messages in a scrollable area.
 * @param {object} props - Component props.
 * @param {Array} props.messages - Array of message objects.
 * @param {boolean} props.isLoading - Indicates if messages are loading.
 * @param {React.Ref} props.scrollAreaRef - Ref for the scroll area viewport.
 */
const ChatBox = ({ messages = [], isLoading = false, scrollAreaRef }) => {
  const endOfMessagesRef = useRef(null);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    if (endOfMessagesRef.current) {
      endOfMessagesRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]); // Dependency: messages array

  return (
    <div className="flex flex-col h-full bg-card border rounded-lg shadow-sm">
      <ScrollArea className="flex-1 p-4 overflow-y-auto" viewportRef={scrollAreaRef}>
        <div className="space-y-4">
          {isLoading && messages.length === 0 && (
            <div className="space-y-2">
              <Skeleton className="h-16 w-3/4" />
              <Skeleton className="h-16 w-3/4 ml-auto" />
              <Skeleton className="h-16 w-3/4" />
            </div>
          )}
          {!isLoading && messages.length === 0 && (
            <p className="text-center text-gray-500">Nenhuma mensagem ainda. Comece a conversar!</p>
          )}
          {messages.map((msg, index) => (
            <ChatMessage key={msg.id || index} message={msg} />
          ))}
          {isLoading && (
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
          <div ref={endOfMessagesRef} />
        </div>
      </ScrollArea>
    </div>
  );
};

export default ChatBox; 