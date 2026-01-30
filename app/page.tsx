"use client";

import { useMemo, useState } from "react";
import { ErrorCode } from "@/src/types";
import { errorDatabase } from "@/data/error-db";
import type { ReactNode } from "react";
import {
  LayoutGrid,
  Monitor,
  Terminal,
  Globe,
  Network as NetworkIcon,
  Database as DatabaseIcon,
  Boxes,
  Mail,
  Search as SearchIcon,
} from "lucide-react";

type SelectedPlatform =
  | "all"
  | "windows"
  | "linux"
  | "web"
  | "network"
  | "database"
  | "container"
  | "smtp";

export default function Home() {
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [selectedPlatform, setSelectedPlatform] =
    useState<SelectedPlatform>("all");
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [copiedFixFor, setCopiedFixFor] = useState<string | null>(null);
  const PLATFORMS: Array<{
    id: SelectedPlatform;
    label: string;
    Icon:
      | typeof LayoutGrid
      | typeof Monitor
      | typeof Terminal
      | typeof Globe
      | typeof NetworkIcon
      | typeof DatabaseIcon
      | typeof Boxes
      | typeof Mail;
  }> = [
    { id: "all", label: "All", Icon: LayoutGrid },
    { id: "windows", label: "Windows", Icon: Monitor },
    { id: "linux", label: "Linux", Icon: Terminal },
    { id: "web", label: "Web / HTTP", Icon: Globe },
    { id: "network", label: "Network / DNS", Icon: NetworkIcon },
    { id: "database", label: "Database", Icon: DatabaseIcon },
    { id: "container", label: "Docker / K8s", Icon: Boxes },
    { id: "smtp", label: "Mail / SMTP", Icon: Mail },
  ];

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
    const list = errorDatabase as unknown as ErrorCode[];
    const term = searchTerm.trim().toLowerCase();
    if (!term) return [];
    return list.filter((e) => {
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
  const platformAccent = (p: SelectedPlatform) => {
    switch (p) {
      case "windows":
        return "border-l-blue-600";
      case "linux":
        return "border-l-orange-500";
      case "web":
        return "border-l-emerald-500";
      case "network":
        return "border-l-teal-500";
      case "database":
        return "border-l-purple-500";
      case "container":
        return "border-l-cyan-500";
      case "smtp":
        return "border-l-pink-500";
      default:
        return "border-l-slate-700";
    }
  };

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
          <div className="relative w-full max-w-2xl">
            <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search code, integer, name, or description…"
              className="w-full rounded-xl bg-slate-900/50 border border-slate-800 pl-12 pr-5 py-4 shadow-lg backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
          </div>

          <div className="w-full">
            <div className="flex overflow-x-auto no-scrollbar gap-3 py-4">
              {PLATFORMS.map(({ id, label, Icon }) => {
                const active = selectedPlatform === id;
                return (
                  <button
                    key={id}
                    onClick={() => setSelectedPlatform(id)}
                    className={[
                      "flex items-center gap-2 whitespace-nowrap rounded-full px-4 py-2 text-sm font-medium transition-all duration-200 border",
                      active
                        ? "bg-blue-600/10 border-blue-500 text-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.3)]"
                        : "bg-slate-900/50 border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-200",
                    ].join(" ")}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{label}</span>
                  </button>
                );
              })}
            </div>
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
                  className={[
                    "rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg backdrop-blur-sm",
                    "border-l-2",
                    platformAccent(err.platform as SelectedPlatform),
                  ].join(" ")}
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
 
                  {Array.isArray(err.likelySeenIn) && err.likelySeenIn.length > 0 && (
                    <div className="flex flex-wrap items-center gap-2 mt-4">
                      <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Seen in:
                      </span>
                      {err.likelySeenIn.map((t) => (
                        <span
                          key={t}
                          className="px-2 py-0.5 rounded text-xs font-medium bg-indigo-500/10 text-indigo-300 border border-indigo-500/20"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="mt-3 text-xs text-slate-500">
                    Integer: {err.codeInt}
                  </div>
 
                  {err.runbook ? (
                    <>
                      {Array.isArray(err.runbook.causes) &&
                        err.runbook.causes.length > 0 && (
                          <div className="mt-4">
                            <div className="text-xs font-bold uppercase text-slate-500">
                              Possible Causes
                            </div>
                                        <ul className="list-disc pl-5 mt-2 text-sm text-slate-300">
                                          {err.runbook.causes.map((c, i) => (
                                            <li key={i} className="break-words">{c}</li>
                                          ))}
                            </ul>
                          </div>
                        )}
                      {err.runbook.fixCommand && (
                        <div className="mt-4 relative">
                          <button
                            aria-label="Copy fix command"
                            onClick={async () => {
                              try {
                                await navigator.clipboard.writeText(
                                  err.runbook!.fixCommand as string
                                );
                                setCopiedFixFor(err.code);
                                setTimeout(() => setCopiedFixFor(null), 2000);
                              } catch {}
                            }}
                            className="absolute right-2 top-2 p-2 text-slate-400 hover:text-green-400 hover:bg-slate-800 rounded transition"
                          >
                            {copiedFixFor === err.code ? (
                              <svg
                                xmlns="http://www.w3.org/2000/svg"
                                viewBox="0 0 24 24"
                                fill="currentColor"
                                className="w-4 h-4"
                              >
                                <path d="M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4z" />
                              </svg>
                            ) : (
                              <svg
                                xmlns="http://www.w3.org/2000/svg"
                                viewBox="0 0 24 24"
                                fill="currentColor"
                                className="w-4 h-4"
                              >
                                <path d="M16 1H4c-1.1 0-2 .9-2 2v12h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z" />
                              </svg>
                            )}
                          </button>
                                      <pre className="bg-black/50 p-3 rounded font-mono text-sm text-green-400 whitespace-pre-wrap overflow-x-auto max-w-full">
                            {err.runbook.fixCommand}
                          </pre>
                        </div>
                      )}
                      {err.runbook.deepDive && (
                                    <div className="mt-3 text-xs text-slate-400 break-words">
                          {err.runbook.deepDive}
                        </div>
                      )}
                    </>
                  ) : (
                    err.solutionHint && (
                      <div className="mt-4 border-l-4 border-emerald-500 bg-slate-800/50 p-3">
                        <div className="mb-1 text-xs font-semibold text-emerald-300">
                          Solution
                        </div>
                        <div className="text-sm text-slate-200">
                          {err.solutionHint}
                        </div>
                      </div>
                    )
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
