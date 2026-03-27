import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "InsureBot AI",
  description: "Offline Insurance AI powered by Ollama + ChromaDB",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-[#0f1117] text-[#e2e8f0]">
        {/* Navigation */}
        <nav className="border-b border-[#2d3148] bg-[#1a1d27] px-6 py-4 flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2 text-[#6366f1] font-bold text-xl">
            <span>🛡️</span>
            <span>InsureBot AI</span>
          </Link>
          <div className="flex gap-6 text-sm">
            <Link href="/chat" className="text-[#94a3b8] hover:text-white transition-colors">
              Chat
            </Link>
            <Link href="/recommend" className="text-[#94a3b8] hover:text-white transition-colors">
              Recommend
            </Link>
            <Link href="/dashboard" className="text-[#94a3b8] hover:text-white transition-colors">
              Dashboard
            </Link>
          </div>
        </nav>
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
