import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-sky-50">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-upla-navy text-white font-bold">
              U
            </div>
            <div>
              <div className="text-sm font-semibold text-upla-navy">
                Universidad Peruana Los Andes
              </div>
              <div className="text-xs text-slate-500">Oficina de Admisión</div>
            </div>
          </div>
          <nav className="flex items-center gap-6 text-sm">
            <Link href="/chat" className="text-slate-700 hover:text-upla-blue">
              Asistente
            </Link>
            <Link href="/panel" className="text-slate-700 hover:text-upla-blue">
              Panel admin
            </Link>
            <a
              href="https://admision.upla.edu.pe"
              className="rounded-md bg-upla-navy px-4 py-2 text-white hover:bg-upla-blue"
            >
              Portal oficial
            </a>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="mx-auto max-w-7xl px-6 py-16">
        <div className="grid gap-12 md:grid-cols-2 md:items-center">
          <div>
            <span className="inline-block rounded-full bg-sky-100 px-3 py-1 text-xs font-semibold text-upla-blue">
              Proceso Ordinario 2027-I · abierto
            </span>
            <h1 className="mt-4 text-5xl font-bold leading-tight text-upla-navy">
              Tu proceso de admisión,{" "}
              <span className="text-upla-blue">resuelto en segundos.</span>
            </h1>
            <p className="mt-6 text-lg text-slate-600">
              Nuestro asistente virtual te acompaña durante toda la admisión: resuelve dudas,
              te inscribe, te muestra las materias de tu canal, consulta tus resultados y
              coordina con un asesor cuando lo necesitas — 24 horas, los 7 días.
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <Link
                href="/chat"
                className="rounded-md bg-upla-navy px-6 py-3 text-white shadow-sm hover:bg-upla-blue"
              >
                Iniciar conversación
              </Link>
              <a
                href="#como-funciona"
                className="rounded-md border border-slate-300 px-6 py-3 text-slate-700 hover:bg-slate-50"
              >
                ¿Cómo funciona?
              </a>
            </div>
            <div className="mt-6 flex items-center gap-4 text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
                Sistema operando
              </span>
              <span>·</span>
              <span>Basado en el Reglamento Res. 311-2025-CU-UPLA</span>
            </div>
          </div>

          <div className="rounded-2xl bg-white p-6 shadow-chat ring-1 ring-slate-200">
            <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
              <div className="h-10 w-10 rounded-full bg-upla-navy text-white grid place-items-center text-sm font-semibold">
                IA
              </div>
              <div>
                <div className="text-sm font-semibold">Asistente UPLA</div>
                <div className="text-xs text-slate-500">En línea · responde al instante</div>
              </div>
            </div>
            <div className="space-y-3 py-4">
              <div className="rounded-lg bg-slate-100 px-4 py-2 text-sm">
                ¡Hola! Soy el asistente de admisión UPLA. ¿En qué te puedo ayudar?
              </div>
              <div className="ml-auto max-w-[80%] rounded-lg bg-upla-navy px-4 py-2 text-sm text-white">
                ¿Cuándo es el examen?
              </div>
              <div className="rounded-lg bg-slate-100 px-4 py-2 text-sm">
                El próximo examen de admisión es el 7 de marzo de 2027, presencial en la sede
                central de Huancayo. ¿Qué carrera estás postulando?{" "}
                <span className="text-xs text-upla-blue">
                  [Art. 20° del Reglamento 311-2025-CU-UPLA]
                </span>
              </div>
            </div>
            <Link
              href="/chat"
              className="block w-full rounded-md bg-upla-gold py-2 text-center text-sm font-semibold text-upla-ink hover:brightness-95"
            >
              Probar el asistente →
            </Link>
          </div>
        </div>
      </section>

      {/* Como funciona */}
      <section id="como-funciona" className="bg-white py-16">
        <div className="mx-auto max-w-7xl px-6">
          <h2 className="mb-10 text-center text-3xl font-bold text-upla-navy">
            El asistente cubre todo el embudo
          </h2>
          <div className="grid gap-6 md:grid-cols-5">
            {[
              { n: "01", t: "Atención", d: "Resuelve dudas sobre modalidades, fechas, pagos y requisitos, citando el Reglamento." },
              { n: "02", t: "Inscripción", d: "Captura tus datos paso a paso y genera tu código de pre-inscripción." },
              { n: "03", t: "Examen", d: "Te muestra las asignaturas y ponderación según el canal de tu carrera." },
              { n: "04", t: "Resultados", d: "Consulta tu puntaje y puesto con tu DNI, en tiempo real." },
              { n: "05", t: "Matrícula", d: "Te orienta sobre los pasos post-ingreso y te deriva a Servicios Académicos." },
            ].map((s) => (
              <div key={s.n} className="rounded-xl border border-slate-200 bg-slate-50 p-5">
                <div className="text-sm font-semibold text-upla-gold">{s.n}</div>
                <div className="mt-2 text-lg font-semibold text-upla-navy">{s.t}</div>
                <p className="mt-2 text-sm text-slate-600">{s.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-upla-navy py-10 text-slate-200">
        <div className="mx-auto max-w-7xl px-6 text-sm">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>© 2026 Universidad Peruana Los Andes · Oficina de Admisión</div>
            <div className="flex gap-6">
              <a href="https://upla.edu.pe">Sitio institucional</a>
              <a href="mailto:admision@upla.edu.pe">admision@upla.edu.pe</a>
              <span>Huancayo · Perú</span>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}
