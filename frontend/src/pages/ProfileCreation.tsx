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
    <div className="d-flex flex-column align-items-center justify-content-center min-vh-60">
      <div className="card w-100" style={{ maxWidth: 672, background: 'var(--bg-surface)', color: 'var(--text-primary)' }}>
        <h2 className="h3 mb-4" style={{ color: 'var(--text-primary)' }}>Profile Creation</h2>
        <form onSubmit={handleSubmit} className="row g-3">
          <div className="col-12">
            <label className="form-label">Upload Resume (PDF, DOCX, etc.)</label>
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt,.rtf"
              className="form-control"
              onChange={e => setFile(e.target.files?.[0] || null)}
              required
            />
          </div>
          <div className="col-12">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !file}
            >
              {loading ? "Uploading..." : "Upload Resume"}
            </button>
          </div>
        </form>
        <div className="mt-3 p-3 rounded" style={{ minHeight: 40, background: 'var(--bg-surface-hover)', color: 'var(--text-primary)' }}>
          {status && <p className="text-success mb-0">{status}</p>}
          {error && <p className="text-danger mb-0">{error}</p>}
        </div>
      </div>
    </div>
  );
}
