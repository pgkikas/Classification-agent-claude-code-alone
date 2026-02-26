'use client'

import { useState, useCallback } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000'
import FileUpload from './components/FileUpload'
import ResultHeader from './components/ResultHeader'
import JournalTable from './components/JournalTable'
import ReasoningPanel from './components/ReasoningPanel'
import { ClassificationResult, JournalEntry } from './types'

type PageState = 'idle' | 'classifying' | 'result' | 'saving' | 'saved'

export default function Home() {
  const [pageState, setPageState] = useState<PageState>('idle')
  const [result, setResult] = useState<ClassificationResult | null>(null)
  const [savedPath, setSavedPath] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  // ── Classify ──────────────────────────────────────────────────────────────

  const handleClassify = useCallback(async (file: File) => {
    setPageState('classifying')
    setError(null)
    setResult(null)
    setSavedPath(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const res = await fetch(`${API}/api/classify`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail ?? `Server error ${res.status}`)
      }

      const data: ClassificationResult = await res.json()
      setResult(data)
      setPageState('result')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
      setPageState('idle')
    }
  }, [])

  // ── Edit journal entries ───────────────────────────────────────────────────

  const handleEntriesChange = useCallback((entries: JournalEntry[]) => {
    setResult(prev => prev ? { ...prev, journal_entries: entries } : prev)
  }, [])

  // ── Save ──────────────────────────────────────────────────────────────────

  const handleSave = useCallback(async () => {
    if (!result) return
    setPageState('saving')

    try {
      const res = await fetch(`${API}/api/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(result),
      })

      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail ?? `Save error ${res.status}`)
      }

      const data = await res.json()
      setSavedPath(data.path)
      setPageState('saved')

      // Auto-reset to idle after 3s
      setTimeout(() => {
        setPageState('idle')
        setResult(null)
        setSavedPath(null)
      }, 3000)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
      setPageState('result')
    }
  }, [result])

  // ── Reset ─────────────────────────────────────────────────────────────────

  const handleReset = () => {
    setPageState('idle')
    setResult(null)
    setError(null)
    setSavedPath(null)
  }

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <main className="max-w-4xl mx-auto px-4 py-10">

      {/* Header */}
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">
          PROPORIA Classification Agent
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Upload a PDF — the agent will classify it into accounting journal entries.
        </p>
      </div>

      {/* Saved toast */}
      {pageState === 'saved' && savedPath && (
        <div className="mb-6 flex items-center gap-3 bg-green-50 border border-green-200 text-green-800 rounded-xl px-5 py-4 shadow-sm">
          <span className="text-xl">✓</span>
          <div>
            <p className="font-semibold">Saved successfully</p>
            <p className="text-sm text-green-600 font-mono mt-0.5 break-all">{savedPath}</p>
          </div>
        </div>
      )}

      {/* Upload (always visible when idle/classifying, or as reset option) */}
      {(pageState === 'idle' || pageState === 'classifying') && (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8">
          <FileUpload
            onClassify={handleClassify}
            loading={pageState === 'classifying'}
            error={error}
          />
        </div>
      )}

      {/* Results */}
      {result && (pageState === 'result' || pageState === 'saving' || pageState === 'saved') && (
        <div className="space-y-5">

          {/* Top bar with "Classify another" */}
          <div className="flex items-center justify-between">
            <button
              onClick={handleReset}
              className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
            >
              ← Classify another document
            </button>
            <span className="text-xs text-gray-400">{result.document_file}</span>
          </div>

          {/* Metadata */}
          <ResultHeader result={result} />

          {/* Journal entries (editable) */}
          <div>
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
              Journal Entries
              <span className="ml-2 text-xs font-normal normal-case text-gray-400">
                — edit cells as needed before confirming
              </span>
            </h2>
            <JournalTable
              entries={result.journal_entries}
              onChange={handleEntriesChange}
            />
          </div>

          {/* Reasoning */}
          <ReasoningPanel reasoning={result.reasoning} />

          {/* Confirm button */}
          {(pageState === 'result' || pageState === 'saving') && (
            <div className="flex justify-end pt-2">
              <button
                onClick={handleSave}
                disabled={pageState === 'saving'}
                className={`
                  px-8 py-3 rounded-xl font-semibold text-white text-sm tracking-wide transition-all shadow-md
                  ${pageState === 'saving'
                    ? 'bg-gray-300 cursor-not-allowed'
                    : 'bg-emerald-600 hover:bg-emerald-700 active:scale-95 hover:shadow-lg'}
                `}
              >
                {pageState === 'saving' ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                    </svg>
                    Saving…
                  </span>
                ) : (
                  'Confirm & Save ✓'
                )}
              </button>
            </div>
          )}
        </div>
      )}
    </main>
  )
}
