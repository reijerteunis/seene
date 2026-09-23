import type { Metadata } from 'next';
import type { ReactNode } from 'react';

import { site } from '../src/site';

export const metadata: Metadata = {
  title: site.name,
  description: site.description,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en-GB">
      <body>{children}</body>
    </html>
  );
}
