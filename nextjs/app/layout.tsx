import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ClientClerkProvider } from '../components/clerk-provider'
import { ThemeProvider } from '../components/theme-provider'

const inter = Inter({ subsets: ['latin'] })

// Dynamic title based on environment
const getTitle = () => {
  if (process.env.NODE_ENV === 'development') {
    return 'Concatly App - Local'
  }
  return 'Concatly App - Dev'
}

export const metadata: Metadata = {
  title: getTitle(),
  description: 'Manage and merge duplicate content in Confluence',
  icons: {
    icon: [
      {
        url: '/catlight.png',
        media: '(prefers-color-scheme: light)',
      },
      {
        url: '/catdark.png',
        media: '(prefers-color-scheme: dark)',
      },
    ],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link
          rel="icon"
          href="/catlight.png"
          media="(prefers-color-scheme: light)"
        />
        <link
          rel="icon"
          href="/catdark.png"
          media="(prefers-color-scheme: dark)"
        />
      </head>
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
