import { useEffect, useMemo, useState } from "react";

import { ActionItemCard } from "./ActionItemCard";
import { titleCase } from "./formatting";
import type { ActionMemo, Manifest } from "./types";

type LoadState<T> =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; data: T };

function useJson<T>(url: string | null): LoadState<T> {
  const [state, setState] = useState<LoadState<T>>({ status: "loading" });

  useEffect(() => {
    if (!url) return;
    let cancelled = false;
    setState({ status: "loading" });

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return res.json() as Promise<T>;
      })
      .then((data) => {
        if (!cancelled) setState({ status: "ready", data });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({ status: "error", message: err instanceof Error ? err.message : String(err) });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [url]);

  return state;
}

export function App() {
  const manifestState = useJson<Manifest>("./data/manifest.json");
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null);

  const companies = manifestState.status === "ready" ? manifestState.data.companies : [];
  const activeCompany = selectedCompany ?? companies[0] ?? null;

  const memoUrl = useMemo(
    () => (activeCompany ? `./data/${activeCompany}/action_memo.json` : null),
    [activeCompany],
  );
  const memoState = useJson<ActionMemo>(memoUrl);

  return (
    <div className="page">
      <header className="page__header">
        <h1>Portfolio Ops Copilot</h1>
        <p className="page__subtitle">
          Static companion viewer — reads the same committed <code>action_memo.json</code> the
          Python pipeline produces. No live pipeline invocation here; see the{" "}
          <a href="https://github.com/AnikNicks/portfolio-ops-copilot">main repo</a> to run it for
          real.
        </p>
      </header>

      {manifestState.status === "loading" && <p>Loading company list…</p>}
      {manifestState.status === "error" && (
        <p className="error">Couldn't load manifest.json: {manifestState.message}</p>
      )}

      {companies.length > 0 && (
        <label className="company-picker">
          Portfolio company
          <select
            value={activeCompany ?? ""}
            onChange={(e) => setSelectedCompany(e.target.value)}
          >
            {companies.map((slug) => (
              <option key={slug} value={slug}>
                {titleCase(slug)}
              </option>
            ))}
          </select>
        </label>
      )}

      {memoState.status === "loading" && activeCompany && <p>Loading memo…</p>}
      {memoState.status === "error" && (
        <p className="error">Couldn't load memo for {activeCompany}: {memoState.message}</p>
      )}

      {memoState.status === "ready" && (
        <main>
          <h2>{titleCase(memoState.data.company)} — Value Creation Memo</h2>
          <p className="summary">{memoState.data.summary}</p>
          <div className="action-list">
            {[...memoState.data.action_items]
              .sort((a, b) => a.priority_rank - b.priority_rank)
              .map((item) => (
                <ActionItemCard key={item.priority_rank} item={item} />
              ))}
          </div>
        </main>
      )}
    </div>
  );
}
