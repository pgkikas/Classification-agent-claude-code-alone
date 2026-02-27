'use client'

import { LineItem } from '../types'

interface Props {
  items?: LineItem[]
}

// ── Category badge config ─────────────────────────────────────────────────────

const CATEGORY_STYLE: Record<string, { label: string; cls: string }> = {
  food:     { label: 'Food',     cls: 'bg-green-100 text-green-700' },
  cleaning: { label: 'Cleaning', cls: 'bg-blue-100 text-blue-700' },
  fuel:     { label: 'Fuel',     cls: 'bg-orange-100 text-orange-700' },
  office:   { label: 'Office',   cls: 'bg-violet-100 text-violet-700' },
  repair:   { label: 'Repair',   cls: 'bg-yellow-100 text-yellow-700' },
  vehicle:  { label: 'Vehicle',  cls: 'bg-red-100 text-red-700' },
  telecom:  { label: 'Telecom',  cls: 'bg-sky-100 text-sky-700' },
  other:    { label: 'Other',    cls: 'bg-gray-100 text-gray-600' },
}

function CategoryBadge({ category }: { category: string }) {
  const style = CATEGORY_STYLE[category] ?? CATEGORY_STYLE.other
  return (
    <span className={`inline-block text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded ${style.cls}`}>
      {style.label}
    </span>
  )
}

function fmt(n: number | undefined | null) {
  if (n == null || n === 0) return '—'
  return n.toLocaleString('el-GR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// ── Summary row — net totals per category ────────────────────────────────────

function CategorySummary({ items }: { items: LineItem[] }) {
  const totals: Record<string, number> = {}
  for (const item of items) {
    const cat = item.category || 'other'
    totals[cat] = (totals[cat] ?? 0) + (item.net_value ?? 0)
  }

  const cats = Object.entries(totals).sort((a, b) => b[1] - a[1])
  if (cats.length === 0) return null

  return (
    <div className="flex flex-wrap gap-2 px-4 py-2 border-b border-gray-100 bg-gray-50">
      {cats.map(([cat, total]) => {
        const style = CATEGORY_STYLE[cat] ?? CATEGORY_STYLE.other
        return (
          <span key={cat} className={`text-xs font-medium px-2 py-0.5 rounded-full ${style.cls}`}>
            {style.label}: {total.toLocaleString('el-GR', { minimumFractionDigits: 2 })} €
          </span>
        )
      })}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export default function LineItemsPanel({ items }: Props) {
  if (!items || items.length === 0) return null

  return (
    <details className="group bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <summary className="flex items-center justify-between px-4 py-3 cursor-pointer select-none list-none hover:bg-gray-50 transition-colors">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-gray-600">Source line items</span>
          <span className="text-xs text-gray-400 font-mono bg-gray-100 px-1.5 py-0.5 rounded">
            {items.length} item{items.length !== 1 ? 's' : ''}
          </span>
        </div>
        {/* Chevron rotates on open */}
        <svg
          className="w-4 h-4 text-gray-400 transition-transform group-open:rotate-180"
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </summary>

      {/* Category totals */}
      <CategorySummary items={items} />

      {/* Items table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-gray-400 uppercase tracking-wider border-b border-gray-100">
              <th className="text-left px-4 py-2">Description</th>
              <th className="text-center px-3 py-2 w-20">Category</th>
              <th className="text-right px-3 py-2 w-20">Qty</th>
              <th className="text-right px-3 py-2 w-24">Unit Price</th>
              <th className="text-right px-3 py-2 w-24">Net (€)</th>
              <th className="text-right px-3 py-2 w-16">VAT %</th>
              <th className="text-right px-3 py-2 w-24">VAT (€)</th>
              <th className="text-right px-3 py-2 w-24">Gross (€)</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, i) => (
              <tr
                key={i}
                className="border-b border-gray-50 last:border-0 hover:bg-gray-50/60 transition-colors"
              >
                <td className="px-4 py-2 text-gray-800">{item.description || '—'}</td>
                <td className="px-3 py-2 text-center">
                  <CategoryBadge category={item.category || 'other'} />
                </td>
                <td className="px-3 py-2 text-right text-gray-600 font-mono text-xs">
                  {item.quantity ? `${item.quantity} ${item.unit || ''}`.trim() : '—'}
                </td>
                <td className="px-3 py-2 text-right text-gray-600 font-mono text-xs">
                  {fmt(item.unit_price)}
                </td>
                <td className="px-3 py-2 text-right font-mono text-xs text-gray-800">
                  {fmt(item.net_value)}
                </td>
                <td className="px-3 py-2 text-right font-mono text-xs text-gray-500">
                  {item.vat_rate != null && item.vat_rate !== 0 ? `${item.vat_rate}%` : '—'}
                </td>
                <td className="px-3 py-2 text-right font-mono text-xs text-gray-600">
                  {fmt(item.vat_amount)}
                </td>
                <td className="px-3 py-2 text-right font-mono text-xs font-semibold text-gray-800">
                  {fmt(item.gross_value)}
                </td>
              </tr>
            ))}
          </tbody>
          {/* Footer totals */}
          <tfoot>
            <tr className="border-t border-gray-200 bg-gray-50 text-xs font-semibold">
              <td className="px-4 py-2 text-gray-500" colSpan={4}>Total</td>
              <td className="px-3 py-2 text-right font-mono text-gray-800">
                {items.reduce((s, i) => s + (i.net_value ?? 0), 0)
                  .toLocaleString('el-GR', { minimumFractionDigits: 2 })}
              </td>
              <td />
              <td className="px-3 py-2 text-right font-mono text-gray-800">
                {items.reduce((s, i) => s + (i.vat_amount ?? 0), 0)
                  .toLocaleString('el-GR', { minimumFractionDigits: 2 })}
              </td>
              <td className="px-3 py-2 text-right font-mono text-gray-800">
                {items.reduce((s, i) => s + (i.gross_value ?? 0), 0)
                  .toLocaleString('el-GR', { minimumFractionDigits: 2 })}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </details>
  )
}
