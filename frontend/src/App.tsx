import { useState } from "react";
import DashboardRouter, { type Page } from "./DashboardRouter";

const NAV_ITEMS: { label: string; page: Page }[] = [
  { label: "Job Listing Hunter", page: "hunter" },
  { label: "Profile Creation", page: "profile" },
  { label: "Job Matcher", page: "matcher" },
];

export default function App() {
  const [page, setPage] = useState<Page>("hunter");
  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <aside className="w-64 bg-white dark:bg-gray-800 shadow-md h-screen fixed hidden md:block">
        <div className="p-6 font-bold text-xl text-gray-800 dark:text-gray-100">Resume Bridge AI</div>
        <nav className="mt-8">
          <div className="flex flex-col gap-2">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.page}
                className={`w-full text-left px-4 py-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200 ${
                  page === item.page ? "bg-gray-200 dark:bg-gray-700 font-semibold" : ""
                }`}
                onClick={() => setPage(item.page)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </nav>
      </aside>
      {/* Main content */}
      <main className="flex-1 ml-0 md:ml-64 p-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">Dashboard</h1>
        <div className="rounded-lg bg-white dark:bg-gray-800 shadow p-6 min-h-[400px]">
          <DashboardRouter page={page} />
        </div>
      </main>
    </div>
  );
}
