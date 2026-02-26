'use client'

import type { ReactNode } from 'react'
import { ClassificationResult } from '../types'

interface Props {
  result: ClassificationResult
}

const confidenceStyle = {
  high:   'bg-green-100 text-green-800 border-green-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  low:    'bg-red-100 text-red-800 border-red-200',
}

const typeLabel: Record<string, string> = {
  invoice:      'Invoice / ΤΠΥ',
  bank_payment: 'Bank Payment',
  receipt:      'Receipt',
}

function Chip({ label, style }: { label: string; style?: string }) {
  return (
    <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium border ${style ?? 'bg-gray-100 text-gray-700 border-gray-200'}`}>
      {label}
    </span>
  )
}

function Field({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div>
      <p className="text-xs text-gray-400 uppercase tracking-wider mb-0.5">{label}</p>
      <p className="text-sm font-medium text-gray-800">{value}</p>
    </div>
  )
}

export default function ResultHeader({ result }: Props) {
  const hasSupplier = result.supplier?.name && result.supplier.name !== 'N/A'

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 space-y-4">
      {/* Top row: file name + chips */}
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Document</p>
          <p className="font-semibold text-gray-900">{result.document_file}</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Chip label={typeLabel[result.document_type] ?? result.document_type} style="bg-blue-50 text-blue-700 border-blue-200" />
          <Chip
            label={`Confidence: ${result.confidence}`}
            style={confidenceStyle[result.confidence] ?? confidenceStyle.medium}
          />
        </div>
      </div>

      {/* Metadata grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Field label="Date" value={result.date || '—'} />
        <Field label="Branch" value={result.branch || '—'} />
        <Field
          label="Total"
          value={
            result.total_amount != null
              ? `€${result.total_amount.toFixed(2)}`
              : '—'
          }
        />
        <Field
          label="Supplier"
          value={
            hasSupplier ? (
              <span>
                {result.supplier.name}
                {result.supplier.code && (
                  <span className="ml-1.5 text-xs text-gray-400 font-mono">{result.supplier.code}</span>
                )}
              </span>
            ) : (
              <span className="text-gray-400">—</span>
            )
          }
        />
      </div>

      {/* Flags */}
      {result.flags && result.flags.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-1">
          {result.flags.map((flag, i) => (
            <Chip key={i} label={`⚠ ${flag}`} style="bg-yellow-50 text-yellow-800 border-yellow-200" />
          ))}
        </div>
      )}
    </div>
  )
}
