import { useState, useEffect } from "react";
import favicon from "./assets/favicon.ico";
import DashboardRouter, { type Page } from "./DashboardRouter";

export default function App () {

const NAV_ITEMS: { label: string; page: Page }[] = [
  { label: "Job Hunter", page: "hunter" },
  { label: "Profile Creation", page: "profile" },
  { label: "Job Matcher", page: "matcher" },
];

  const [page, setPage] = useState<Page>("hunter");
  const [darkMode, setDarkMode] = useState(() =>
    window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
  );

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : '');
  }, [darkMode]);

  return (
    <>
      {/* Sidebar Navigation */}
      <aside
        className="d-flex flex-column border-end position-fixed app-sidebar vh-100"
      >
        <div className="d-flex flex-column flex-grow-1">
          <header className="d-flex align-items-center border-bottom px-4 py-3 gap-2">
            <img src={favicon} alt="Logo" className="me-2" width={20} height={20} />
            <span className="fs-6 fw-semibold app-brand">Resume Bridge AI</span>
          </header>
          <nav className="flex-grow-1 px-3 py-4">
            <ul className="nav flex-column w-100">
              {NAV_ITEMS.map((item) => (
                <li
                  key={item.page}
                  className={`nav-item${page === item.page ? ' active app-nav-active' : ''}`}
                >
                  <button
                    className="nav-link text-start w-100"
                    aria-current={page === item.page ? "page" : undefined}
                    onClick={() => setPage(item.page)}
                  >
                    {item.label}
                  </button>
                </li>
              ))}
            </ul>
          </nav>
        </div>
        <div className="d-flex flex-column align-items-center gap-2 px-4 pb-3 mt-auto">
          <button
            className="btn btn-outline-secondary btn-sm rounded-circle d-flex align-items-center justify-content-center app-dark-toggle"
            onClick={() => setDarkMode((d) => !d)}
            aria-label="Toggle light/dark mode"
          >
            {darkMode ? (
              <i className="bi bi-brightness-high-fill fs-5" aria-hidden="true"></i>
            ) : (
              <i className="bi bi-moon-fill fs-5" aria-hidden="true"></i>
            )}
          </button>
          <footer className="w-100 pt-2 border-top text-center small text-secondary">
            &copy; 2026 Resume Bridge AI
          </footer>
        </div>
      </aside>
      {/* Main Content */}
      <main
        className="flex-1 d-flex flex-column app-main"
      >
        <section className="flex-grow-1 p-4 d-flex flex-column">
          <div className="card flex-grow-1">
            <DashboardRouter page={page} />
          </div>
        </section>
      </main>
    </>
  );
}
