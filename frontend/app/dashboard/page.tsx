"use client";

import { useState, useEffect, useCallback } from "react";
import {
  listPolicies,
  createPolicy,
  cancelPolicy,
  type Policy,
} from "@/lib/api";

const POLICY_TYPES = [
  "Life Insurance",
  "Health Insurance",
  "Motor Insurance",
  "Home Insurance",
  "Term Life Insurance",
  "Investment Plan (ULIP)",
  "Senior Citizen Health Insurance",
];

export default function DashboardPage() {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    user_name: "",
    policy_type: POLICY_TYPES[0],
    premium: "",
  });

  const fetchPolicies = useCallback(async () => {
    try {
      setError("");
      const data = await listPolicies();
      setPolicies(data);
    } catch {
      setError("Could not load policies. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPolicies();
  }, [fetchPolicies]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    try {
      await createPolicy({
        user_name: form.user_name,
        policy_type: form.policy_type,
        premium: parseFloat(form.premium),
      });
      setForm({ user_name: "", policy_type: POLICY_TYPES[0], premium: "" });
      setShowForm(false);
      await fetchPolicies();
    } catch (err) {
      setError("Failed to create policy.");
    } finally {
      setCreating(false);
    }
  }

  async function handleCancel(id: number) {
    if (!confirm("Cancel this policy?")) return;
    try {
      await cancelPolicy(id);
      await fetchPolicies();
    } catch {
      setError("Failed to cancel policy.");
    }
  }

  const activePolicies = policies.filter((p) => p.status === "active");
  const cancelledPolicies = policies.filter((p) => p.status === "cancelled");

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Policy Dashboard</h1>
          <p className="text-[#94a3b8] text-sm mt-1">
            {activePolicies.length} active / {policies.length} total
          </p>
        </div>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="bg-[#6366f1] hover:bg-[#4f46e5] text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          {showForm ? "✕ Close" : "+ New Policy"}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 bg-red-900/20 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Create Form */}
      {showForm && (
        <form
          onSubmit={handleCreate}
          className="bg-[#1a1d27] border border-[#6366f1]/30 rounded-xl p-6 mb-8 space-y-4"
        >
          <h2 className="text-white font-semibold">Create New Policy</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-[#94a3b8] mb-1.5">
                Customer Name
              </label>
              <input
                type="text"
                required
                value={form.user_name}
                onChange={(e) =>
                  setForm((f) => ({ ...f, user_name: e.target.value }))
                }
                placeholder="John Doe"
                className="w-full bg-[#0f1117] border border-[#2d3148] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#6366f1]"
              />
            </div>
            <div>
              <label className="block text-xs text-[#94a3b8] mb-1.5">
                Policy Type
              </label>
              <select
                value={form.policy_type}
                onChange={(e) =>
                  setForm((f) => ({ ...f, policy_type: e.target.value }))
                }
                className="w-full bg-[#0f1117] border border-[#2d3148] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#6366f1]"
              >
                {POLICY_TYPES.map((t) => (
                  <option key={t}>{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-[#94a3b8] mb-1.5">
                Annual Premium (₹)
              </label>
              <input
                type="number"
                required
                min={1}
                value={form.premium}
                onChange={(e) =>
                  setForm((f) => ({ ...f, premium: e.target.value }))
                }
                placeholder="15000"
                className="w-full bg-[#0f1117] border border-[#2d3148] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#6366f1]"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={creating}
            className="bg-[#6366f1] hover:bg-[#4f46e5] text-white px-6 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {creating ? "Creating…" : "Create Policy"}
          </button>
        </form>
      )}

      {/* Loading */}
      {loading && (
        <div className="text-center py-16 text-[#94a3b8]">
          Loading policies…
        </div>
      )}

      {/* Active Policies */}
      {!loading && (
        <>
          <section className="mb-8">
            <h2 className="text-sm font-semibold text-[#94a3b8] uppercase tracking-wide mb-3">
              Active Policies
            </h2>
            {activePolicies.length === 0 ? (
              <div className="bg-[#1a1d27] border border-[#2d3148] rounded-xl p-8 text-center text-[#94a3b8] text-sm">
                No active policies. Click &quot;+ New Policy&quot; to create one.
              </div>
            ) : (
              <div className="space-y-3">
                {activePolicies.map((p) => (
                  <PolicyCard key={p.id} policy={p} onCancel={handleCancel} />
                ))}
              </div>
            )}
          </section>

          {cancelledPolicies.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-[#94a3b8] uppercase tracking-wide mb-3">
                Cancelled Policies
              </h2>
              <div className="space-y-3 opacity-60">
                {cancelledPolicies.map((p) => (
                  <PolicyCard key={p.id} policy={p} onCancel={null} />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

function PolicyCard({
  policy,
  onCancel,
}: {
  policy: Policy;
  onCancel: ((id: number) => void) | null;
}) {
  const date = new Date(policy.created_at).toLocaleDateString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return (
    <div className="bg-[#1a1d27] border border-[#2d3148] rounded-xl px-5 py-4 flex items-center justify-between gap-4">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3 mb-1">
          <span className="text-white font-medium text-sm truncate">
            {policy.policy_type}
          </span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full border ${
              policy.status === "active"
                ? "border-green-500/40 text-green-400 bg-green-500/10"
                : "border-[#2d3148] text-[#94a3b8]"
            }`}
          >
            {policy.status}
          </span>
        </div>
        <p className="text-xs text-[#94a3b8]">
          {policy.user_name} · ₹{policy.premium.toLocaleString("en-IN")}/yr ·
          Since {date}
        </p>
      </div>
      {onCancel && (
        <button
          onClick={() => onCancel(policy.id)}
          className="text-xs text-red-400 border border-red-500/30 hover:bg-red-500/10 px-3 py-1.5 rounded-lg transition-colors shrink-0"
        >
          Cancel
        </button>
      )}
    </div>
  );
}
