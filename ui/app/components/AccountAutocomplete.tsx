'use client'

import { useState, useEffect, useRef } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000'

interface Suggestion {
  code: string
  desc: string
  kind: 'account' | 'supplier'
}

interface Props {
  value: string
  onSelect: (code: string, desc: string) => void
  className?: string
}

export default function AccountAutocomplete({ value, onSelect, className }: Props) {
  const [query, setQuery]           = useState(value)
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [open, setOpen]             = useState(false)
  const [activeIdx, setActiveIdx]   = useState(-1)
  const containerRef = useRef<HTMLDivElement>(null)
  const timerRef     = useRef<ReturnType<typeof setTimeout>>()

  // Keep in sync when parent resets value
  useEffect(() => { setQuery(value) }, [value])

  // Debounced search
  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current)
    if (query.length < 2) { setSuggestions([]); setOpen(false); return }
    timerRef.current = setTimeout(async () => {
      try {
        const res  = await fetch(`${API}/api/search?q=${encodeURIComponent(query)}`)
        const data: Suggestion[] = await res.json()
        setSuggestions(data)
        setOpen(data.length > 0)
        setActiveIdx(-1)
      } catch {
        setSuggestions([])
        setOpen(false)
      }
    }, 280)
    return () => { if (timerRef.current) clearTimeout(timerRef.current) }
  }, [query])

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const select = (s: Suggestion) => {
    setQuery(s.code)
    onSelect(s.code, s.desc)
    setOpen(false)
    setSuggestions([])
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!open || suggestions.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIdx(i => Math.min(i + 1, suggestions.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIdx(i => Math.max(i - 1, 0))
    } else if (e.key === 'Enter' && activeIdx >= 0) {
      e.preventDefault()
      select(suggestions[activeIdx])
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <div ref={containerRef} className="relative w-full">
      <input
        type="text"
        value={query}
        onChange={e => {
          setQuery(e.target.value)
          onSelect(e.target.value, '')   // propagate raw typing too
        }}
        onFocus={() => suggestions.length > 0 && setOpen(true)}
        onKeyDown={handleKeyDown}
        spellCheck={false}
        autoComplete="off"
        className={className}
      />

      {open && suggestions.length > 0 && (
        <div className="absolute z-50 left-0 top-full mt-0.5 w-72 bg-white border border-gray-200 rounded-lg shadow-xl overflow-hidden">
          {suggestions.map((s, i) => (
            <button
              key={s.code}
              onMouseDown={e => { e.preventDefault(); select(s) }}
              className={`
                w-full text-left px-3 py-2 flex items-start gap-2
                hover:bg-blue-50 transition-colors border-b border-gray-50 last:border-0
                ${i === activeIdx ? 'bg-blue-50' : ''}
              `}
            >
              <span className={`
                shrink-0 text-[10px] font-bold px-1.5 py-0.5 rounded mt-0.5 uppercase tracking-wide
                ${s.kind === 'supplier'
                  ? 'bg-purple-100 text-purple-700'
                  : 'bg-blue-100 text-blue-700'}
              `}>
                {s.kind === 'supplier' ? 'SUP' : 'ACC'}
              </span>
              <div className="min-w-0">
                <p className="text-xs font-mono text-gray-900 leading-snug">{s.code}</p>
                <p className="text-xs text-gray-500 truncate leading-snug">{s.desc}</p>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
