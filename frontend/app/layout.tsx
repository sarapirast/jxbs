import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'jxbs — search comparison',
  description: 'Keyword vs. hybrid job search, side by side.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
