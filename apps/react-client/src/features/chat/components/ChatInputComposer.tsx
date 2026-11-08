import { useEffect, useRef, type ChangeEvent, type KeyboardEvent } from 'react'
import { IconMic, IconPlus, IconUpArrow } from '../../../components/common/Icons'

interface ChatInputComposerProps {
  input: string
  onChange: (value: string) => void
  onSubmit: () => void
  loading: boolean
  placeholder?: string
  mode?: 'general' | 'exact_article'
  onModeChange?: (mode: 'general' | 'exact_article') => void
  variant?: 'centered' | 'bottom'
  autoFocus?: boolean
}

export function ChatInputComposer({
  input,
  onChange,
  onSubmit,
  loading,
  placeholder = 'សួរសំណួររបស់អ្នកអំពីច្បាប់កម្ពុជា…',
  mode = 'general',
  onModeChange,
  variant = 'bottom',
  autoFocus = false,
}: ChatInputComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-focus on mount if requested
  useEffect(() => {
    if (autoFocus) {
      textareaRef.current?.focus()
    }
  }, [autoFocus])

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    const newHeight = Math.min(el.scrollHeight, variant === 'centered' ? 140 : 180)
    el.style.height = `${newHeight}px`
  }, [input, variant])

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (!loading && input.trim()) {
        onSubmit()
      }
    }
  }

  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value)
  }

  const canSubmit = !loading && input.trim().length > 0
  const isCentered = variant === 'centered'

  return (
    <div className={`w-full transition-all ${isCentered ? 'max-w-2xl mx-auto' : 'max-w-3xl mx-auto px-4'}`}>
      <div
        className={`relative flex flex-col rounded-3xl border border-slate-200/90 bg-white transition-all ${
          isCentered
            ? 'shadow-lg hover:border-slate-300 focus-within:border-slate-400 focus-within:ring-4 focus-within:ring-slate-100/80 p-3 sm:p-4'
            : 'shadow-xs border-slate-300 focus-within:border-slate-400 focus-within:ring-2 focus-within:ring-slate-100 p-2 sm:p-2.5'
        }`}
      >
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={isCentered ? 2 : 1}
          className={`chat-scrollbar w-full resize-none border-0 bg-transparent px-2 sm:px-3 text-sm sm:text-base text-slate-900 outline-none placeholder:text-slate-400 leading-relaxed ${
            isCentered ? 'min-h-[56px] max-h-36' : 'min-h-[44px] max-h-44'
          }`}
          aria-label="សួរសំណួររបស់អ្នក"
        />

        {/* Bottom controls inside the composer dock (matching ChatGPT & Fresh AI) */}
        <div className="mt-2 flex items-center justify-between border-t border-slate-100/80 pt-2 px-1">
          {/* Left tools: Mode selector pills */}
          <div className="flex items-center gap-1.5">
            <span className="hidden sm:inline-flex items-center justify-center h-7 w-7 rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors cursor-pointer" title="ជម្រើសបន្ថែម">
              <IconPlus className="h-4 w-4" />
            </span>

            {onModeChange && (
              <div className="flex items-center gap-1 rounded-full bg-slate-100/90 p-0.5">
                <button
                  type="button"
                  onClick={() => onModeChange('general')}
                  className={`rounded-full px-2.5 py-1 text-xs font-medium transition-all ${
                    mode === 'general'
                      ? 'bg-white text-blue-700 shadow-xs'
                      : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  ឆ្លើយសង្ខេប
                </button>
                <button
                  type="button"
                  onClick={() => onModeChange('exact_article')}
                  className={`rounded-full px-2.5 py-1 text-xs font-medium transition-all ${
                    mode === 'exact_article'
                      ? 'bg-white text-blue-700 shadow-xs'
                      : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  មាត្រាជាក់លាក់
                </button>
              </div>
            )}
          </div>

          {/* Right tools: Voice & Submit */}
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              className="inline-flex h-8 w-8 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
              title="បញ្ចូលជាសំឡេង (មិនទាន់ដំណើរការ)"
              aria-label="សំឡេង"
            >
              <IconMic className="h-4 w-4" />
            </button>

            <button
              type="button"
              onClick={onSubmit}
              disabled={!canSubmit}
              className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full transition-all ${
                canSubmit
                  ? 'bg-slate-900 text-white hover:bg-slate-800'
                  : 'bg-slate-100 text-slate-300 cursor-not-allowed'
              }`}
              title="ផ្ញើសំណួរ"
              aria-label="ផ្ញើសំណួរ"
            >
              <IconUpArrow className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <p className="mt-2 text-center text-[11px] text-slate-400">
        ធីតាអាចមានការខុសឆ្គង។ សូមផ្ទៀងផ្ទាត់ជាមួយឯកសារផ្លូវការជានិច្ច។
      </p>
    </div>
  )
}
