"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  getInfo,
  getInscripciones,
  getMetrics,
  getObservations,
  getSessions,
} from "@/lib/api";
import type { PanelMetrics } from "@/lib/types";

export default function PanelPage() {
  const [metrics, setMetrics] = useState<PanelMetrics | null>(null);
  const [info, setInfo] = useState<any>(null);
  const [obs, setObs] = useState<any[]>([]);
  const [inscs, setInscs] = useState<any[]>([]);
  const [sess, setSess] = useState<any[]>([]);
  const [tab, setTab] = useState<"obs" | "inscs" | "sess">("obs");
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    try {
      const [m, i, o, is, ss] = await Promise.all([
        getMetrics(),
        getInfo(),
        getObservations(),
        getInscripciones(),
        getSessions(),
      ]);
      setMetrics(m);
      setInfo(i);
      setObs(o);
      setInscs(is);
      setSess(ss);
      setErr(null);
    } catch (e: any) {
      setErr(e?.message ?? "Error cargando panel");
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <div className="text-sm font-semibold text-upla-navy">
              Panel Administrativo · Asistente UPLA
            </div>
            <div className="text-xs text-slate-500">
              Oficina de Admisión · monitoreo en vivo (actualiza cada 10s)
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs">
            {info && (
              <>
                <span className="rounded bg-slate-100 px-2 py-1 font-mono">
                  v{info.version}
                </span>
                <span className="rounded bg-slate-100 px-2 py-1 font-mono">
                  {info.llm_provider}:{info.llm_model}
                </span>
                <span className="rounded bg-slate-100 px-2 py-1 font-mono">
                  {info.kb_chunks} chunks
                </span>
              </>
            )}
            <Link href="/" className="text-slate-500 hover:text-upla-blue">
              ← Volver
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        {err && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {err}
          </div>
        )}

        {/* KPI cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <Kpi label="Sesiones totales" value={metrics?.sessions_total ?? 0} />
          <Kpi label="Sesiones hoy" value={metrics?.sessions_today ?? 0} />
          <Kpi label="Mensajes procesados" value={metrics?.messages_total ?? 0} />
          <Kpi
            label="Confianza promedio"
            value={`${((metrics?.avg_confidence ?? 0) * 100).toFixed(1)}%`}
          />
          <Kpi label="Inscripciones iniciadas" value={metrics?.inscripciones_iniciadas ?? 0} />
          <Kpi
            label="Inscripciones confirmadas"
            value={metrics?.inscripciones_confirmadas ?? 0}
          />
          <Kpi
            label="Observaciones pendientes"
            value={metrics?.observations_pending ?? 0}
            accent={(metrics?.observations_pending ?? 0) > 0 ? "amber" : "default"}
          />
          <Kpi
            label="Top intent"
            value={metrics?.top_intents?.[0]?.intent ?? "—"}
          />
        </div>

        {/* Tabs */}
        <div className="mt-8 flex items-center gap-2 border-b border-slate-200">
          <Tab active={tab === "obs"} onClick={() => setTab("obs")}>
            Observaciones ({obs.length})
          </Tab>
          <Tab active={tab === "inscs"} onClick={() => setTab("inscs")}>
            Inscripciones ({inscs.length})
          </Tab>
          <Tab active={tab === "sess"} onClick={() => setTab("sess")}>
            Sesiones ({sess.length})
          </Tab>
        </div>

        <div className="mt-6 rounded-lg bg-white shadow-sm ring-1 ring-slate-200">
          {tab === "obs" && <ObservationsTable rows={obs} />}
          {tab === "inscs" && <InscripcionesTable rows={inscs} />}
          {tab === "sess" && <SessionsTable rows={sess} />}
        </div>
      </main>
    </div>
  );
}

function Kpi({
  label, value, accent = "default",
}: {
  label: string; value: string | number; accent?: "default" | "amber";
}) {
  const bg = accent === "amber" ? "bg-amber-50 ring-amber-200" : "bg-white ring-slate-200";
  const text = accent === "amber" ? "text-amber-700" : "text-upla-navy";
  return (
    <div className={`rounded-lg ${bg} p-4 shadow-sm ring-1`}>
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`mt-1 text-2xl font-bold ${text}`}>{value}</div>
    </div>
  );
}

