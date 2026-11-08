import { useState } from 'react'
import type { UIMessage } from '../../../types'
import { IconCheck, IconCopy, IconSparkles } from '../../../components/common/Icons'
import { CitationDrawer } from './CitationDrawer'
import { MarkdownText } from './MarkdownText'

interface ChatMessageItemProps {
  message: UIMessage
}

export function ChatMessageItem({ message }: ChatMessageItemProps) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'user'

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // ignore clipboard error
    }
  }

  if (isUser) {
    return (
      <div className="flex justify-end py-2">
        <div className="max-w-[85%] sm:max-w-[75%] rounded-3xl bg-slate-100 px-4 py-3 text-slate-900 shadow-sm">
          <p className="khmer-text whitespace-pre-wrap text-sm sm:text-base leading-7">
            {message.content}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-3 sm:gap-4 py-4 text-slate-900">
      <div className="grid h-8 w-8 sm:h-9 sm:w-9 shrink-0 place-items-center rounded-full bg-blue-600 text-white shadow-sm">
        <IconSparkles className="h-4 w-4" />
      </div>

      <div className="min-w-0 flex-1 space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs sm:text-sm font-semibold text-slate-900">ធីតា</span>
          <span className="text-[11px] font-medium text-slate-400">ជំនួយការច្បាប់</span>
        </div>

        {message.hasSufficientEvidence === false && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs sm:text-sm text-amber-900">
            <p className="font-semibold">មិនអាចផ្តល់ចម្លើយដែលមានមូលដ្ឋានគ្រប់គ្រាន់</p>
            {message.insufficientEvidenceMessage && (
              <p className="mt-1 opacity-90">{message.insufficientEvidenceMessage}</p>
            )}
          </div>
        )}

        <div className="khmer-text text-sm sm:text-base leading-7 sm:leading-8 text-slate-800">
          <MarkdownText>{message.content}</MarkdownText>
        </div>

        {message.sources && message.sources.length > 0 && (
          <CitationDrawer sources={message.sources} />
        )}

        <div className="flex items-center gap-2 pt-1">
          <button
            type="button"
            onClick={handleCopy}
            className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-slate-500 hover:bg-slate-100 hover:text-slate-800 transition-colors"
            title="ចម្លងអត្ថបទ"
          >
            {copied ? (
              <>
                <IconCheck className="h-3.5 w-3.5 text-emerald-600" />
                <span className="text-emerald-600 font-medium">បានចម្លង</span>
              </>
            ) : (
              <>
                <IconCopy className="h-3.5 w-3.5" />
                <span>ចម្លង</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

