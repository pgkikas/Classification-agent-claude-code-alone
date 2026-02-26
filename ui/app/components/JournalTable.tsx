'use client'

import { JournalEntry, JournalLine } from '../types'

interface Props {
  entries: JournalEntry[]
  onChange: (entries: JournalEntry[]) => void
}

function updateLine(
  entries: JournalEntry[],
  entryIdx: number,
  lineIdx: number,
  patch: Partial<JournalLine>
): JournalEntry[] {
  return entries.map((entry, ei) => {
    if (ei !== entryIdx) return entry
    return {
      ...entry,
      lines: entry.lines.map((line, li) =>
        li === lineIdx ? { ...line, ...patch } : line
      ),
    }
  })
}

const inputBase =
  'w-full border border-transparent rounded px-2 py-1 text-sm bg-transparent ' +
  'focus:outline-none focus:border-blue-300 focus:bg-white transition-colors'

export default function JournalTable({ entries, onChange }: Props) {
  if (!entries || entries.length === 0) {
    return <p className="text-sm text-gray-400 italic">No journal entries.</p>
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
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Entry {entry.entry}
                {entry.description && (
                  <span className="ml-2 font-normal normal-case text-gray-400">— {entry.description}</span>
                )}
              </span>
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${balanced ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                {balanced ? 'Balanced ✓' : `Imbalance: ${(drTotal - crTotal).toFixed(2)}`}
              </span>
            </div>

            {/* Lines table */}
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-gray-400 uppercase tracking-wider border-b border-gray-100">
                  <th className="text-left px-4 py-2 w-20">Side</th>
                  <th className="text-left px-4 py-2 w-44">Account</th>
                  <th className="text-left px-4 py-2">Description</th>
                  <th className="text-right px-4 py-2 w-28">Amount (€)</th>
                </tr>
              </thead>
              <tbody>
                {entry.lines.map((line, li) => (
                  <tr
                    key={li}
                    className={`border-b border-gray-50 last:border-0 hover:bg-gray-50/60 transition-colors ${
                      line.side === 'DR' ? '' : 'text-gray-500'
                    }`}
                  >
                    {/* Side */}
                    <td className="px-3 py-1.5">
                      <select
                        value={line.side}
                        onChange={e =>
                          onChange(updateLine(entries, ei, li, { side: e.target.value as 'DR' | 'CR' }))
                        }
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

                    {/* Account */}
                    <td className="px-1 py-1">
                      <input
                        type="text"
                        value={line.account}
                        onChange={e =>
                          onChange(updateLine(entries, ei, li, { account: e.target.value }))
                        }
                        className={`${inputBase} font-mono`}
                        spellCheck={false}
                      />
                    </td>

                    {/* Description */}
                    <td className="px-1 py-1">
                      <input
                        type="text"
                        value={line.description}
                        onChange={e =>
                          onChange(updateLine(entries, ei, li, { description: e.target.value }))
                        }
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
                        onChange={e =>
                          onChange(updateLine(entries, ei, li, { amount: parseFloat(e.target.value) || 0 }))
                        }
                        className={`${inputBase} text-right font-mono`}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      })}
    </div>
  )
}
