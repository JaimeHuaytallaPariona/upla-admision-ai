import type { ChatResponse, PanelMetrics } from "./types";

const API_BASE = "http://localhost:8000/api/v1";

async function handle<T>(r: Response): Promise<T> {
  if (!r.ok) {
    const txt = await r.text();
    throw new Error(`API ${r.status}: ${txt.slice(0, 200)}`);
  }
  return r.json();
}

export async function sendChat(params: {
  session_id?: string;
  message: string;
  channel?: "web" | "whatsapp";
  dni?: string;
}): Promise<ChatResponse> {
  const r = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: params.session_id ?? null,
      message: params.message,
      channel: params.channel ?? "web",
      dni: params.dni ?? null,
    }),
  });
  return handle<ChatResponse>(r);
}

export async function getMetrics(): Promise<PanelMetrics> {
  return handle<PanelMetrics>(await fetch(`${API_BASE}/admin/metrics`, { cache: "no-store" }));
}

export async function getObservations(): Promise<Array<{
  id: string; session_id: string; query: string; reason: string; status: string; created_at: string;
}>> {
  return handle(await fetch(`${API_BASE}/admin/observations?status=pending`, { cache: "no-store" }));
}

export async function getInscripciones(): Promise<Array<{
  codigo: string; dni: string; nombres: string; email: string; modalidad: string; carrera: string;
  canal: string; estado: string; created_at: string;
}>> {
  return handle(await fetch(`${API_BASE}/admin/inscripciones`, { cache: "no-store" }));
}

export async function getSessions(): Promise<Array<{
  id: string; channel: string; identity_level: string; current_phase: string;
  current_intent: string | null; message_count: number; created_at: string; updated_at: string;
}>> {
  return handle(await fetch(`${API_BASE}/admin/sessions`, { cache: "no-store" }));
}

export async function getInfo(): Promise<{
  app: string; version: string; env: string; llm_provider: string; llm_model: string;
  embedding_model: string; db_ok: boolean; kb_chunks: number;
}> {
  return handle(await fetch(`${API_BASE}/info`, { cache: "no-store" }));
}
