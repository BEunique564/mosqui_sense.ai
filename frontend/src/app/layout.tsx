import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MosquiSense AI — Lucknow Municipal Corporation",
  description: "Predictive mosquito outbreak intelligence platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="hi">
      <body className="bg-slate-950 text-slate-100 antialiased">{children}</body>
    </html>
  );
}
