import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  metadataBase: new URL('https://arxiv-math-observatory-guyu.nifty-scout-4978.chatgpt.site'),
  title: 'arXiv Math Observatory',
  description: 'Explore the most prolific authors in arXiv mathematics across a custom date range.',
  openGraph: {
    title: 'arXiv Math Observatory',
    description: 'Rank the 50 most active arXiv mathematics author names in any date window longer than 15 days.',
    url: 'https://arxiv-math-observatory-guyu.nifty-scout-4978.chatgpt.site',
    type: 'website',
    images: [{ url: 'https://arxiv-math-observatory-guyu.nifty-scout-4978.chatgpt.site/og.png', width: 1200, height: 630 }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'arXiv Math Observatory',
    description: 'Rank the 50 most active arXiv mathematics author names in a custom date window.',
    images: ['https://arxiv-math-observatory-guyu.nifty-scout-4978.chatgpt.site/og.png'],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
