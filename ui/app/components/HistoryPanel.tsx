'use client'

import { useEffect, useState } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000'

interface HistorySummary {
  filename: string
  document_file: string
  document_type: string
  date: string
  supplier_name: string
  total_amount: number
  confidence: string
  branch: string
  saved_at: number
}

interface Props {
  refreshKey: number
  onLoad: (filename: string) => void
}

const confidenceColor: Record<string, string> = {
  high:   'bg-green-100 text-green-700',
  medium: 'bg-yellow-100 text-yellow-700',
  low:    'bg-red-100 text-red-700',
}

export default function HistoryPanel({ refreshKey, onLoad }: Props) {
  const [items, setItems] = useState<HistorySummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    fetch(`${API}/api/history`)
      .then(r => r.json())
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false))
  }, [refreshKey])

  const handleDelete = async (e: React.MouseEvent, filename: string) => {
    e.stopPropagation()
    if (!confirm(`Delete ${filename}?`)) return
    await fetch(`${API}/api/history/${filename}`, { method: 'DELETE' })
    setItems(prev => prev.filter(i => i.filename !== filename))
  }

  if (loading) {
    return (
      <div className="text-center py-6 text-sm text-gray-400">
        Loading history…
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="text-center py-6">
        <p className="text-sm text-gray-400 italic">No classified documents yet.</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-1">
        History
        <span className="ml-2 text-gray-300 font-normal normal-case">{items.length} saved</span>
      </h2>

      {items.map(item => (
        <button
          key={item.filename}
          onClick={() => onLoad(item.filename)}
          className="w-full text-left bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-md px-4 py-3 transition-all group"
        >
          <div className="flex items-center justify-between gap-3">
            {/* Left: doc info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-800 truncate">
                  {item.document_file || item.filename}
                </span>
                <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${
                  confidenceColor[item.confidence] || 'bg-gray-100 text-gray-500'
                }`}>
                  {(item.confidence || '').toUpperCase()}
                </span>
              </div>
              <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                {item.date && <span>{item.date}</span>}
                {item.supplier_name && (
                  <span className="truncate max-w-[200px]">{item.supplier_name}</span>
                )}
                {item.branch && <span>{item.branch}</span>}
              </div>
            </div>

            {/* Right: amount + delete */}
            <div className="flex items-center gap-3 shrink-0">
              <span className="text-sm font-mono font-semibold text-gray-700">
                {item.total_amount
                  ? item.total_amount.toLocaleString('el-GR', { minimumFractionDigits: 2 })
                  : '—'}
                <span className="text-xs text-gray-400 font-normal ml-0.5">€</span>
              </span>
              <span
                onClick={e => handleDelete(e, item.filename)}
                title="Delete"
                className="opacity-0 group-hover:opacity-100 text-gray-300 hover:text-red-500 text-sm font-bold cursor-pointer transition-all px-1"
              >
                ×
              </span>
            </div>
          </div>
        </button>
      ))}
    </div>
  )
}
