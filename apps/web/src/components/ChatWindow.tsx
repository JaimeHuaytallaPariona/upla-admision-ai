"use client";

import { useEffect, useRef, useState } from "react";
import { Message } from "./Message";
import { PhaseIndicator } from "./PhaseIndicator";
import { sendChat } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

const INITIAL_QUICK = [
  "Quiero inscribirme",
  "¿Qué modalidades hay?",
  "¿Cuándo es el examen?",
  "Consultar mis resultados",
  "Hablar con un asesor",
];

export function ChatWindow() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [phase, setPhase] = useState("atencion");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      agent: "greeting",
      confidence: 0.99,
      content:
        "¡Hola! Soy el asistente virtual de admisión de la UPLA. Te puedo ayudar a conocer las modalidades, inscribirte, consultar fechas o resultados, o derivarte con un asesor. ¿En qué te puedo ayudar hoy?",
      quick_replies: INITIAL_QUICK,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [quickReplies, setQuickReplies] = useState<string[]>(INITIAL_QUICK);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(text: string) {
    if (!text.trim() || loading) return;
    setInput("");
    setQuickReplies([]);
    setMessages((m) => [...m, { role: "user", content: text }]);
    setLoading(true);
    try {
      const resp = await sendChat({
        session_id: sessionId ?? undefined,
        message: text,
      });
      setSessionId(resp.session_id);
      setPhase(resp.phase);
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: resp.reply,
          agent: resp.agent,
          citations: resp.citations,
          confidence: resp.confidence,
          requires_handoff: resp.requires_handoff,
          phase: resp.phase,
          intent: resp.intent ?? undefined,
        },
      ]);
      setQuickReplies(resp.quick_replies ?? []);
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: `Ups, tuve un problema para conectar con el servidor. ${e?.message ?? ""}`,
          agent: "error",
          confidence: 0,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col bg-slate-50">
      <PhaseIndicator current={phase} />

      <div className="flex-1 overflow-y-auto px-4 py-4">
        <div className="mx-auto max-w-3xl space-y-4">
          {messages.map((m, i) => (
            <Message key={i} msg={m} />
          ))}
          {loading && (
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <span className="typing-dot h-2 w-2 rounded-full bg-slate-400"></span>
              <span className="typing-dot h-2 w-2 rounded-full bg-slate-400"></span>
              <span className="typing-dot h-2 w-2 rounded-full bg-slate-400"></span>
            </div>
          )}
          <div ref={endRef} />
        </div>
      </div>

      {quickReplies.length > 0 && (
        <div className="border-t border-slate-200 bg-white px-4 py-2">
          <div className="mx-auto flex max-w-3xl flex-wrap gap-2">
            {quickReplies.map((q) => (
              <button
                key={q}
                onClick={() => send(q)}
                className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-700 hover:border-upla-blue hover:text-upla-blue"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="border-t border-slate-200 bg-white px-4 py-3"
      >
        <div className="mx-auto flex max-w-3xl items-center gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Escribe tu pregunta…"
            className="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm focus:border-upla-blue focus:outline-none focus:ring-2 focus:ring-upla-blue/20"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="rounded-lg bg-upla-navy px-5 py-2 text-sm font-semibold text-white hover:bg-upla-blue disabled:opacity-50"
          >
            Enviar
          </button>
        </div>
        <div className="mx-auto mt-1 max-w-3xl text-[10px] text-slate-400">
          Sesión: {sessionId ?? "(nueva)"} · Las respuestas citan el Reglamento 311-2025-CU-UPLA.
        </div>
      </form>
    </div>
  );
}
