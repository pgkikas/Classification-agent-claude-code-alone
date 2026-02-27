export type LineItemCategory =
  | 'food' | 'cleaning' | 'fuel' | 'office' | 'repair' | 'vehicle' | 'telecom' | 'other'

export interface LineItem {
  description: string
  quantity: number
  unit: string
  unit_price: number
  net_value: number
  vat_rate: number
  vat_amount: number
  gross_value: number
  category: LineItemCategory | string
}

export interface SupplierInfo {
  name: string
  afm: string
  code: string
}

export interface JournalLine {
  side: 'DR' | 'CR'
  account: string
  description: string
  amount: number
  items?: LineItem[]   // populated on DR expense lines; empty/absent on VAT and CR lines
}

export interface JournalEntry {
  entry: number
  description: string
  lines: JournalLine[]
}

export interface AgentToolCall {
  name: string
  args: Record<string, any>
  result: string
}

export interface AgentLogStep {
  step: number
  reasoning: string | null
  tool_calls: AgentToolCall[]
  tokens: { prompt: number; completion: number; total: number }
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  proposed_update?: ClassificationResult | null
}

export interface ClassificationResult {
  document_file: string
  document_type: 'invoice' | 'bank_payment' | 'receipt'
  date: string
  supplier: SupplierInfo
  branch: string
  total_amount: number
  journal_entries: JournalEntry[]
  reasoning: string
  confidence: 'high' | 'medium' | 'low'
  flags: string[]
  agent_log?: AgentLogStep[]
}
