// src/api/profile.ts
import API_BASE_URL from "./config";

export async function uploadResume(user_id: string, file: File) {
  const formData = new FormData();
  formData.append("user_id", user_id);
  formData.append("file", file);
  const res = await fetch(`${API_BASE_URL}/upload_resume`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to upload resume");
  return res.json();
}
