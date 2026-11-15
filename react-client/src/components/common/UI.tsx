import { isDemo } from "../../services/api";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import type { Citation, SearchMode } from "../../types";

export function Button({
  children,
  type = "button",
  variant = "primary",
  disabled,
  onClick,
}: {
  children: ReactNode;
  type?: "button" | "submit";
  variant?: "primary" | "secondary" | "ghost";
  disabled?: boolean;
  onClick?: () => void;
}) {
  const styles = {
    primary: "bg-blue-600 text-white hover:bg-blue-700",
    secondary:
      "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50",
    ghost: "text-slate-600 hover:bg-slate-100",
  };
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`rounded-lg px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant]}`}
    >
      {children}
    </button>
  );
}

export function ModeSelector({
  value,
  onChange,
}: {
  value: SearchMode;
  onChange: (mode: SearchMode) => void;
}) {
  const modes: { value: SearchMode; label: string }[] = [
    { value: "keyword", label: "ពាក្យគន្លឹះ" },
    { value: "semantic", label: "ស្វែងរកន័យ" },
    { value: "exact_article", label: "មាត្រាជាក់លាក់" },
  ];
  return (
    <div className="flex flex-wrap gap-2" aria-label="Search mode">
      {modes.map((mode) => (
        <button
          key={mode.value}
          type="button"
          aria-pressed={value === mode.value}
          onClick={() => onChange(mode.value)}
          className={`rounded-full border px-3 py-1.5 text-sm ${value === mode.value ? "border-blue-700 bg-blue-50 text-blue-700" : "border-slate-200 bg-white text-slate-600 hover:border-blue-300"}`}
        >
          {mode.label}
        </button>
      ))}
    </div>
  );
}

export function StatePanel({
  title,
  description,
  tone = "neutral",
}: {
  title: string;
  description?: string;
  tone?: "neutral" | "error" | "warning";
}) {
  const colors =
    tone === "error"
      ? "border-red-200 bg-red-50 text-red-900"
      : tone === "warning"
        ? "border-amber-200 bg-amber-50 text-amber-900"
        : "border-slate-200 bg-white text-slate-700";
  return (
    <div
      className={`rounded-xl border p-8 text-center ${colors}`}
      role="status"
    >
      <p className="font-semibold">{title}</p>
      {description && <p className="mt-2 text-sm opacity-80">{description}</p>}
    </div>
  );
}

export function LoadingPanel() {
  return <StatePanel title="កំពុងស្វែងរក…" description="សូមរង់ចាំបន្តិច។" />;
}

export function PdfLink({
  url,
  label = "បើក PDF ដើម",
}: {
  url: string | null;
  label?: string;
}) {
  let valid = false;
  try {
    valid = Boolean(url && ["http:", "https:"].includes(new URL(url).protocol));
  } catch {
    valid = false;
  }
  if (!valid)
    return <span className="text-sm text-slate-400">តំណប្រភពមិនអាចប្រើបាន</span>;
  return (
    <a
      href={url || undefined}
      target="_blank"
      rel="noreferrer"
      className="inline-flex items-center gap-1 text-sm font-semibold text-blue-700 hover:text-blue-900"
    >
      ↗ {label}
    </a>
  );
}

function pdfDisplayName(url: string | null) {
  if (!url) return "Original PDF";
  try {
    const basename = decodeURIComponent(
      new URL(url).pathname.split("/").filter(Boolean).pop() ?? "",
    );
    return !basename || basename.toLowerCase() === "download"
      ? "Original PDF"
      : basename;
  } catch {
    return "Original PDF";
  }
}

export function SourceCard({
  source,
  compact = false,
}: {
  source: Citation;
  compact?: boolean;
}) {
  if (compact)
    return (
      <article className="min-w-0 rounded-xl border border-slate-200 bg-white p-3 sm:p-4">
        <div className="flex min-w-0 items-center gap-3">
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-slate-100 text-xs font-bold text-slate-600">
            ↗
          </span>
          <p className="min-w-0 break-words text-sm font-semibold text-slate-900">
            {source.title}
          </p>
        </div>
        <div className="mt-3 pl-11">
          <PdfLink url={source.pdfUrl} label={pdfDisplayName(source.pdfUrl)} />
        </div>
      </article>
    );

  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">
            ប្រភពយោង
          </p>
          <h3 className="mt-1 font-semibold text-slate-900">{source.title}</h3>
        </div>
        {source.score != null && (
          <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
            ភាពពាក់ព័ន្ធ {Math.round(source.score * 100)}%
          </span>
        )}
      </div>
      <p className="mt-3 text-sm text-slate-600">
        មាត្រា {source.articleNumber ?? "—"}
        {source.chapterTitle ? ` · ${source.chapterTitle}` : ""}
        {source.sectionTitle ? ` · ${source.sectionTitle}` : ""}
      </p>
      <p className="mt-3 text-xs text-slate-500">
        {isDemo ? "ទិន្នន័យគំរូ · " : ""}
        {source.reviewRequired
          ? "ត្រូវពិនិត្យប្រភពឡើងវិញ"
          : "ស្ថានភាពផ្ទៀងផ្ទាត់៖ មិនទាន់បានផ្ទៀងផ្ទាត់"}{" "}
        · កាលបរិច្ឆេទផ្ទៀងផ្ទាត់៖ មិនមាន
      </p>
      <p className="mt-2 text-xs text-slate-500">
        ប្រភព៖ {isDemo ? "សំណុំទិន្នន័យគំរូ" : "ទិន្នន័យ API"} · កាលបរិច្ឆេទចេញផ្សាយ៖{" "}
        {source.issuedDate ?? "មិនមាន"} ·{" "}
        {source.recordType === "preamble" ? "បុព្វកថា" : "មាត្រា"}
      </p>
      {source.reviewReason && (
        <p className="text-sm text-amber-800">{source.reviewReason}</p>
      )}
      {source.excerpt && (
        <p className="khmer-text mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">
          {source.excerpt}
        </p>
      )}
      <div className="mt-4 flex flex-wrap gap-4">
        {source.articleNumber != null && (
          <Link
            to={`/articles/${encodeURIComponent(source.documentId)}/${encodeURIComponent(source.articleNumber)}`}
            className="text-sm font-semibold text-blue-700 hover:text-blue-900"
          >
            អានអត្ថបទ →
          </Link>
        )}
        <PdfLink url={source.pdfUrl} />
      </div>
    </article>
  );
}
