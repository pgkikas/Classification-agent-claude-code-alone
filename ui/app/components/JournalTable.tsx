'use client'

import { useRef, useState } from 'react'
import AccountAutocomplete from './AccountAutocomplete'
import { JournalEntry, JournalLine, LineItem, LineItemCategory } from '../types'

interface Props {
  entries: JournalEntry[]
  onChange: (entries: JournalEntry[]) => void
}

// ── Math helpers ──────────────────────────────────────────────────────────────

function r2(n: number) { return Math.round(n * 100) / 100 }

function applyItemPatch(item: LineItem, field: keyof LineItem, value: any): LineItem {
  const updated = { ...item, [field]: value }
  if (field === 'quantity' || field === 'unit_price') {
    updated.net_value = r2((updated.quantity || 0) * (updated.unit_price || 0))
  }
  updated.vat_amount  = r2((updated.net_value || 0) * (updated.vat_rate || 0) / 100)
  updated.gross_value = r2((updated.net_value || 0) + updated.vat_amount)
  return updated
}

function recomputeLineAmount(line: JournalLine): JournalLine {
  if (!line.items || line.items.length === 0) return line
  return { ...line, amount: r2(line.items.reduce((s, i) => s + (i.net_value || 0), 0)) }
}

// ── Immutable update helpers ──────────────────────────────────────────────────

function setLineItems(
  entries: JournalEntry[], ei: number, li: number, items: LineItem[]
): JournalEntry[] {
  return entries.map((entry, i) =>
    i !== ei ? entry : {
      ...entry,
      lines: entry.lines.map((line, j) => {
        if (j !== li) return line
        return recomputeLineAmount({ ...line, items })
      }),
    }
  )
}

