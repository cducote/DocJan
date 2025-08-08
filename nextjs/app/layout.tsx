import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ClientClerkProvider } from '../components/clerk-provider'
import { ThemeProvider } from '../components/theme-provider'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Concatly - Confluence Duplicate Manager',
  description: 'Manage and merge duplicate content in Confluence',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider>
          <ClientClerkProvider>
            {children}
          </ClientClerkProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
