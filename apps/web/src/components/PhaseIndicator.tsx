"use client";

const PHASES = [
  { id: "atencion", label: "Atención" },
  { id: "inscripcion", label: "Inscripción" },
  { id: "examen", label: "Examen" },
  { id: "resultados", label: "Resultados" },
  { id: "matricula", label: "Matrícula" },
];

export function PhaseIndicator({ current }: { current: string }) {
  const currentIdx = PHASES.findIndex((p) => p.id === current);
  return (
    <div className="flex items-center gap-2 overflow-x-auto px-6 py-3">
      {PHASES.map((p, i) => {
        const active = i === currentIdx;
        const past = i < currentIdx;
        return (
          <div key={p.id} className="flex items-center gap-2 flex-shrink-0">
            <div
              className={`grid h-7 w-7 place-items-center rounded-full text-xs font-semibold ${
                active
                  ? "bg-upla-navy text-white ring-4 ring-upla-blue/20"
                  : past
                  ? "bg-emerald-500 text-white"
                  : "bg-slate-200 text-slate-500"
              }`}
            >
              {past ? "✓" : i + 1}
            </div>
            <span
              className={`text-xs ${active ? "font-semibold text-upla-navy" : "text-slate-500"}`}
            >
              {p.label}
            </span>
            {i < PHASES.length - 1 && <span className="mx-1 text-slate-300">›</span>}
          </div>
        );
      })}
    </div>
  );
}
