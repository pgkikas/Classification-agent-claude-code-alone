'use client'

import AccountAutocomplete from './AccountAutocomplete'
import { JournalEntry, JournalLine } from '../types'

interface Props {
  entries: JournalEntry[]
  onChange: (entries: JournalEntry[]) => void
}

// ── Immutable update helpers ──────────────────────────────────────────────────

function patchLine(
  entries: JournalEntry[],
  ei: number,
  li: number,
  patch: Partial<JournalLine>
): JournalEntry[] {
  return entries.map((entry, i) =>
    i !== ei ? entry : {
      ...entry,
      lines: entry.lines.map((line, j) => j !== li ? line : { ...line, ...patch }),
    }
  )
}

function addLine(entries: JournalEntry[], ei: number): JournalEntry[] {
  return entries.map((entry, i) =>
    i !== ei ? entry : {
      ...entry,
      lines: [...entry.lines, { side: 'DR' as const, account: '', description: '', amount: 0 }],
    }
  )
}

function removeLine(entries: JournalEntry[], ei: number, li: number): JournalEntry[] {
  return entries.map((entry, i) =>
    i !== ei ? entry : { ...entry, lines: entry.lines.filter((_, j) => j !== li) }
  )
}

function addEntry(entries: JournalEntry[]): JournalEntry[] {
  return [
    ...entries,
    {
      entry: entries.length + 1,
      description: '',
      lines: [
        { side: 'DR' as const, account: '', description: '', amount: 0 },
        { side: 'CR' as const, account: '', description: '', amount: 0 },
      ],
    },
  ]
}

function removeEntry(entries: JournalEntry[], ei: number): JournalEntry[] {
  return entries
    .filter((_, i) => i !== ei)
    .map((e, i) => ({ ...e, entry: i + 1 }))
}

// ── Shared input style ────────────────────────────────────────────────────────

const inputBase =
  'w-full border border-transparent rounded px-2 py-1 text-sm bg-transparent ' +
  'focus:outline-none focus:border-blue-300 focus:bg-white transition-colors'

// ── Component ─────────────────────────────────────────────────────────────────

export default function JournalTable({ entries, onChange }: Props) {
  if (!entries || entries.length === 0) {
    return (
      <div className="text-center py-6">
        <p className="text-sm text-gray-400 italic mb-3">No journal entries.</p>
        <button
          onClick={() => onChange(addEntry([]))}
          className="text-xs text-blue-600 hover:text-blue-800 font-medium"
        >
          + Add entry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {entries.map((entry, ei) => {
        const drTotal = entry.lines
          .filter(l => l.side === 'DR')
          .reduce((s, l) => s + (Number(l.amount) || 0), 0)
        const crTotal = entry.lines
          .filter(l => l.side === 'CR')
          .reduce((s, l) => s + (Number(l.amount) || 0), 0)
        const balanced = Math.abs(drTotal - crTotal) < 0.01

        return (
          <div key={ei} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">

            {/* Entry header */}
            <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200">
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider shrink-0">
                  Entry {entry.entry}
                </span>
                <input
                  type="text"
                  value={entry.description}
                  onChange={e => onChange(entries.map((en, i) =>
                    i !== ei ? en : { ...en, description: e.target.value }
                  ))}
                  placeholder="Entry description…"
                  className="flex-1 text-xs text-gray-500 bg-transparent border border-transparent rounded px-1 py-0.5 focus:outline-none focus:border-blue-300 focus:bg-white min-w-0"
                />
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  balanced ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }`}>
                  {balanced ? 'Balanced ✓' : `Δ ${Math.abs(drTotal - crTotal).toFixed(2)}`}
                </span>
                {entries.length > 1 && (
                  <button
                    onClick={() => onChange(removeEntry(entries, ei))}
                    title="Delete this entry"
                    className="text-gray-300 hover:text-red-500 text-sm font-bold leading-none transition-colors px-1"
                  >
                    ×
                  </button>
                )}
              </div>
            </div>

            {/* Lines table */}
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-gray-400 uppercase tracking-wider border-b border-gray-100">
                  <th className="text-left px-4 py-2 w-20">Side</th>
                  <th className="text-left px-4 py-2 w-48">Account</th>
                  <th className="text-left px-4 py-2">Description</th>
                  <th className="text-right px-4 py-2 w-28">Amount (€)</th>
                  <th className="w-8" />
                </tr>
              </thead>
              <tbody>
                {entry.lines.map((line, li) => (
                  <tr
                    key={li}
                    className="border-b border-gray-50 last:border-0 hover:bg-gray-50/60 transition-colors group"
                  >
                    {/* Side */}
                    <td className="px-3 py-1.5">
                      <select
                        value={line.side}
                        onChange={e => onChange(patchLine(entries, ei, li, {
                          side: e.target.value as 'DR' | 'CR',
                        }))}
                        className={`border rounded px-2 py-0.5 text-xs font-bold cursor-pointer focus:outline-none focus:ring-1 focus:ring-blue-300 ${
                          line.side === 'DR'
                            ? 'bg-blue-50 text-blue-700 border-blue-200'
                            : 'bg-purple-50 text-purple-700 border-purple-200'
                        }`}
                      >
                        <option value="DR">DR</option>
                        <option value="CR">CR</option>
                      </select>
                    </td>

                    {/* Account — with autocomplete */}
                    <td className="px-1 py-1">
                      <AccountAutocomplete
                        value={line.account}
                        onSelect={(code, desc) => {
                          const patch: Partial<JournalLine> = { account: code }
                          // Always update description from lookup when selected from dropdown
                          if (desc) patch.description = desc
                          onChange(patchLine(entries, ei, li, patch))
                        }}
                        className={`${inputBase} font-mono`}
                      />
                    </td>

                    {/* Description */}
                    <td className="px-1 py-1">
                      <input
                        type="text"
                        value={line.description}
                        onChange={e => onChange(patchLine(entries, ei, li, {
                          description: e.target.value,
                        }))}
                        className={inputBase}
                      />
                    </td>

                    {/* Amount */}
                    <td className="px-1 py-1">
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        value={line.amount}
                        onChange={e => onChange(patchLine(entries, ei, li, {
                          amount: parseFloat(e.target.value) || 0,
                        }))}
                        className={`${inputBase} text-right font-mono`}
                      />
                    </td>

                    {/* Delete line — visible on row hover */}
                    <td className="pr-2 text-center">
                      <button
                        onClick={() => {
                          if (entry.lines.length > 1) onChange(removeLine(entries, ei, li))
                        }}
                        disabled={entry.lines.length <= 1}
                        title="Delete line"
                        className="opacity-0 group-hover:opacity-100 text-gray-300 hover:text-red-500 disabled:opacity-0 text-base font-bold leading-none transition-all"
                      >
                        ×
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Add line footer */}
            <div className="px-4 py-2 border-t border-gray-50">
              <button
                onClick={() => onChange(addLine(entries, ei))}
                className="text-xs text-blue-500 hover:text-blue-700 font-medium transition-colors"
              >
                + Add line
              </button>
            </div>
          </div>
        )
      })}

      {/* Add entry */}
      <div className="flex justify-center pt-1">
        <button
          onClick={() => onChange(addEntry(entries))}
          className="text-xs text-gray-400 hover:text-blue-600 font-medium border border-dashed border-gray-300 hover:border-blue-400 rounded-lg px-4 py-2 transition-colors"
        >
          + Add entry
        </button>
      </div>
    </div>
  )
}