function Tab({
  active, onClick, children,
}: {
  active: boolean; onClick: () => void; children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm ${
        active
          ? "border-b-2 border-upla-navy font-semibold text-upla-navy"
          : "text-slate-500 hover:text-upla-blue"
      }`}
    >
      {children}
    </button>
  );
}

function ObservationsTable({ rows }: { rows: any[] }) {
  if (rows.length === 0)
    return <div className="p-6 text-sm text-slate-500">Sin observaciones pendientes 🎉</div>;
  return (
    <table className="w-full text-sm">
      <thead className="border-b border-slate-200 text-left text-xs text-slate-500">
        <tr>
          <th className="px-4 py-2">Fecha</th>
          <th className="px-4 py-2">Consulta</th>
          <th className="px-4 py-2">Razón</th>
          <th className="px-4 py-2">Sesión</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.id} className="border-b border-slate-100">
            <td className="px-4 py-2 text-xs text-slate-500">
              {new Date(r.created_at).toLocaleString("es-PE")}
            </td>
            <td className="px-4 py-2">{r.query}</td>
            <td className="px-4 py-2">
              <span className="rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-700">
                {r.reason}
              </span>
            </td>
            <td className="px-4 py-2 font-mono text-xs text-slate-500">
              {r.session_id.slice(0, 8)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function InscripcionesTable({ rows }: { rows: any[] }) {
  if (rows.length === 0)
    return <div className="p-6 text-sm text-slate-500">Aún no se han iniciado inscripciones.</div>;
  return (
    <table className="w-full text-sm">
      <thead className="border-b border-slate-200 text-left text-xs text-slate-500">
        <tr>
          <th className="px-4 py-2">Código</th>
          <th className="px-4 py-2">DNI</th>
          <th className="px-4 py-2">Postulante</th>
          <th className="px-4 py-2">Modalidad</th>
          <th className="px-4 py-2">Carrera</th>
          <th className="px-4 py-2">Canal</th>
          <th className="px-4 py-2">Estado</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.codigo} className="border-b border-slate-100">
            <td className="px-4 py-2 font-mono text-xs">{r.codigo}</td>
            <td className="px-4 py-2">{r.dni}</td>
            <td className="px-4 py-2">{r.nombres}</td>
            <td className="px-4 py-2">{r.modalidad}</td>
            <td className="px-4 py-2">{r.carrera}</td>
            <td className="px-4 py-2">{r.canal}</td>
            <td className="px-4 py-2">
              <span className="rounded bg-sky-100 px-2 py-0.5 text-xs text-upla-blue">
                {r.estado}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function SessionsTable({ rows }: { rows: any[] }) {
  if (rows.length === 0)
    return <div className="p-6 text-sm text-slate-500">Sin sesiones aún.</div>;
  return (
    <table className="w-full text-sm">
      <thead className="border-b border-slate-200 text-left text-xs text-slate-500">
        <tr>
          <th className="px-4 py-2">Sesión</th>
          <th className="px-4 py-2">Canal</th>
          <th className="px-4 py-2">Identidad</th>
          <th className="px-4 py-2">Fase</th>
          <th className="px-4 py-2">Intent</th>
          <th className="px-4 py-2">Mensajes</th>
          <th className="px-4 py-2">Actualizado</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.id} className="border-b border-slate-100">
            <td className="px-4 py-2 font-mono text-xs text-slate-500">{r.id.slice(0, 8)}</td>
            <td className="px-4 py-2">{r.channel}</td>
            <td className="px-4 py-2 text-xs">{r.identity_level}</td>
            <td className="px-4 py-2">
              <span className="rounded bg-slate-100 px-2 py-0.5 text-xs">{r.current_phase}</span>
            </td>
            <td className="px-4 py-2 text-xs text-slate-500">{r.current_intent ?? "—"}</td>
            <td className="px-4 py-2 text-center">{r.message_count}</td>
            <td className="px-4 py-2 text-xs text-slate-500">
              {new Date(r.updated_at).toLocaleString("es-PE")}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
