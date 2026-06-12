"use client";

import Link from "next/link";
import ChatBox from "@/components/ChatBox";

export default function ChatPage() {
  return (
    <main className="flex-1 flex flex-col h-screen">
      {/* Background gradient */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(99,102,241,0.06)_0%,_transparent_50%)]" />
      </div>

      {/* Header */}
      <header className="border-b border-card-border px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/analyze"
              className="text-muted text-sm hover:text-accent transition-colors"
              id="back-to-results"
            >
              ← Results
            </Link>
            <div className="w-px h-5 bg-card-border" />
            <h1 className="text-sm font-semibold">
              <span className="text-muted">Profile</span>{" "}
              <span className="text-accent">Chat</span>
            </h1>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-green-accent animate-pulse" />
            <span className="text-xs text-muted">AI Ready</span>
          </div>
        </div>
      </header>

      {/* Chat area */}
      <div className="flex-1 max-w-3xl mx-auto w-full">
        <ChatBox />
      </div>
    </main>
  );
}
