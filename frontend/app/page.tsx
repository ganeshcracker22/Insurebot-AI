import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] px-4 text-center">
      <div className="max-w-2xl">
        <div className="text-6xl mb-6">🛡️</div>
        <h1 className="text-4xl font-bold text-white mb-4">
          InsureBot AI
        </h1>
        <p className="text-[#94a3b8] text-lg mb-10">
          Your offline-first insurance assistant powered by local AI.
          Ask questions about policies, get personalized recommendations,
          and manage your coverage — all privately on your device.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link
            href="/chat"
            className="bg-[#1a1d27] border border-[#2d3148] rounded-xl p-6 hover:border-[#6366f1] transition-all group"
          >
            <div className="text-3xl mb-3">💬</div>
            <h2 className="text-white font-semibold mb-1 group-hover:text-[#6366f1] transition-colors">
              Chat
            </h2>
            <p className="text-[#94a3b8] text-sm">
              Ask questions about insurance policies using AI-powered RAG
            </p>
          </Link>
          <Link
            href="/recommend"
            className="bg-[#1a1d27] border border-[#2d3148] rounded-xl p-6 hover:border-[#6366f1] transition-all group"
          >
            <div className="text-3xl mb-3">✨</div>
            <h2 className="text-white font-semibold mb-1 group-hover:text-[#6366f1] transition-colors">
              Recommend
            </h2>
            <p className="text-[#94a3b8] text-sm">
              Get personalized insurance recommendations based on your profile
            </p>
          </Link>
          <Link
            href="/dashboard"
            className="bg-[#1a1d27] border border-[#2d3148] rounded-xl p-6 hover:border-[#6366f1] transition-all group"
          >
            <div className="text-3xl mb-3">📋</div>
            <h2 className="text-white font-semibold mb-1 group-hover:text-[#6366f1] transition-colors">
              Dashboard
            </h2>
            <p className="text-[#94a3b8] text-sm">
              View and manage all your insurance policies in one place
            </p>
          </Link>
        </div>
      </div>
    </div>
  );
}
