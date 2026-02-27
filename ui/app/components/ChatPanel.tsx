'use client'

import { useRef, useEffect, useState } from 'react'
import { ChatMessage, ClassificationResult } from '../types'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000'

interface Props {
  classification: ClassificationResult
  messages: ChatMessage[]
  onMessagesChange: (msgs: ChatMessage[]) => void
  onApplyUpdate: (update: ClassificationResult) => void
}

export default function ChatPanel({ classification, messages, onMessagesChange, onApplyUpdate }: Props) {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return

    const userMsg: ChatMessage = { role: 'user', content: text }
    const updated = [...messages, userMsg]
    onMessagesChange(updated)
    setInput('')
    setLoading(true)

    try {
      // Build the messages array for the API (role + content only)
      const apiMessages = updated.map(m => ({ role: m.role, content: m.content }))

      const res = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: apiMessages,
          classification,
        }),
      })

      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail ?? `Chat error ${res.status}`)
      }

      const data = await res.json()
      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: data.reply || '(no response)',
        proposed_update: data.proposed_update || null,
      }
      onMessagesChange([...updated, assistantMsg])
    } catch (e: unknown) {
      const errMsg: ChatMessage = {
        role: 'assistant',
        content: `Error: ${e instanceof Error ? e.message : String(e)}`,
      }
      onMessagesChange([...updated, errMsg])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-2.5 border-b border-gray-100 bg-gray-50 shrink-0">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Chat Assistant
        </h3>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3 min-h-0">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <p className="text-xs text-gray-400">
              Ask questions about the classification or request corrections.
            </p>
            <div className="mt-3 space-y-1">
              {[
                'Why is this item classified as cleaning?',
                'Move non-stick paper to food category',
                'Explain the VAT routing for food items',
              ].map((hint, i) => (
                <button
                  key={i}
                  onClick={() => { setInput(hint); }}
                  className="block mx-auto text-[11px] text-indigo-500 hover:text-indigo-700 transition-colors"
                >
                  "{hint}"
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700'
            }`}>
              <pre className="whitespace-pre-wrap font-sans">{msg.content}</pre>

              {/* Apply changes button */}
              {msg.proposed_update && (
                <button
                  onClick={() => onApplyUpdate(msg.proposed_update!)}
                  className={`mt-2 w-full text-center py-1.5 rounded-lg text-[11px] font-semibold transition-all ${
                    msg.role === 'user'
                      ? 'bg-white/20 text-white hover:bg-white/30'
                      : 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
                  }`}
                >
                  Apply changes
                </button>
              )}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-xl px-4 py-2">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-100 px-3 py-2 bg-gray-50 shrink-0">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about the classification…"
            rows={1}
            className="flex-1 resize-none rounded-lg border border-gray-200 px-3 py-2 text-xs focus:outline-none focus:border-blue-300 focus:ring-1 focus:ring-blue-200 transition-colors"
          />
          <button
            onClick={send}
            disabled={!input.trim() || loading}
            className="px-3 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors shrink-0"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
