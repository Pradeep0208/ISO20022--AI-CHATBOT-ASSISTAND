// Use an environment variable if provided, otherwise use same-origin.
// - Local dev: set VITE_API_BASE_URL=http://localhost:8000 (or your FastAPI URL)
// - Deployment (Hugging Face Space): leave it empty so it calls /api/chat on the same site
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export async function sendMessage(userMessage) {
  const res = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: userMessage }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }

  return await res.json();
}