function patchLine(
  entries: JournalEntry[], ei: number, li: number, patch: Partial<JournalLine>
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

function moveItem(
  entries: JournalEntry[],
  fromEi: number, fromLi: number, fromIi: number,
  toEi: number, toLi: number
): JournalEntry[] {
  const item = entries[fromEi].lines[fromLi].items![fromIi]
  // Remove from source line
  let result = setLineItems(
    entries, fromEi, fromLi,
    (entries[fromEi].lines[fromLi].items || []).filter((_, i) => i !== fromIi)
  )
  // Add to target line
  const targetItems = [...(result[toEi].lines[toLi].items || []), item]
  return setLineItems(result, toEi, toLi, targetItems)
}

// ── Constants ─────────────────────────────────────────────────────────────────

const CATEGORIES: LineItemCategory[] = [
  'food', 'cleaning', 'fuel', 'office', 'repair', 'vehicle', 'telecom', 'other',
]

const VAT_RATES = [0, 6, 13, 24]

const BLANK_ITEM: LineItem = {
  description: '', quantity: 1, unit: 'τεμ', unit_price: 0,
  net_value: 0, vat_rate: 24, vat_amount: 0, gross_value: 0, category: 'other',
}

// ── Styles ────────────────────────────────────────────────────────────────────

const inputBase =
  'w-full border border-transparent rounded px-2 py-1 text-sm bg-transparent ' +
  'focus:outline-none focus:border-blue-300 focus:bg-white transition-colors'

const itemInput =
  'w-full border border-transparent rounded px-1.5 py-0.5 text-xs bg-transparent ' +
  'focus:outline-none focus:border-blue-300 focus:bg-white transition-colors'

function fmtNum(n: number | undefined | null) {
  if (n == null || n === 0) return '—'
  return n.toLocaleString('el-GR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// ── ItemsPanel ────────────────────────────────────────────────────────────────

interface ItemsPanelProps {
  items: LineItem[]
  ei: number
  li: number
  allEntries: JournalEntry[]
  onItemsChange: (items: LineItem[]) => void
  onReceiveDrop: (fromEi: number, fromLi: number, fromIi: number) => void
  onMoveTo: (fromIi: number, toEi: number, toLi: number) => void
}

function ItemsPanel({ items, ei, li, allEntries, onItemsChange, onReceiveDrop, onMoveTo }: ItemsPanelProps) {
  const [dragOver, setDragOver] = useState(false)
  const [openMoveMenu, setOpenMoveMenu] = useState<number | null>(null)
  const dragCounter = useRef(0)

  // All DR lines in all entries except the current one — these are valid move targets
  const drTargets = allEntries.flatMap((entry, toEi) =>
    entry.lines.flatMap((line, toLi) => {
      if (line.side !== 'DR') return []
      if (toEi === ei && toLi === li) return []
      const label = `Entry ${entry.entry} · ${line.account || '—'} · ${line.description || 'no desc'}`
      return [{ toEi, toLi, label }]
    })
  )

  const netTotal   = r2(items.reduce((s, i) => s + (i.net_value   || 0), 0))
  const grossTotal = r2(items.reduce((s, i) => s + (i.gross_value || 0), 0))

  const handleChange = (ii: number, field: keyof LineItem, value: any) => {
    onItemsChange(items.map((item, i) => i !== ii ? item : applyItemPatch(item, field, value)))
  }

  return (
    <tr>
      <td colSpan={5} className="p-0">
        <div
          className={`mx-4 mb-2 rounded-lg border overflow-hidden transition-all ${
            dragOver
              ? 'border-indigo-400 bg-indigo-100/50 ring-2 ring-indigo-200'
              : 'border-indigo-100 bg-indigo-50/30'
          }`}
          onDragEnter={e => {
            e.preventDefault()
            dragCounter.current++
            setDragOver(true)
          }}
          onDragOver={e => e.preventDefault()}
          onDragLeave={() => {
            dragCounter.current--
            if (dragCounter.current <= 0) {
              dragCounter.current = 0
              setDragOver(false)
            }
          }}
          onDrop={e => {
            e.preventDefault()
            dragCounter.current = 0
            setDragOver(false)
            try {
              const src = JSON.parse(e.dataTransfer.getData('application/item'))
              if (src.ei !== ei || src.li !== li) {
                onReceiveDrop(src.ei, src.li, src.ii)
              }
            } catch {}
          }}
        >
          {items.length === 0 ? (
            /* Empty state — drop zone + add button */
            <div className={`flex items-center gap-3 px-4 py-3 transition-colors ${
              dragOver ? 'text-indigo-600' : 'text-gray-400'
            }`}>
              <span className="text-lg select-none">{dragOver ? '⬇' : '⠿'}</span>
              <span className="text-xs">
                {dragOver ? 'Drop item here' : 'Drop items here or'}
              </span>
              {!dragOver && (
                <button
                  onClick={() => onItemsChange([{ ...BLANK_ITEM }])}
                  className="text-xs text-indigo-500 hover:text-indigo-700 font-semibold transition-colors"
                >
                  + Add item
                </button>
              )}
            </div>
          ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs min-w-[640px]">
              <thead>
                <tr className="text-[10px] text-gray-400 uppercase tracking-wider border-b border-indigo-100">
                  <th className="w-7" />
                  <th className="text-left px-2 py-1.5">Description</th>
                  <th className="text-center px-1 py-1.5 w-24">Category</th>
                  <th className="text-right px-1 py-1.5 w-12">Qty</th>
                  <th className="text-left  px-1 py-1.5 w-10">Unit</th>
                  <th className="text-right px-1 py-1.5 w-20">Price (€)</th>
                  <th className="text-right px-1 py-1.5 w-22">Net (€)</th>
                  <th className="text-center px-1 py-1.5 w-16">VAT%</th>
                  <th className="text-right px-1 py-1.5 w-22">Gross (€)</th>
                  <th className="w-7" />
                </tr>
              </thead>
              <tbody>
                {items.map((item, ii) => (
                  <tr
                    key={ii}
                    draggable
                    onDragStart={e => {
                      e.dataTransfer.setData('application/item', JSON.stringify({ ei, li, ii }))
                      e.dataTransfer.effectAllowed = 'move'
                    }}
                    className="border-b border-indigo-50 last:border-0 hover:bg-white/70 transition-colors group/item cursor-default"
                  >
                    {/* Drag handle */}
                    <td className="text-center text-gray-300 hover:text-gray-500 cursor-grab active:cursor-grabbing pl-2 select-none text-sm">
                      ⠿
                    </td>

                    {/* Description */}
                    <td className="px-1 py-0.5">
                      <input
                        type="text"
                        value={item.description}
                        onChange={e => handleChange(ii, 'description', e.target.value)}
                        className={itemInput}
                        placeholder="Description…"
                      />
                    </td>

                    {/* Category */}
                    <td className="px-1 py-0.5">
                      <select
                        value={item.category}
                        onChange={e => handleChange(ii, 'category', e.target.value)}
                        className={`${itemInput} capitalize cursor-pointer`}
                      >
                        {CATEGORIES.map(c => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                    </td>

                    {/* Qty */}
                    <td className="px-1 py-0.5">
                      <input
                        type="number" min="0" step="1"
                        value={item.quantity}
                        onChange={e => handleChange(ii, 'quantity', parseFloat(e.target.value) || 0)}
                        className={`${itemInput} text-right font-mono`}
                      />
                    </td>

                    {/* Unit */}
                    <td className="px-1 py-0.5">
                      <input
                        type="text"
                        value={item.unit}
                        onChange={e => handleChange(ii, 'unit', e.target.value)}
                        className={itemInput}
                      />
                    </td>

                    {/* Unit price */}
                    <td className="px-1 py-0.5">
                      <input
                        type="number" min="0" step="0.01"
                        value={item.unit_price}
                        onChange={e => handleChange(ii, 'unit_price', parseFloat(e.target.value) || 0)}
                        className={`${itemInput} text-right font-mono`}
                      />
                    </td>

                    {/* Net value — editable; auto-updated when qty×price changes */}
                    <td className="px-1 py-0.5">
                      <input
                        type="number" min="0" step="0.01"
                        value={item.net_value}
                        onChange={e => handleChange(ii, 'net_value', parseFloat(e.target.value) || 0)}
                        className={`${itemInput} text-right font-mono font-semibold`}
                      />
                    </td>

                    {/* VAT rate */}
                    <td className="px-1 py-0.5">
                      <select
                        value={item.vat_rate}
                        onChange={e => handleChange(ii, 'vat_rate', parseInt(e.target.value))}
                        className={`${itemInput} text-right font-mono cursor-pointer`}
                      >
                        {VAT_RATES.map(r => (
                          <option key={r} value={r}>{r}%</option>
                        ))}
                      </select>
                    </td>

                    {/* Gross — computed, read-only */}
                    <td className="px-2 py-0.5 text-right font-mono font-semibold text-gray-700">
                      {(item.gross_value || 0).toLocaleString('el-GR', { minimumFractionDigits: 2 })}
                    </td>

                    {/* Move-to + Delete */}
                    <td className="px-1 text-center relative">
                      <div className="flex items-center justify-center gap-0.5">
                        <button
                          onClick={() => setOpenMoveMenu(openMoveMenu === ii ? null : ii)}
                          title="Move to another line"
                          className="opacity-0 group-hover/item:opacity-100 text-gray-300 hover:text-indigo-500 text-xs font-bold transition-all"
                        >
                          →
                        </button>
                        <button
                          onClick={() => onItemsChange(items.filter((_, i) => i !== ii))}
                          title="Remove item"
                          className="opacity-0 group-hover/item:opacity-100 text-gray-300 hover:text-red-500 text-base font-bold leading-none transition-all pr-1"
                        >
                          ×
                        </button>
                      </div>

                      {/* Move-to dropdown */}
                      {openMoveMenu === ii && (
                        <>
                          {/* Backdrop */}
                          <div
                            className="fixed inset-0 z-40"
                            onClick={() => setOpenMoveMenu(null)}
                          />
                          <div className="absolute right-0 top-full z-50 bg-white border border-gray-200 rounded-lg shadow-lg min-w-[240px] py-1 text-left">
                            <div className="px-3 py-1 text-[10px] text-gray-400 uppercase tracking-wider border-b border-gray-100">
                              Move to…
                            </div>
                            {drTargets.length === 0 ? (
                              <div className="px-3 py-2 text-xs text-gray-400 italic">
                                No other DR lines available
                              </div>
                            ) : (
                              drTargets.map(({ toEi, toLi, label }) => (
                                <button
                                  key={`${toEi}-${toLi}`}
                                  onClick={() => {
                                    onMoveTo(ii, toEi, toLi)
                                    setOpenMoveMenu(null)
                                  }}
                                  className="w-full text-left px-3 py-1.5 text-xs hover:bg-indigo-50 hover:text-indigo-700 transition-colors"
                                >
                                  {label}
                                </button>
                              ))
                            )}
                          </div>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>

              <tfoot>
                <tr className="border-t border-indigo-200 bg-indigo-50/60">
                  <td colSpan={5} className="px-3 py-1.5">
                    <button
                      onClick={() => onItemsChange([...items, { ...BLANK_ITEM }])}
                      className="text-[10px] text-indigo-500 hover:text-indigo-700 font-semibold uppercase tracking-wide transition-colors"
                    >
                      + Add item
                    </button>
                    <span className="ml-2 text-[10px] text-gray-400">
                      {items.length} item{items.length !== 1 ? 's' : ''}
                    </span>
                  </td>
                  <td className="px-1 py-1.5 text-right text-[10px] font-semibold font-mono text-gray-800">
                    {netTotal.toLocaleString('el-GR', { minimumFractionDigits: 2 })}
                  </td>
                  <td />
                  <td className="px-2 py-1.5 text-right text-[10px] font-semibold font-mono text-gray-800">
                    {grossTotal.toLocaleString('el-GR', { minimumFractionDigits: 2 })}
                  </td>
                  <td />
                </tr>
              </tfoot>
            </table>
          </div>
          )}
        </div>
      </td>
    </tr>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

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
                  <th className="text-right px-4 py-2 w-36">Amount (€)</th>
                  <th className="w-8" />
                </tr>
              </thead>
              <tbody>
                {entry.lines.map((line, li) => {
                  const hasItems = !!(line.items && line.items.length > 0)

                  return (
                    <>
                      <tr
                        key={`line-${li}`}
                        className={`border-b transition-colors group ${
                          hasItems ? 'border-indigo-50/80' : 'border-gray-50 hover:bg-gray-50/60'
                        }`}
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

                        {/* Account */}
                        <td className="px-1 py-1">
                          <AccountAutocomplete
                            value={line.account}
                            onSelect={(code, desc) => {
                              const patch: Partial<JournalLine> = { account: code }
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

                        {/* Amount — locked (Σ items) when items exist, free input otherwise */}
                        <td className="px-1 py-1">
                          {hasItems ? (
                            <div
                              title="Auto-computed from items — edit items to change"
                              className="flex items-center justify-end gap-1 px-2 py-1 text-sm font-mono font-semibold text-gray-700 bg-gray-50 border border-gray-100 rounded select-none"
                            >
                              <span className="text-[10px] text-gray-400 font-normal">Σ</span>
                              {fmtNum(line.amount)}
                            </div>
                          ) : (
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
                          )}
                        </td>

                        {/* Delete line */}
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

                      {/* Items panel — always visible on DR lines */}
                      {line.side === 'DR' && (
                        <ItemsPanel
                          key={`items-${li}`}
                          items={line.items ?? []}
                          ei={ei}
                          li={li}
                          allEntries={entries}
                          onItemsChange={newItems =>
                            onChange(setLineItems(entries, ei, li, newItems))
                          }
                          onReceiveDrop={(fromEi, fromLi, fromIi) =>
                            onChange(moveItem(entries, fromEi, fromLi, fromIi, ei, li))
                          }
                          onMoveTo={(fromIi, toEi, toLi) =>
                            onChange(moveItem(entries, ei, li, fromIi, toEi, toLi))
                          }
                        />
                      )}
                    </>
                  )
                })}
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
