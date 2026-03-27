"use client";

import { useState } from "react";
import { getRecommendations, type RecommendResponse } from "@/lib/api";

export default function RecommendPage() {
  const [form, setForm] = useState({
    age: "",
    income: "",
    dependents: "0",
    has_vehicle: false,
    has_house: false,
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RecommendResponse | null>(null);
  const [error, setError] = useState("");

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const data = await getRecommendations({
        age: parseInt(form.age),
        income: parseFloat(form.income),
        dependents: parseInt(form.dependents),
        has_vehicle: form.has_vehicle,
        has_house: form.has_house,
      });
      setResult(data);
    } catch (err) {
      setError(
        "Failed to get recommendations. Make sure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  }

  const PRIORITY_COLORS: Record<number, string> = {
    1: "border-[#f59e0b] text-[#f59e0b]",
    2: "border-[#6366f1] text-[#6366f1]",
    3: "border-[#22c55e] text-[#22c55e]",
    4: "border-[#94a3b8] text-[#94a3b8]",
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-white mb-1">
        Insurance Recommendations
      </h1>
      <p className="text-[#94a3b8] text-sm mb-8">
        Fill in your profile to receive personalized insurance suggestions.
      </p>

      <form
        onSubmit={handleSubmit}
        className="bg-[#1a1d27] border border-[#2d3148] rounded-xl p-6 space-y-5"
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm text-[#94a3b8] mb-1.5">
              Age <span className="text-red-400">*</span>
            </label>
            <input
              type="number"
              name="age"
              value={form.age}
              onChange={handleChange}
              min={0}
              max={120}
              required
              placeholder="e.g. 35"
              className="w-full bg-[#0f1117] border border-[#2d3148] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#6366f1]"
            />
          </div>
          <div>
            <label className="block text-sm text-[#94a3b8] mb-1.5">
              Annual Income (₹) <span className="text-red-400">*</span>
            </label>
            <input
              type="number"
              name="income"
              value={form.income}
              onChange={handleChange}
              min={0}
              required
              placeholder="e.g. 800000"
              className="w-full bg-[#0f1117] border border-[#2d3148] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#6366f1]"
            />
          </div>
          <div>
            <label className="block text-sm text-[#94a3b8] mb-1.5">
              Number of Dependents
            </label>
            <input
              type="number"
              name="dependents"
              value={form.dependents}
              onChange={handleChange}
              min={0}
              placeholder="0"
              className="w-full bg-[#0f1117] border border-[#2d3148] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#6366f1]"
            />
          </div>
        </div>

        <div className="flex gap-6">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              name="has_vehicle"
              checked={form.has_vehicle}
              onChange={handleChange}
              className="w-4 h-4 accent-[#6366f1]"
            />
            <span className="text-sm text-[#e2e8f0]">I own a vehicle</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              name="has_house"
              checked={form.has_house}
              onChange={handleChange}
              className="w-4 h-4 accent-[#6366f1]"
            />
            <span className="text-sm text-[#e2e8f0]">I own a house</span>
          </label>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-[#6366f1] hover:bg-[#4f46e5] text-white py-2.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          {loading ? "Analysing…" : "Get Recommendations"}
        </button>
      </form>

      {error && (
        <div className="mt-4 bg-red-900/20 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-8 space-y-6">
          <h2 className="text-lg font-semibold text-white">
            Your Recommendations
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {result.recommendations.map((rec, i) => (
              <div
                key={i}
                className={`bg-[#1a1d27] border rounded-xl p-4 ${
                  PRIORITY_COLORS[rec.priority] ?? "border-[#2d3148] text-[#94a3b8]"
                }`}
              >
                <p className="font-semibold text-white text-sm">{rec.type}</p>
                <p className="text-xs mt-1 opacity-80">{rec.reason}</p>
              </div>
            ))}
          </div>

          {result.explanation && (
            <div className="bg-[#1a1d27] border border-[#2d3148] rounded-xl p-5">
              <p className="text-xs text-[#6366f1] font-medium mb-2 uppercase tracking-wide">
                AI Explanation
              </p>
              <p className="text-sm text-[#e2e8f0] leading-relaxed whitespace-pre-wrap">
                {result.explanation}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
