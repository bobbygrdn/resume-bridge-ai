import React, { useState } from "react";
import { matchJob } from "../api/matcher";

type MatchResult = {
  match_score: number;
  key_alignments: string[];
  skill_gaps: string[];
  personalized_pitch: string;
};

export default function JobMatcher() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<MatchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await matchJob(url, "default_user");
      setResult(data);
    } catch (err: unknown) {
      setError((err as Error).message || "Match failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="d-flex flex-column align-items-center justify-content-center min-vh-60">
      <div className="card w-100">
        <h2 className="h3 mb-4">Job Matcher</h2>
        <form onSubmit={handleSubmit} className="row g-3 align-items-end">
          <div className="col flex-grow-1">
            <input
              type="url"
              className="form-control"
              placeholder="Paste a job posting URL"
              value={url}
              onChange={e => setUrl(e.target.value)}
              required
            />
          </div>
          <div className="col-auto">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !url}
            >
              {loading ? "Matching..." : "Match Job"}
            </button>
          </div>
        </form>
        <div className="mt-4 p-3 rounded border" style={{ minHeight: 120, background: 'var(--bg-surface-hover)', color: 'var(--text-muted)' }}>
          {error && <p className="text-danger mb-0">{error}</p>}
          {result && (
            <div className="d-flex flex-column gap-3">
              <div>
                <span className="fw-semibold">Match Score:</span>{' '}
                <span className="text-primary fw-semibold">{result.match_score}%</span>
              </div>
              <div>
                <span className="fw-semibold">Key Alignments:</span>
                <ul className="ms-3 text-success">
                  {result.key_alignments.map((item, i) => <li key={i}>{item}</li>)}
                </ul>
              </div>
              <div>
                <span className="fw-semibold">Skill Gaps:</span>
                <ul className="ms-3 text-danger">
                  {result.skill_gaps.map((item, i) => <li key={i}>{item}</li>)}
                </ul>
              </div>
              <div>
                <span className="fw-semibold">Personalized Pitch:</span>
                <p className="fst-italic text-body">{result.personalized_pitch}</p>
              </div>
            </div>
          )}
          {!result && !error && !loading && (
            <p className="text-muted mb-0">
              Paste a job URL and click Match to see your fit.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
