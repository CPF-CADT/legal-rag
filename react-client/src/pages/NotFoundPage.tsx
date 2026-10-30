import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return <section className="rounded-xl border border-slate-200 bg-white p-10 text-center shadow-sm"><h1 className="text-2xl font-bold">រកមិនឃើញទំព័រ</h1><p className="mt-3 text-slate-600">ទំព័រដែលអ្នកស្នើសុំមិនមានទេ។</p><Link to="/" className="mt-5 inline-block font-semibold text-blue-700">ត្រឡប់ទៅទំព័រដើម</Link></section>
}
