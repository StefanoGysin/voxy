import React from 'react';
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton"; // For loading state
import { PlusCircle, MessageSquare } from 'lucide-react';
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from 'date-fns'; // To display relative time

/**
 * Sidebar component to display chat sessions and allow creation/selection.
 *
 * @param {Object} props - Component props.
 * @param {Array<object>} props.sessions - List of session objects [{id, title, created_at, updated_at}].
 * @param {string|null} props.currentSessionId - The ID of the currently active session.
 * @param {boolean} props.isLoading - Indicates if sessions are currently being loaded.
 * @param {Function} props.onSelectSession - Callback function when a session is selected (receives sessionId).
 * @param {Function} props.onCreateNew - Callback function when the "New Chat" button is clicked.
 */
const SessionSidebar = ({
  sessions = [],
  currentSessionId = null,
  isLoading = false,
  onSelectSession,
  onCreateNew,
}) => {

  const formatSessionTitle = (session) => {
    // Placeholder: Use a truncated ID or relative timestamp if no title
    // TODO: Implement session title logic later if needed
    return `Chat ${formatDistanceToNow(new Date(session.updated_at || session.created_at), { addSuffix: true })}`;
  };

  return (
    <aside className="w-64 flex flex-col border-r bg-muted/40 p-4 space-y-4">
      <Button variant="outline" onClick={onCreateNew} className="w-full justify-start">
        <PlusCircle className="mr-2 h-4 w-4" />
        New Chat
      </Button>

      <h2 className="text-lg font-semibold tracking-tight px-2">
        History
      </h2>

      <ScrollArea className="flex-1 -mx-2">
        <div className="space-y-1 px-2">
          {isLoading ? (
            // Loading Skeleton
            <>
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </>
          ) : sessions.length === 0 ? (
              <p className="text-sm text-muted-foreground px-2 py-4 text-center">No chat history yet.</p>
          ) : (
            sessions.map((session) => (
              <Button
                key={session.id}
                variant={currentSessionId === session.id ? "secondary" : "ghost"}
                className={cn(
                  "w-full justify-start truncate",
                  currentSessionId === session.id && "font-semibold"
                )}
                onClick={() => onSelectSession(session.id)}
              >
                <MessageSquare className="mr-2 h-4 w-4 flex-shrink-0" />
                <span className="truncate">{formatSessionTitle(session)}</span>
              </Button>
            ))
          )}
        </div>
      </ScrollArea>
      {/* Maybe add user info or settings button at the bottom later */}
    </aside>
  );
};

export default SessionSidebar; 