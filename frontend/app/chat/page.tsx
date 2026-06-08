"use client";

import { signIn, useSession } from "next-auth/react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { AppShell } from "@/components/AppShell";
import { apiFetch, apiStream } from "@/lib/api-client";

const QUICK_PROMPTS = [
  "Как создать подушку безопасности?",
  "Какие налоговые вычеты мне доступны?",
  "Сколько мне нужно откладывать для моей цели?",
];

interface Message {
  role: string;
  content: string;
}

export default function ChatPage() {
  const { data: session, status } = useSession();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [guestLoading, setGuestLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const guestAttempted = useRef(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (status === "loading" || session || guestAttempted.current) return;
    guestAttempted.current = true;
    setGuestLoading(true);
    signIn("credentials", { mode: "guest", redirect: false })
      .then((result) => {
        if (result?.error) setAuthError("Не удалось войти. Попробуйте обновить страницу или войти через /auth/login");
      })
      .finally(() => setGuestLoading(false));
  }, [status, session]);

  useEffect(() => {
    if (!session?.accessToken) return;
    apiFetch<{ session_id: string }>("/api/chat/sessions", {
      method: "POST",
      token: session.accessToken,
    }).then((res) => setSessionId(res.session_id));
  }, [session]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage(text: string) {
    if (!session?.accessToken || !sessionId || streaming) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setStreaming(true);
    let assistantText = "";
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      await apiStream(
        "/api/chat/message",
        { session_id: sessionId, message: text, include_profile: true },
        session.accessToken,
        (chunk) => {
          assistantText += chunk;
          setMessages((prev) => {
            const copy = [...prev];
            copy[copy.length - 1] = { role: "assistant", content: assistantText };
            return copy;
          });
        },
      );
    } catch (e) {
      setMessages((prev) => {
        const copy = [...prev];
        copy[copy.length - 1] = { role: "assistant", content: `Ошибка: ${(e as Error).message}` };
        return copy;
      });
    } finally {
      setStreaming(false);
    }
  }

  async function newChat() {
    if (!session?.accessToken) return;
    const res = await apiFetch<{ session_id: string }>("/api/chat/sessions", {
      method: "POST",
      token: session.accessToken,
    });
    setSessionId(res.session_id);
    setMessages([]);
  }

  if (status === "loading" || guestLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-500">
        Загрузка чата...
      </div>
    );
  }

  if (!session?.accessToken) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 text-slate-600 px-4">
        <p>{authError || "Сессия не создана"}</p>
        <a href="/auth/login" className="text-primary underline">
          Войти или зарегистрироваться
        </a>
      </div>
    );
  }

  return (
    <AppShell>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">AI-советник</h1>
        <button onClick={newChat} className="text-sm text-primary border border-primary px-3 py-1 rounded-lg">
          Новый чат
        </button>
      </div>

      <div className="bg-white rounded-xl border flex flex-col h-[calc(100vh-12rem)]">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-wrap gap-2">
              {QUICK_PROMPTS.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="text-sm border rounded-full px-4 py-2 hover:bg-slate-50"
                >
                  {q}
                </button>
              ))}
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[80%] p-3 rounded-lg ${
                  m.role === "user" ? "bg-primary text-white" : "bg-slate-100 prose prose-sm"
                }`}
              >
                {m.role === "assistant" ? <ReactMarkdown>{m.content}</ReactMarkdown> : m.content}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage(input);
          }}
          className="border-t p-4 flex gap-2"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Задайте вопрос..."
            className="flex-1 border rounded-lg px-4 py-2"
            disabled={streaming}
          />
          <button type="submit" disabled={streaming || !input.trim()} className="bg-primary text-white px-4 py-2 rounded-lg">
            Отправить
          </button>
        </form>
      </div>
    </AppShell>
  );
}
