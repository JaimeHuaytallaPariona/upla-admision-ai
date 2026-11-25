export type Citation = {
  source: string;
  article?: string | null;
  citation: string;
  chunk_id?: string | null;
};

export type ChatMessage = {
  id?: string;
  role: "user" | "assistant" | "system";
  content: string;
  agent?: string;
  citations?: Citation[];
  confidence?: number;
  quick_replies?: string[];
  requires_handoff?: boolean;
  phase?: string;
  intent?: string;
};

export type ChatResponse = {
  session_id: string;
  reply: string;
  citations: Citation[];
  agent: string;
  phase: string;
  intent: string | null;
  confidence: number;
  requires_handoff: boolean;
  quick_replies: string[];
};

export type PanelMetrics = {
  sessions_total: number;
  sessions_today: number;
  messages_total: number;
  observations_pending: number;
  inscripciones_iniciadas: number;
  inscripciones_confirmadas: number;
  avg_confidence: number;
  top_intents: Array<{ intent: string; count: number }>;
};
