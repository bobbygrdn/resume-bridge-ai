// src/api/jobListings.ts
import API_BASE_URL from "./config";

export async function fetchJobListings(search_query: string, user_id: string = "default_user") {
  const res = await fetch(`${API_BASE_URL}/hunt-jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ search_query, user_id })
  });
  if (!res.ok) throw new Error("Failed to fetch job listings");
  return res.json();
}
