'use client'

import { useState } from 'react'

interface ToolCall {
  name: string
  args: Record<string, any>
  result: string
}

interface LogStep {
  step: number
  reasoning: string | null
  tool_calls: ToolCall[]
  tokens: { prompt: number; completion: number; total: number }
}

interface Props {
  log: LogStep[]
}

export default function AgentLogPanel({ log }: Props) {
  const [open, setOpen] = useState(false)

  if (!log || log.length === 0) return null

  const totalTokens = log.reduce((s, step) => s + (step.tokens?.total || 0), 0)
  const totalToolCalls = log.reduce((s, step) => s + step.tool_calls.length, 0)

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-3 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className={`text-xs text-gray-400 transition-transform ${open ? 'rotate-90' : ''}`}>
            ▶
          </span>
          <span className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
            Agent Trace
          </span>
          <span className="text-xs text-gray-400 font-normal normal-case">
            {log.length} steps, {totalToolCalls} tool calls, {totalTokens.toLocaleString()} tokens
          </span>
        </div>
      </button>

      {open && (
        <div className="border-t border-gray-100 px-5 py-4 space-y-4 max-h-[600px] overflow-y-auto">
          {log.map((step, i) => (
            <div key={i} className="relative pl-6 border-l-2 border-gray-200">
              {/* Step number */}
              <div className="absolute -left-[11px] top-0 w-5 h-5 rounded-full bg-white border-2 border-gray-300 flex items-center justify-center">
                <span className="text-[9px] font-bold text-gray-400">{step.step}</span>
              </div>

              {/* Reasoning */}
              {step.reasoning && (
                <div className="mb-2">
                  <pre className="text-xs text-gray-600 whitespace-pre-wrap font-sans leading-relaxed">
                    {step.reasoning}
                  </pre>
                </div>
              )}

              {/* Tool calls */}
              {step.tool_calls.map((tc, j) => (
                <div key={j} className="mb-2 bg-gray-50 rounded-lg border border-gray-100 overflow-hidden">
                  <div className="px-3 py-1.5 flex items-center gap-2 border-b border-gray-100">
                    <span className="text-[10px] font-semibold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">
                      TOOL
                    </span>
                    <span className="text-xs font-mono font-semibold text-gray-700">
                      {tc.name}
                    </span>
                    <span className="text-[10px] text-gray-400 font-mono">
                      ({Object.entries(tc.args).map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(', ')})
                    </span>
                  </div>
                  <div className="px-3 py-1.5">
                    <pre className="text-[11px] text-gray-500 whitespace-pre-wrap font-mono leading-relaxed break-all">
                      {tc.result}
                    </pre>
                  </div>
                </div>
              ))}

              {/* Tokens */}
              <div className="text-[10px] text-gray-300 mt-1">
                {step.tokens.total.toLocaleString()} tokens
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
