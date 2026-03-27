const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type Source = {
  company: string;
  source: string;
  page: number;
};

export type ChatResponse = {
  question: string;
  answer: string;
  sources: Source[];
};

export type Recommendation = {
  type: string;
  reason: string;
  priority: number;
};

export type RecommendResponse = {
  profile: Record<string, unknown>;
  recommendations: Recommendation[];
  explanation: string;
};

export type Policy = {
  id: number;
  user_name: string;
  policy_type: string;
  premium: number;
  status: string;
  created_at: string;
};

export async function chatWithBot(
  question: string,
  topK = 3
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k: topK }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Chat API error: ${err}`);
  }
  return res.json();
}

export async function getRecommendations(profile: {
  age: number;
  income: number;
  dependents: number;
  has_vehicle: boolean;
  has_house: boolean;
}): Promise<RecommendResponse> {
  const res = await fetch(`${API_BASE}/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Recommend API error: ${err}`);
  }
  return res.json();
}

export async function listPolicies(
  userName?: string,
  status?: string
): Promise<Policy[]> {
  const params = new URLSearchParams();
  if (userName) params.set("user_name", userName);
  if (status) params.set("status", status);
  const url = `${API_BASE}/policies${params.toString() ? `?${params}` : ""}`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch policies");
  return res.json();
}

export async function createPolicy(data: {
  user_name: string;
  policy_type: string;
  premium: number;
}): Promise<Policy> {
  const res = await fetch(`${API_BASE}/policy`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Create policy error: ${err}`);
  }
  return res.json();
}

export async function cancelPolicy(id: number): Promise<Policy> {
  const res = await fetch(`${API_BASE}/policy/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Cancel policy error: ${err}`);
  }
  return res.json();
}
