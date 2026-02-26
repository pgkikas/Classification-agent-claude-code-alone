'use client'

import { useCallback, useRef, useState } from 'react'

interface Props {
  onClassify: (file: File) => void
  loading: boolean
  error?: string | null
}

export default function FileUpload({ onClassify, loading, error }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = useCallback((f: File) => {
    if (!f.name.toLowerCase().endsWith('.pdf')) return
    setFile(f)
  }, [])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }, [handleFile])

  const onDragOver = (e: React.DragEvent) => { e.preventDefault(); setDragging(true) }
  const onDragLeave = () => setDragging(false)

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) handleFile(e.target.files[0])
  }

  const handleClassify = () => {
    if (file && !loading) onClassify(file)
  }

  return (
    <div className="flex flex-col items-center gap-6">
      {/* Drop zone */}
      <div
        onClick={() => inputRef.current?.click()}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        className={`
          w-full max-w-lg border-2 border-dashed rounded-xl p-10 text-center cursor-pointer
          transition-colors duration-150
          ${dragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white hover:border-blue-400 hover:bg-blue-50/30'}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={onInputChange}
        />
        <div className="text-4xl mb-3">📄</div>
        {file ? (
          <div>
            <p className="font-semibold text-blue-700">{file.name}</p>
            <p className="text-sm text-gray-400 mt-1">Click to choose a different file</p>
          </div>
        ) : (
          <div>
            <p className="font-medium text-gray-600">Drop a PDF here or click to browse</p>
            <p className="text-sm text-gray-400 mt-1">Only .pdf files accepted</p>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="w-full max-w-lg bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {/* Classify button */}
      <button
        onClick={handleClassify}
        disabled={!file || loading}
        className={`
          px-8 py-3 rounded-xl font-semibold text-white text-sm tracking-wide transition-all
          ${!file || loading
            ? 'bg-gray-300 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 active:scale-95 shadow-md hover:shadow-lg'}
        `}
      >
        {loading ? (
          <span className="flex items-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            Analysing document…
          </span>
        ) : (
          'Classify →'
        )}
      </button>
    </div>
  )
}
