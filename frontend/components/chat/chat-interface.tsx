"use client";

import Link from "next/link";
import { AxiosError } from "axios";
import { Loader2, Send } from "lucide-react";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { askRag } from "@/services/rag";
import type { ChatMessage } from "@/types/rag";

type ChatFormValues = {
  question: string;
};

export function ChatInterface() {
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const {
    formState: { isSubmitting },
    handleSubmit,
    register,
    reset,
  } = useForm<ChatFormValues>({
    defaultValues: {
      question: "",
    },
  });

  const hasMessages = messages.length > 0;
  const lastSources = useMemo(
    () => [...messages].reverse().find((message) => message.role === "assistant" && message.sources)?.sources ?? [],
    [messages],
  );

  const onSubmit = handleSubmit(async (values) => {
    const question = values.question.trim();

    if (!question) {
      return;
    }

    setError(null);
    const userMessage: ChatMessage = {
      content: question,
      id: crypto.randomUUID(),
      role: "user",
    };

    setMessages((current) => [...current, userMessage]);
    reset();

    try {
      const response = await askRag({ question, top_k: 5 });
      const assistantMessage: ChatMessage = {
        content: response.answer,
        id: crypto.randomUUID(),
        role: "assistant",
        sources: response.sources,
      };
      setMessages((current) => [...current, assistantMessage]);
    } catch (caughtError) {
      setError(getErrorMessage(caughtError, "Unable to ask the memory engine."));
    }
  });

  return (
    <div className="grid min-h-[calc(100vh-11rem)] gap-4 xl:grid-cols-[minmax(0,1fr)_22rem]">
      <Card className="flex min-h-[36rem] flex-col overflow-hidden">
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {error ? (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}

          {!hasMessages ? (
            <div className="flex h-full min-h-72 items-center justify-center text-center text-sm text-muted-foreground">
              Ask a question about your saved memories.
            </div>
          ) : null}

          {messages.map((message) => (
            <div
              className={message.role === "user" ? "flex justify-end" : "flex justify-start"}
              key={message.id}
            >
              <div
                className={
                  message.role === "user"
                    ? "max-w-[82%] rounded-lg bg-primary px-4 py-3 text-sm leading-6 text-primary-foreground"
                    : "max-w-[82%] rounded-lg border border-border bg-muted px-4 py-3 text-sm leading-6 text-foreground"
                }
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
                {message.sources?.length ? (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {message.sources.map((source) => (
                      <Badge key={`${message.id}-${source.memory_id}`}>
                        [{source.memory_id}] {source.title}
                      </Badge>
                    ))}
                  </div>
                ) : null}
              </div>
            </div>
          ))}
        </div>

        <form className="border-t border-border p-4" onSubmit={onSubmit}>
          <div className="space-y-2">
            <Label htmlFor="question">Message</Label>
            <div className="flex gap-2">
              <Textarea
                className="min-h-12 resize-none"
                id="question"
                placeholder="Ask the engine what you know about..."
                {...register("question", { required: true })}
              />
              <Button disabled={isSubmitting} size="icon" type="submit">
                {isSubmitting ? (
                  <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                ) : (
                  <Send className="size-4" aria-hidden="true" />
                )}
                <span className="sr-only">Send</span>
              </Button>
            </div>
          </div>
        </form>
      </Card>

      <Card className="p-4">
        <h2 className="text-sm font-semibold text-foreground">Sources</h2>
        <p className="mt-1 text-xs text-muted-foreground">Citations returned with the latest answer.</p>

        <div className="mt-4 space-y-3">
          {lastSources.length === 0 ? (
            <p className="text-sm text-muted-foreground">No citations yet.</p>
          ) : null}

          {lastSources.map((source) => (
            <Link
              className="block rounded-md border border-border p-3 transition-colors hover:bg-muted"
              href={`/dashboard/memories/${source.memory_id}`}
              key={source.memory_id}
            >
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm font-medium text-foreground">[{source.memory_id}] {source.title}</p>
                <Badge>{source.category}</Badge>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                Distance {source.distance.toFixed(4)}
              </p>
            </Link>
          ))}
        </div>
      </Card>
    </div>
  );
}

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof AxiosError ? error.response?.data?.detail ?? fallback : fallback;
}
