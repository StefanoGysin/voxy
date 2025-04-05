// Conteúdo copiado de frontend_old/src/components/Chat/ChatBox.jsx
import React, { useEffect, useRef } from 'react';
import { ScrollArea } from "@/components/ui/scroll-area";
import ChatMessage from './ChatMessage';
// ChatInput não é mais usado aqui
// import ChatInput from './ChatInput'; 
import { cn } from "@/lib/utils";
import { Bot } from 'lucide-react';

/**
 * Componente que exibe a caixa de mensagens do chat.
 * Recebe as mensagens e o estado de carregamento como props.
 * 
 * @param {Object} props - Propriedades do componente
 * @param {Array} props.messages - Array de objetos de mensagem ({ role: string, content: string })
 * @param {boolean} props.isLoading - Indica se uma resposta está sendo carregada
 * @param {React.RefObject} props.chatBoxRef - Referência para a área de scroll (passada de App.jsx)
 */
const ChatBox = ({ messages, isLoading, chatBoxRef }) => {
  // Remove o estado interno de messages e loading
  // const [messages, setMessages] = useState([]);
  // const [loading, setLoading] = useState(false);
  
  // Mantém a ref para o final das mensagens para scroll automático
  const messagesEndRef = useRef(null);

  // Remove o useEffect daqui, pois App.jsx já gerencia o scroll com chatBoxRef
  /*
  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);
  */

  // A função scrollToBottom pode ser removida se não for usada em outro lugar aqui
  // Ou mantida se houver outra lógica de scroll futura neste componente.
  // Por enquanto, vou manter, mas ela não é chamada pelo useEffect.
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Remove a função interna handleSendMessage
  // const handleSendMessage = async (content) => { ... };

  return (
    <div className="flex flex-col h-full bg-card border rounded-lg shadow-sm">
      {/* Usa a ref passada de App.jsx */}
      <ScrollArea ref={chatBoxRef} className="flex-1 p-4 space-y-4">
        {/* Usa as props messages e isLoading */}
        {messages.length === 0 && !isLoading ? (
          <div className="text-center text-muted-foreground my-8">
            <p>Bem-vindo ao Voxy!</p>
            <p className="text-sm mt-2">Envie uma mensagem para iniciar a conversa.</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <ChatMessage key={index} message={message} />
          ))
        )}
        
        {/* Usa a prop isLoading */}
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
        
        <div ref={messagesEndRef} />
      </ScrollArea>
      
      {/* O ChatInput agora é renderizado diretamente em App.jsx */}
      {/* <ChatInput onSendMessage={handleSendMessage} disabled={loading} /> */}
    </div>
  );
};

export default ChatBox; 