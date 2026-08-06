import { useEffect, useState } from "react";
import { NavBar } from "./components/NavBar";
import { LandingPage } from "./pages/LandingPage";
import { OverviewPage } from "./pages/OverviewPage";
import { ResultsPage } from "./pages/ResultsPage";
import { VerifyResponse, verifyClaim } from "./services/api";

type Theme = "light" | "dark";

function getInitialTheme(): Theme {
  return (window.localStorage.getItem("verifai-theme") as Theme | null) ?? "light";
}

function getInitialQuery(): string {
  return new URLSearchParams(window.location.search).get("q") ?? "";
}

export default function App() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  const [query, setQuery] = useState(getInitialQuery);
  const [hasSearched, setHasSearched] = useState(Boolean(getInitialQuery()));
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<VerifyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    window.localStorage.setItem("verifai-theme", theme);
  }, [theme]);

  useEffect(() => {
    const initial = getInitialQuery();
    if (initial) {
      void handleSearch(initial);
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, []);

  async function handleSearch(claim: string) {
    setQuery(claim);
    setHasSearched(true);
    setLoading(true);
    setResponse(null);
    setError(null);

    try {
      const nextResponse = await verifyClaim(claim);
      setResponse(nextResponse);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Verification request failed.");
    } finally {
      setLoading(false);
    }
  }

  function handleHome() {
    setQuery("");
    setHasSearched(false);
    setResponse(null);
    setError(null);
    window.history.replaceState({}, "", window.location.pathname);
  }

  return (
    <main className="app-shell">
      <NavBar theme={theme} onThemeChange={setTheme} onHome={handleHome} />
      {!hasSearched ? (
        <>
          <LandingPage initialQuery={query} loading={loading} onSearch={handleSearch} />
          <OverviewPage />
        </>
      ) : (
        <ResultsPage query={query} loading={loading} response={response} error={error} onSearch={handleSearch} />
      )}
    </main>
  );
}
