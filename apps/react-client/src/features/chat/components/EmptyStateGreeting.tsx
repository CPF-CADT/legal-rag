import { ChatInputComposer } from './ChatInputComposer'

interface EmptyStateGreetingProps {
  input: string
  onChange: (value: string) => void
  onSubmit: () => void
  loading: boolean
}

export function EmptyStateGreeting({
  input,
  onChange,
  onSubmit,
  loading,
}: EmptyStateGreetingProps) {
  return (
    <div className="mx-auto flex min-h-[70vh] w-full max-w-2xl flex-col items-center justify-center px-4 py-8 text-center">
      <h1 className="mb-6 text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight text-slate-900">
        តើអ្នកចង់ស្វែងយល់អ្វីអំពីច្បាប់កម្ពុជា?
      </h1>

      <ChatInputComposer
        input={input}
        onChange={onChange}
        onSubmit={onSubmit}
        loading={loading}
        variant="centered"
        autoFocus
        placeholder="សួរសំណួររបស់អ្នកអំពីច្បាប់កម្ពុជា… (ចុច Enter ដើម្បីផ្ញើ)"
      />
    </div>
  )
}
