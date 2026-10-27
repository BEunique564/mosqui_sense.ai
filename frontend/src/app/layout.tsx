import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MosquiSense AI — Sadar Cantt, Lucknow",
  description: "Real-time mosquito outbreak prediction for Sadar Cantt using MOSDAC satellite data + AI ensemble",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="hi">
      <body className="bg-slate-950 text-slate-100 antialiased">{children}</body>
    </html>
  );
}
