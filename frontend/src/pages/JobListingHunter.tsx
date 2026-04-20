import React, { useState } from "react";
import { fetchJobListings } from "../api/jobListings";

export default function JobListingHunter() {
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults([]);
    try {
      const data = await fetchJobListings(search, "default_user");
      // Expecting { status: string } or { urls: string[] }
      if (Array.isArray(data)) {
        setResults(data);
      } else if (Array.isArray(data.urls)) {
        setResults(data.urls);
      } else if (data.status) {
        setResults([data.status]);
      } else {
        setResults([]);
      }
    } catch (err: unknown) {
      setError((err as Error).message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="d-flex flex-column align-items-center justify-content-center min-vh-60">
      <div className="card w-100" style={{ maxWidth: 672, background: 'var(--bg-surface)', color: 'var(--text-primary)' }}>
        <h2 className="h3 mb-4" style={{ color: 'var(--text-primary)' }}>Job Listing Hunter</h2>
        <form onSubmit={handleSubmit} className="row g-3 align-items-end">
          <div className="col flex-grow-1">
            <input
              type="text"
              className="form-control"
              placeholder="Search for jobs (e.g. Python developer)"
              value={search}
              onChange={e => setSearch(e.target.value)}
              required
            />
          </div>
          <div className="col-auto">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? "Searching..." : "Search"}
            </button>
          </div>
        </form>
        <div className="mt-4 p-3 rounded border" style={{ minHeight: 120, background: 'var(--bg-surface-hover)', color: 'var(--text-primary)' }}>
          {error && <p className="text-danger mb-0">{error}</p>}
          {!error && results.length === 0 && !loading && (
            <p className="text-muted mb-0">Enter a search to find jobs.</p>
          )}
          {!error && results.length > 0 && (
            <div className="d-flex flex-column gap-2">
              {results.map((url, i) => (
                <a
                  key={url + i}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="d-block px-3 py-2 rounded border text-primary fw-semibold bg-white"
                  style={{ wordBreak: 'break-all' }}
                >
                  {url}
                </a>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
