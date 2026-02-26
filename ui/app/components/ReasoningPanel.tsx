'use client'

interface Props {
  reasoning: string
}

export default function ReasoningPanel({ reasoning }: Props) {
  if (!reasoning) return null

  return (
    <details className="group bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <summary className="flex items-center justify-between px-4 py-3 cursor-pointer select-none bg-gray-50 hover:bg-gray-100 transition-colors">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Agent Reasoning
        </span>
        <svg
          className="h-4 w-4 text-gray-400 group-open:rotate-180 transition-transform"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </summary>
      <div className="px-4 py-4">
        <pre className="text-xs text-gray-600 whitespace-pre-wrap font-mono leading-relaxed">
          {reasoning}
        </pre>
      </div>
    </details>
  )
}
