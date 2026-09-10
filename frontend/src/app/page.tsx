"use client";

import { useState } from "react";
import type { FormEvent, ReactNode } from "react";

type Evidence = {
  chunk_id: number | string;
  score: number;
  text: string;
};

type AdvisorResult = {
  question: string;
  intent: string;
  component: string;
  confidence: string;
  answer: string;
  tools_materials: string[];
  safety_topics: string[];
  safety_warnings: string[];
  evidence: Evidence[];
  answer_mode: string;
  llm_warning?: string;
};

const exampleQuestions = [
  "How do I maintain the battery?",
  "What should I do in case of short circuit?",
  "What safety equipment should I wear?",
  "How should I deal with rust on the turbine?",
];

export default function Home() {
  const [question, setQuestion] = useState("How do I maintain the battery?");

  const [mode, setMode] = useState<"offline" | "llm">("offline");

  const [result, setResult] = useState<AdvisorResult | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "";

      const response = await fetch(`${apiUrl}/api/advisor`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question,
          mode,
        }),
      });

      if (!response.ok) {
        throw new Error("The advisor could not process the question.");
      }

      const data: AdvisorResult = await response.json();

      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  const llmSucceeded = result?.answer_mode.includes("llm") ?? false;

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-5xl px-6 py-16">
        {/* HEADER */}
        <header>
          <p className="text-sm font-medium uppercase tracking-widest text-cyan-400">
            NLP · Information Retrieval · Evidence Grounding
          </p>

          <h1 className="mt-4 text-4xl font-bold tracking-tight md:text-5xl">
            Wind Turbine Maintenance Advisor
          </h1>

          <p className="mt-5 max-w-3xl leading-7 text-slate-400">
            Evidence-grounded maintenance and troubleshooting assistant using
            NLP, information retrieval, and optional LLM-assisted rewriting.
          </p>
        </header>

        {/* QUESTION FORM */}
        <section className="mt-12 rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
          <form onSubmit={handleSubmit}>
            <label
              htmlFor="question"
              className="text-sm font-medium text-slate-300"
            >
              Ask a maintenance question
            </label>

            <textarea
              id="question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={4}
              className="mt-3 w-full rounded-xl border border-slate-700 bg-slate-950 p-4 text-slate-100 outline-none transition focus:border-cyan-500"
              placeholder="How do I maintain the battery?"
            />

            {/* EXAMPLE QUESTIONS */}
            <div className="mt-5">
              <p className="text-sm text-slate-400">Try an example</p>

              <div className="mt-3 flex flex-wrap gap-2">
                {exampleQuestions.map((example) => (
                  <button
                    key={example}
                    type="button"
                    onClick={() => setQuestion(example)}
                    className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-300 transition hover:border-cyan-400 hover:text-cyan-300"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>

            {/* ANSWER MODE */}
            <div className="mt-7">
              <p className="text-sm font-medium text-slate-300">Answer mode</p>

              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <label
                  className={`cursor-pointer rounded-xl border p-4 transition ${
                    mode === "offline"
                      ? "border-cyan-400 bg-cyan-400/10"
                      : "border-slate-700 bg-slate-950 hover:border-slate-600"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <input
                      type="radio"
                      name="mode"
                      value="offline"
                      checked={mode === "offline"}
                      onChange={() => setMode("offline")}
                    />

                    <div>
                      <p className="font-medium">Offline / Evidence-grounded</p>

                      <p className="mt-1 text-xs text-slate-500">
                        Uses the NLP and retrieval pipeline directly.
                      </p>
                    </div>
                  </div>
                </label>

                <label
                  className={`cursor-pointer rounded-xl border p-4 transition ${
                    mode === "llm"
                      ? "border-cyan-400 bg-cyan-400/10"
                      : "border-slate-700 bg-slate-950 hover:border-slate-600"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <input
                      type="radio"
                      name="mode"
                      value="llm"
                      checked={mode === "llm"}
                      onChange={() => setMode("llm")}
                    />

                    <div>
                      <p className="font-medium">LLM-assisted</p>

                      <p className="mt-1 text-xs text-slate-500">
                        Rewrites the grounded answer for readability.
                      </p>
                    </div>
                  </div>
                </label>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="mt-7 rounded-xl bg-cyan-400 px-6 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Analyzing..." : "Analyze"}
            </button>
          </form>
        </section>

        {/* ERROR */}
        {error && (
          <div className="mt-8 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-red-300">
            {error}
          </div>
        )}

        {/* RESULT */}
        {result && (
          <section className="mt-10 space-y-6">
            {/* RESULT METADATA */}
            <div className="grid gap-4 md:grid-cols-4">
              <InfoCard title="Component" value={result.component} />

              <InfoCard title="Intent" value={result.intent} />

              <InfoCard title="Confidence" value={result.confidence} />

              <InfoCard
                title="Mode"
                value={llmSucceeded ? "LLM-Assisted" : "Offline"}
              />
            </div>

            {/* LLM STATUS */}
            {llmSucceeded && (
              <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 px-5 py-4">
                <p className="font-medium text-cyan-300">
                  ✓ LLM rewrite completed
                </p>

                <p className="mt-1 text-sm text-slate-400">
                  The technical answer was generated by the evidence-grounded
                  advisor and then rewritten by the LLM for readability.
                </p>
              </div>
            )}

            {/* LLM FALLBACK */}
            {result.llm_warning && (
              <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-5 py-4">
                <p className="font-medium text-amber-300">
                  LLM unavailable — offline answer used
                </p>

                <p className="mt-1 text-sm text-slate-400">
                  {result.llm_warning}
                </p>
              </div>
            )}

            {/* ANSWER */}
            <ResultSection title="Recommended Answer">
              <div className="whitespace-pre-line leading-8 text-slate-300">
                {result.answer}
              </div>
            </ResultSection>

            {/* TOOLS */}
            <ResultSection title="Tools / Materials">
              {result.tools_materials.length > 0 ? (
                <ul className="list-disc space-y-2 pl-5 text-slate-300">
                  {result.tools_materials.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-slate-400">
                  No specific tools or materials were found.
                </p>
              )}
            </ResultSection>

            {/* SAFETY */}
            <ResultSection title="Safety Information">
              {result.safety_warnings.length > 0 ? (
                <ul className="list-disc space-y-2 pl-5 text-slate-300">
                  {result.safety_warnings.map((warning) => (
                    <li key={warning}>{warning}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-slate-400">
                  No specific safety information was retrieved from the manual.
                </p>
              )}
            </ResultSection>

            {/* EVIDENCE */}
            <details className="rounded-2xl border border-slate-800 bg-slate-900/50">
              <summary className="cursor-pointer p-6 font-semibold text-cyan-400">
                View supporting evidence from the manual
              </summary>

              <div className="space-y-4 border-t border-slate-800 p-6">
                {result.evidence.map((item, index) => (
                  <div
                    key={`${item.chunk_id}-${index}`}
                    className="rounded-xl border border-slate-800 bg-slate-950 p-5"
                  >
                    <div className="flex flex-wrap gap-4 text-sm">
                      <span className="text-cyan-400">
                        Evidence #{index + 1}
                      </span>

                      <span className="text-slate-500">
                        Chunk {item.chunk_id}
                      </span>

                      <span className="text-slate-500">
                        Similarity {item.score.toFixed(3)}
                      </span>
                    </div>

                    <p className="mt-4 leading-7 text-slate-400">
                      {cleanEvidenceText(item.text)}
                    </p>
                  </div>
                ))}
              </div>
            </details>

            {/* EXPLANATION */}
            <p className="text-sm leading-6 text-slate-500">
              {llmSucceeded
                ? "LLM-assisted mode changes presentation only. Technical recommendations remain grounded in the offline advisor and retrieved manual content."
                : "Offline mode generates the response directly from the NLP, information retrieval, and evidence-grounding pipeline."}
            </p>
          </section>
        )}
      </div>
    </main>
  );
}

function InfoCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
      <p className="text-xs uppercase tracking-wider text-slate-500">{title}</p>

      <p className="mt-2 capitalize text-slate-100">{value}</p>
    </div>
  );
}

function ResultSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
      <h2 className="text-xl font-semibold">{title}</h2>

      <div className="mt-4">{children}</div>
    </div>
  );
}

function cleanEvidenceText(text: string) {
  return text.replace(/\s+/g, " ").trim();
}
