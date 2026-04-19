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
    } catch (err: any) {
      setError(err.message || "Match failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-2xl font-semibold">Job Matcher</h2>
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-end">
        <input
          type="url"
          className="flex-1 px-3 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
          placeholder="Paste a job posting URL"
          value={url}
          onChange={e => setUrl(e.target.value)}
          required
        />
        <button
          type="submit"
          className="px-4 py-2 rounded bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50"
          disabled={loading || !url}
        >
          {loading ? "Matching..." : "Match Job"}
        </button>
      </form>
      <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg shadow min-h-[120px]">
        {error && <p className="text-red-600 dark:text-red-400">{error}</p>}
        {result && (
          <div className="space-y-4">
            <div>
              <span className="font-semibold">Match Score:</span> <span className="text-blue-700 dark:text-blue-300">{result.match_score}%</span>
            </div>
            <div>
              <span className="font-semibold">Key Alignments:</span>
              <ul className="list-disc ml-6 text-green-700 dark:text-green-400">
                {result.key_alignments.map((item, i) => <li key={i}>{item}</li>)}
              </ul>
            </div>
            <div>
              <span className="font-semibold">Skill Gaps:</span>
              <ul className="list-disc ml-6 text-red-700 dark:text-red-400">
                {result.skill_gaps.map((item, i) => <li key={i}>{item}</li>)}
              </ul>
            </div>
            <div>
              <span className="font-semibold">Personalized Pitch:</span>
              <p className="italic text-gray-800 dark:text-gray-200">{result.personalized_pitch}</p>
            </div>
          </div>
        )}
        {!result && !error && !loading && (
          <p className="text-gray-600 dark:text-gray-300">Paste a job URL and click Match to see your fit.</p>
        )}
      </div>
    </div>
  );
}
