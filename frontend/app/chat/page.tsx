"use client";

import { useState, useRef, useEffect } from "react";
import { chatWithBot, type ChatMessage, type Source } from "@/lib/api";

type Message = ChatMessage & { sources?: Source[] };

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello! I'm InsureBot, your AI insurance assistant. Ask me anything about insurance policies, coverage, claims, or premiums.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const result = await chatWithBot(question);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: result.answer, sources: result.sources },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "⚠️ Unable to reach the backend. Make sure the FastAPI server is running on port 8000.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-65px)] max-w-3xl mx-auto px-4">
      {/* Header */}
      <div className="py-4 border-b border-[#2d3148]">
        <h1 className="text-xl font-bold text-white">Insurance Chat</h1>
        <p className="text-[#94a3b8] text-sm">
          Powered by local Ollama + ChromaDB RAG
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-[#6366f1] text-white rounded-br-sm"
                  : "bg-[#1a1d27] border border-[#2d3148] text-[#e2e8f0] rounded-bl-sm"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap leading-relaxed">
                {msg.content}
              </p>
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 pt-2 border-t border-[#2d3148]">
                  <p className="text-xs text-[#6366f1] font-medium mb-1">
                    Sources:
                  </p>
                  {msg.sources.map((s, j) => (
                    <p key={j} className="text-xs text-[#94a3b8]">
                      {s.company} — {s.source} (p.{s.page})
                    </p>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-[#1a1d27] border border-[#2d3148] rounded-2xl rounded-bl-sm px-4 py-3">
              <div className="flex gap-1 items-center">
                <span className="w-2 h-2 bg-[#6366f1] rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-2 h-2 bg-[#6366f1] rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-2 h-2 bg-[#6366f1] rounded-full animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="py-4 border-t border-[#2d3148] flex gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about insurance policies…"
          disabled={loading}
          className="flex-1 bg-[#1a1d27] border border-[#2d3148] rounded-xl px-4 py-2.5 text-sm text-[#e2e8f0] placeholder-[#94a3b8] focus:outline-none focus:border-[#6366f1] disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="bg-[#6366f1] hover:bg-[#4f46e5] text-white px-5 py-2.5 rounded-xl text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </form>
    </div>
  );
}
