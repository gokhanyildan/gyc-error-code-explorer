"use client";

import { useMemo, useState } from "react";
import { ErrorCode } from "@/src/types";
import { errorDatabase } from "@/data/error-db";

type SelectedPlatform = "all" | "windows" | "linux";

export default function Home() {
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [selectedPlatform, setSelectedPlatform] =
    useState<SelectedPlatform>("all");

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
                    <div>
                      <div className="text-lg font-semibold text-slate-100">
                        {err.code}
                      </div>
                      <div className="text-sm text-slate-400">{err.name}</div>
                    </div>
                    <div className="flex items-center gap-2">
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
 
                  <div className="mt-4 text-sm text-slate-300">
                    {err.description}
                  </div>
 
                  <div className="mt-3 text-xs text-slate-500">
                    Integer: {err.codeInt}
                  </div>
 
                  {err.solutionHint && (
                    <div className="mt-4 rounded-lg border border-slate-700 bg-slate-800/60 p-3">
                      <div className="mb-1 text-xs font-semibold text-slate-300">
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
