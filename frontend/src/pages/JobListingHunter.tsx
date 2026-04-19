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
    } catch (err: any) {
      setError(err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">Job Listing Hunter</h2>
      <form onSubmit={handleSubmit} className="mb-4 flex gap-2">
        <input
          type="text"
          className="flex-1 px-3 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
          placeholder="Search for jobs (e.g. Python developer)"
          value={search}
          onChange={e => setSearch(e.target.value)}
          required
        />
        <button
          type="submit"
          className="px-4 py-2 rounded bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </form>
      <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg shadow min-h-[120px]">
        {error && <p className="text-red-600 dark:text-red-400">{error}</p>}
        {!error && results.length === 0 && !loading && (
          <p className="text-gray-600 dark:text-gray-300">Enter a search to find jobs.</p>
        )}
        {!error && results.length > 0 && (
          <ul className="divide-y divide-gray-300 dark:divide-gray-600">
            {results.map((url, i) => (
              <li key={url + i} className="py-2">
                <a href={url} target="_blank" rel="noopener noreferrer" className="text-blue-700 dark:text-blue-300 underline break-all">{url}</a>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
