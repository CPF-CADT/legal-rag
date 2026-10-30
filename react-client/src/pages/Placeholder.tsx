export function Placeholder({ title, description }: { title: string; description: string }) {
  return (
    <section className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-sm">
      <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
      <p className="mt-3 text-slate-600">{description}</p>
    </section>
  )
}
