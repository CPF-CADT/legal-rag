import { Link } from 'react-router-dom'

export function HomePage() {
  return (
    <section className="mx-auto max-w-3xl py-12 text-center">
      <p className="mb-3 text-sm font-semibold uppercase tracking-wide text-blue-700">Khmer Legal AI</p>
      <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">ស្វែងរកច្បាប់ ឬសួរសំណួរអំពីច្បាប់</h1>
      <p className="mx-auto mt-4 max-w-2xl text-slate-600">ស្វែងរកឯកសារច្បាប់កម្ពុជាដោយមានប្រភពយោង និងតំណទាញយក PDF ដើម។</p>
      <div className="mt-8 flex flex-wrap justify-center gap-3">
        <Link to="/search" className="rounded-lg bg-blue-700 px-5 py-3 font-semibold text-white hover:bg-blue-800">ចាប់ផ្តើមស្វែងរក</Link>
        <Link to="/chat" className="rounded-lg border border-slate-300 bg-white px-5 py-3 font-semibold text-slate-700 hover:bg-slate-50">សួរសំណួរ</Link>
      </div>
      <p className="mt-10 text-sm text-slate-500">ប្រព័ន្ធនេះផ្តល់ព័ត៌មានប៉ុណ្ណោះ មិនមែនជាដំបូន្មានផ្នែកច្បាប់ទេ។</p>
    </section>
  )
}
