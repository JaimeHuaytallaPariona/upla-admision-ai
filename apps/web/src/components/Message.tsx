"use client";

import ReactMarkdown from "react-markdown";
import type { ChatMessage } from "@/lib/types";

export function Message({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="mr-3 mt-1 grid h-8 w-8 flex-shrink-0 place-items-center rounded-full bg-upla-navy text-xs font-semibold text-white">
          IA
        </div>
      )}
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 shadow-sm ${
          isUser
            ? "rounded-tr-sm bg-upla-navy text-white"
            : "rounded-tl-sm bg-white ring-1 ring-slate-200"
        }`}
      >
        <div className={`prose-chat text-sm ${isUser ? "text-white" : "text-slate-800"}`}>
          <ReactMarkdown>{msg.content}</ReactMarkdown>
        </div>

        {msg.citations && msg.citations.length > 0 && (
          <div className="mt-3 border-t border-slate-100 pt-2 text-xs">
            <div className="mb-1 font-semibold text-slate-500">Fuentes:</div>
            <ul className="space-y-1">
              {msg.citations.map((c, i) => (
                <li key={i} className="text-upla-blue">
                  • {c.citation}
                </li>
              ))}
            </ul>
          </div>
        )}

        {!isUser && msg.agent && (
          <div className="mt-2 flex items-center gap-2 text-[10px] text-slate-400">
            <span className="rounded bg-slate-100 px-1.5 py-0.5 font-mono">{msg.agent}</span>
            {msg.confidence !== undefined && (
              <span>
                conf: {(msg.confidence * 100).toFixed(0)}%
              </span>
            )}
            {msg.requires_handoff && (
              <span className="rounded bg-amber-100 px-1.5 py-0.5 text-amber-700">
                → humano
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
