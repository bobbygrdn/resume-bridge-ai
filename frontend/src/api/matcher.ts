// src/api/matcher.ts
import API_BASE_URL from "./config";

export async function matchJob(target_url: string, user_id: string = "default_user") {
  const res = await fetch(`${API_BASE_URL}/match-job`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_url, user_id })
  });
  if (!res.ok) throw new Error("Failed to match job");
  return res.json();
}
