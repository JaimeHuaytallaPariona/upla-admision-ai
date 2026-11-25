import Link from "next/link";
import { ChatWindow } from "@/components/ChatWindow";

export default function ChatPage() {
  return (
    <div className="h-screen bg-white">
      <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-upla-navy text-sm font-bold text-white">
            U
          </div>
          <div>
            <div className="text-sm font-semibold text-upla-navy">UPLA · Asistente de Admisión</div>
            <div className="text-xs text-slate-500">
              Powered by RAG + Reglamento 311-2025-CU-UPLA
            </div>
          </div>
        </div>
        <Link href="/" className="text-xs text-slate-500 hover:text-upla-blue">
          ← Volver al inicio
        </Link>
      </header>
      <ChatWindow />
    </div>
  );
}
