"use client";

import { useMemo, useState } from "react";
import { ErrorCode } from "@/src/types";
import { errorDatabase } from "@/data/error-db";
import type { ReactNode } from "react";

type SelectedPlatform = "all" | "windows" | "linux";

export default function Home() {
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [selectedPlatform, setSelectedPlatform] =
    useState<SelectedPlatform>("all");
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const escapeRegExp = (s: string) =>
    s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const highlight = (text: string, term: string): ReactNode => {
    const t = term.trim();
    if (!t) return text;
    const re = new RegExp(`(${escapeRegExp(t)})`, "gi");
    const parts = text.split(re);
    return parts.map((part, i) =>
      i % 2 === 1 ? (
        <span key={i} className="text-amber-400">
          {part}
        </span>
      ) : (
        part
      )
    );
  };

  const matched: ErrorCode[] = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();
    if (!term) return [];
    return errorDatabase.filter((e) => {
      if (selectedPlatform !== "all" && e.platform !== selectedPlatform) {
        return false;
      }
      return (
        e.code.toLowerCase().includes(term) ||
        String(e.codeInt).toLowerCase().includes(term) ||
        e.name.toLowerCase().includes(term) ||
        e.description.toLowerCase().includes(term)
      );
    });
  }, [searchTerm, selectedPlatform]);

  const limited: ErrorCode[] = useMemo(() => matched.slice(0, 50), [matched]);
  const isLimited = matched.length > 50;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      <main className="mx-auto max-w-7xl px-6 py-12">
        <header className="mb-10 text-center">
          <h1 className="text-4xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-400 to-purple-400">
            Error Code Explorer
          </h1>
          <p className="mt-3 text-slate-400">
            Search and filter common Windows and Linux error codes
          </p>
        </header>

        <section className="mb-8 flex flex-col items-center gap-4">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search code, integer, name, or description…"
            className="w-full max-w-2xl rounded-xl bg-slate-900/50 border border-slate-800 px-5 py-4 shadow-lg backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/40"
          />

          <div className="flex items-center gap-2">
            {(["all", "windows", "linux"] as SelectedPlatform[]).map((p) => {
              const active = selectedPlatform === p;
              return (
                <button
                  key={p}
                  onClick={() => setSelectedPlatform(p)}
                  className={[
                    "rounded-lg px-4 py-2 text-sm font-medium transition",
                    active
                      ? "bg-slate-800 text-white ring-1 ring-slate-700"
                      : "bg-slate-900/50 text-slate-300 border border-slate-800 hover:bg-slate-800",
                  ].join(" ")}
                >
                  {p === "all" ? "All" : p.charAt(0).toUpperCase() + p.slice(1)}
                </button>
              );
            })}
          </div>

          {searchTerm.trim() && (
            <div className="text-xs text-slate-500">
              {isLimited
                ? `Showing top 50 matches • ${matched.length} total`
                : `${matched.length} result${matched.length === 1 ? "" : "s"}`}
            </div>
          )}
        </section>

        {!searchTerm.trim() ? (
          <div className="flex items-center justify-center py-24">
            <div className="text-center">
              <div className="mb-4 text-5xl">🔎</div>
              <div className="text-lg text-slate-300">
                Enter a code to start exploring...
              </div>
            </div>
          </div>
        ) : (
          <section>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {limited.map((err) => (
                <article
                  key={`${err.platform}-${err.code}-${err.name}`}
                  className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg backdrop-blur-sm"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-2xl bg-slate-800 rounded-md px-2 py-1 text-slate-100">
                        {err.code}
                      </span>
                      <button
                        aria-label="Copy error code"
                        onClick={async () => {
                          try {
                            await navigator.clipboard.writeText(err.code);
                            setCopiedCode(err.code);
                            setTimeout(() => setCopiedCode(null), 2000);
                          } catch {}
                        }}
                        className="p-2 text-slate-500 hover:text-blue-400 hover:bg-slate-800 rounded-lg transition-all"
                      >
                        {copiedCode === err.code ? (
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="currentColor"
                            className="w-5 h-5"
                          >
                            <path d="M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4z" />
                          </svg>
                        ) : (
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            fill="currentColor"
                            className="w-5 h-5"
                          >
                            <path d="M16 1H4c-1.1 0-2 .9-2 2v12h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z" />
                          </svg>
                        )}
                      </button>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <span className="inline-flex items-center rounded-md bg-slate-800 px-2 py-1 text-xs text-slate-200 ring-1 ring-slate-700">
                        {err.source}
                      </span>
                      <span
                        className={[
                          "inline-flex items-center rounded-md px-2 py-1 text-xs ring-1",
                          err.platform === "windows"
                            ? "bg-blue-900/60 text-blue-200 ring-blue-700"
                            : "bg-emerald-900/60 text-emerald-200 ring-emerald-700",
                        ].join(" ")}
                      >
                        {err.platform}
                      </span>
                    </div>
                  </div>
                  <div className="mt-3 text-sm text-slate-400">
                    {highlight(err.name, searchTerm)}
                  </div>
 
                  <div className="mt-4 text-sm text-slate-300">
                    {highlight(err.description, searchTerm)}
                  </div>
 
                  <div className="mt-3 text-xs text-slate-500">
                    Integer: {err.codeInt}
                  </div>
 
                  {err.solutionHint && (
                    <div className="mt-4 border-l-4 border-emerald-500 bg-slate-800/50 p-3">
                      <div className="mb-1 text-xs font-semibold text-emerald-300">
                        Solution
                      </div>
                      <div className="text-sm text-slate-200">
                        {err.solutionHint}
                      </div>
                    </div>
                  )}
                </article>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
