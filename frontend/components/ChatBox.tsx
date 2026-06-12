"use client";

import { useRef, useEffect, useState } from "react";
import { streamChat, type ChatMessage } from "@/lib/api";

export default function ChatBox() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;

    const userMessage: ChatMessage = { role: "user", content: trimmed };
    const history = [...messages];

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsStreaming(true);

    // Add placeholder for assistant response
    const assistantMessage: ChatMessage = { role: "assistant", content: "" };
    setMessages((prev) => [...prev, assistantMessage]);

    await streamChat(
      trimmed,
      history,
      (token) => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "assistant") {
            updated[updated.length - 1] = {
              ...last,
              content: last.content + token,
            };
          }
          return updated;
        });
      },
      () => {
        setIsStreaming(false);
        inputRef.current?.focus();
      },
      (error) => {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "assistant") {
            updated[updated.length - 1] = {
              ...last,
              content: `Error: ${error}`,
            };
          }
          return updated;
        });
        setIsStreaming(false);
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      className="flex flex-col h-full max-h-[calc(100vh-12rem)]"
      id="chat-container"
    >
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-16 space-y-3">
            <div className="text-4xl">💬</div>
            <p className="text-muted text-sm">
              Ask anything about your developer profile
            </p>
            <div className="flex flex-wrap justify-center gap-2 mt-4">
              {[
                "What should I learn next?",
                "How can I improve my GitHub?",
                "What roles am I suited for?",
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => {
                    setInput(suggestion);
                    inputRef.current?.focus();
                  }}
                  className="text-xs px-3 py-1.5 rounded-full bg-card-bg border border-card-border
                             text-muted hover:text-accent hover:border-accent/30 transition-all"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            id={`chat-message-${idx}`}
          >
            <div
              className={`max-w-[80%] px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                msg.role === "user"
                  ? "chat-bubble-user"
                  : "chat-bubble-assistant"
              }`}
            >
              {msg.content}
              {isStreaming &&
                idx === messages.length - 1 &&
                msg.role === "assistant" && (
                  <span className="inline-block w-1.5 h-4 bg-accent ml-0.5 animate-pulse" />
                )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-card-border px-4 py-4">
        <div className="flex items-center gap-3 max-w-3xl mx-auto">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your profile..."
            disabled={isStreaming}
            className="flex-1 bg-card-bg border border-card-border rounded-xl px-4 py-3
                       text-foreground text-sm placeholder:text-muted/40
                       focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30
                       disabled:opacity-50 transition-all"
            id="chat-input"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
            className="bg-accent hover:bg-accent-hover disabled:bg-card-bg disabled:text-muted/40
                       text-white px-5 py-3 rounded-xl text-sm font-medium
                       transition-all disabled:cursor-not-allowed"
            id="chat-send-btn"
          >
            {isStreaming ? (
              <svg
                className="animate-spin h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
            ) : (
              "Send"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
