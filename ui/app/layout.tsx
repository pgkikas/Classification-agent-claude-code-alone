import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import './globals.css'

export const metadata: Metadata = {
  title: 'PROPORIA — Classification Agent',
  description: 'Greek accounting document classification',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="el">
      <body className="min-h-screen bg-gray-100 text-gray-900 antialiased">
        {children}
      </body>
    </html>
  )
}
