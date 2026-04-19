import React, { useState } from "react";
import { uploadResume } from "../api/profile";

export default function ProfileCreation() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setStatus(null);
    setError(null);
    try {
      const result = await uploadResume("default_user", file);
      setStatus("Resume uploaded and processed successfully.");
    } catch (err: any) {
      setError(err.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-2xl font-semibold">Profile Creation</h2>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <label className="block">
          <span className="text-gray-700 dark:text-gray-200">Upload Resume (PDF, DOCX, etc.)</span>
          <input
            type="file"
            accept=".pdf,.doc,.docx,.txt,.rtf"
            className="mt-1 block w-full text-gray-900 dark:text-gray-100"
            onChange={e => setFile(e.target.files?.[0] || null)}
            required
          />
        </label>
        <button
          type="submit"
          className="px-4 py-2 rounded bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50"
          disabled={loading || !file}
        >
          {loading ? "Uploading..." : "Upload Resume"}
        </button>
      </form>
      <div className="min-h-[40px]">
        {status && <p className="text-green-700 dark:text-green-400">{status}</p>}
        {error && <p className="text-red-600 dark:text-red-400">{error}</p>}
      </div>
    </div>
  );
}
