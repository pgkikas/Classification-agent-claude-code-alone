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
}

export interface JournalEntry {
  entry: number
  description: string
  lines: JournalLine[]
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
}
