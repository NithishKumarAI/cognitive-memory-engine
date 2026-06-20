import { ChatInterface } from "@/components/chat/chat-interface";
import { PageHeader } from "@/components/dashboard/page-header";

export default function ChatPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        description="Ask questions against saved memories and inspect the citations behind each answer."
        title="Chat"
      />
      <ChatInterface />
    </div>
  );
}
