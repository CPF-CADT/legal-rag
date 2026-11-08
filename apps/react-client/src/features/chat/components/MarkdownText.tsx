import type { ReactNode } from 'react'

function renderInline(value: string): ReactNode[] {
  const parts = value.split(/(\*\*.+?\*\*|__.+?__|`.+?`|\*.+?\*|_.+?_)/g)

  return parts.map((part, index) => {
    if (!part) return null
    if ((part.startsWith('**') && part.endsWith('**')) || (part.startsWith('__') && part.endsWith('__'))) {
      return <strong key={index}>{part.slice(2, -2)}</strong>
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={index} className="rounded bg-slate-100 px-1 py-0.5 text-[0.9em]">{part.slice(1, -1)}</code>
    }
    if ((part.startsWith('*') && part.endsWith('*')) || (part.startsWith('_') && part.endsWith('_'))) {
      return <em key={index}>{part.slice(1, -1)}</em>
    }
    return <span key={index}>{part}</span>
  })
}

export function MarkdownText({ children }: { children: string }) {
  return (
    <div className="space-y-3">
      {children.split('\n').map((line, index) => {
        const trimmed = line.trim()
        if (!trimmed) return <div key={index} className="h-1" />

        const heading = trimmed.match(/^#{1,6}\s+(.+)$/)
        if (heading) {
          return <p key={index} className="font-semibold text-slate-900">{renderInline(heading[1])}</p>
        }

        const bullet = trimmed.match(/^[+-]\s+(.+)$/)
        return (
          <p key={index}>
            {bullet && <span className="mr-2">•</span>}
            {renderInline(bullet ? bullet[1] : trimmed)}
          </p>
        )
      })}
    </div>
  )
}
