'use client';

import { useState } from 'react';
import styles from './SearchComparison.module.css';

type JobResult = {
  id: string;
  title: string;
  company: string;
  location: string | null;
  url: string | null;
  score: number;
};

type SearchResponse = {
  query: string;
  mode: string;
  results: JobResult[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000';

export default function SearchComparison() {
  const [query, setQuery] = useState('');
  const [bm25Results, setBm25Results] = useState<JobResult[] | null>(null);
  const [hybridResults, setHybridResults] = useState<JobResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeSkills, setResumeSkills] = useState<string[] | null>(null);
  const [resumeResults, setResumeResults] = useState<JobResult[] | null>(null);
  const [resumeLoading, setResumeLoading] = useState(false);
  const [resumeError, setResumeError] = useState<string | null>(null);

  async function runResumeMatch(e: React.FormEvent) {
    e.preventDefault();
    if (!resumeFile) return;

    setResumeLoading(true);
    setResumeError(null);
    try {
      const formData = new FormData();
      formData.append('file', resumeFile);
      const res = await fetch(`${API_BASE}/match-resume`, { method: 'POST', body: formData });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? 'Resume matching failed');
      }
      const data = await res.json();
      setResumeSkills(data.skills_detected ?? []);
      setResumeResults(data.results ?? []);
    } catch (err) {
      setResumeError(err instanceof Error ? err.message : 'Could not process this resume.');
      setResumeSkills(null);
      setResumeResults(null);
    } finally {
      setResumeLoading(false);
    }
  }

  async function runSearch(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    try {
      const [bm25Res, hybridRes] = await Promise.all([
        fetch(`${API_BASE}/search?q=${encodeURIComponent(trimmed)}&mode=bm25&k=8`),
        fetch(`${API_BASE}/search?q=${encodeURIComponent(trimmed)}&mode=hybrid&k=8`),
      ]);
      if (!bm25Res.ok || !hybridRes.ok) {
        throw new Error('Search request failed');
      }
      const bm25Data: SearchResponse = await bm25Res.json();
      const hybridData: SearchResponse = await hybridRes.json();
      setBm25Results(bm25Data.results);
      setHybridResults(hybridData.results);
    } catch (err) {
      setError('Could not reach the search API — is the backend running?');
      setBm25Results(null);
      setHybridResults(null);
    } finally {
      setLoading(false);
    }
  }

  const bm25Ids = new Set((bm25Results ?? []).map((r) => r.id));
  const hybridIds = new Set((hybridResults ?? []).map((r) => r.id));

  return (
    <>
      <header className={styles.hero}>
        <span className={styles.heroTitle}>jxbs</span>
      </header>

      <main className={styles.main}>
        <p className={styles.subtitle}>
          Same query, two rankers — keyword search next to hybrid search. Results found by only
          one ranker are marked; that disagreement is what hybrid retrieval is trying to resolve.
        </p>

        <form onSubmit={runSearch} className={styles.searchForm}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. remote backend role using Python"
            className={styles.searchInput}
            aria-label="Search query"
          />
          <button type="submit" className={styles.searchButton} disabled={loading}>
            {loading ? 'Searching…' : 'Search'}
          </button>
        </form>

        {error && <p className={styles.error}>{error}</p>}

        {(bm25Results || hybridResults) && (
          <div className={styles.columns}>
            <ResultColumn
              label="BM25 (keyword only)"
              results={bm25Results ?? []}
              otherIds={hybridIds}
            />
            <ResultColumn
              label="Hybrid (BM25 + semantic, RRF-fused)"
              results={hybridResults ?? []}
              otherIds={bm25Ids}
              accent
            />
          </div>
        )}

        <div className={styles.divider} />

        <section className={styles.resumeSection}>
          <h2 className={styles.resumeHeading}>Or match by resume</h2>
          <p className={styles.subtitle}>
            Upload a PDF resume — skills are detected automatically and used to find matching
            jobs, no query needed.
          </p>

          <form onSubmit={runResumeMatch} className={styles.resumeForm}>
            <input
              type="file"
              accept="application/pdf"
              onChange={(e) => setResumeFile(e.target.files?.[0] ?? null)}
              className={styles.fileInput}
              aria-label="Upload resume PDF"
            />
            <button
              type="submit"
              className={styles.searchButton}
              disabled={resumeLoading || !resumeFile}
            >
              {resumeLoading ? 'Matching…' : 'Find matches'}
            </button>
          </form>

          {resumeError && <p className={styles.error}>{resumeError}</p>}

          {resumeSkills && (
            <div className={styles.skillsRow}>
              {resumeSkills.length === 0 ? (
                <p className={styles.empty}>No known skills detected in this resume.</p>
              ) : (
                resumeSkills.map((skill) => (
                  <span key={skill} className={styles.skillPill}>
                    {skill}
                  </span>
                ))
              )}
            </div>
          )}

          {resumeResults && resumeResults.length > 0 && (
            <div className={styles.resumeResultsWrap}>
              <ResultColumn
                label="Matched jobs"
                results={resumeResults}
                otherIds={new Set()}
                accent
                showExclusiveTag={false}
              />
            </div>
          )}
        </section>
      </main>
    </>
  );
}

function ResultColumn({
  label,
  results,
  otherIds,
  accent,
  showExclusiveTag = true,
}: {
  label: string;
  results: JobResult[];
  otherIds: Set<string>;
  accent?: boolean;
  showExclusiveTag?: boolean;
}) {
  return (
    <section className={styles.column}>
      <h2 className={accent ? styles.columnLabelAccent : styles.columnLabel}>{label}</h2>
      {results.length === 0 ? (
        <p className={styles.empty}>No results.</p>
      ) : (
        <div className={styles.resultList}>
          {results.map((r, i) => (
            <div key={r.id} className={styles.resultCard}>
              <span className={styles.rank}>{String(i + 1).padStart(2, '0')}</span>
              <div className={styles.resultBody}>
                <div className={styles.resultTitleRow}>
                  {r.url ? (
                    <a href={r.url} target="_blank" rel="noreferrer" className={styles.resultTitle}>
                      {r.title}
                    </a>
                  ) : (
                    <span className={styles.resultTitle}>{r.title}</span>
                  )}
                  {showExclusiveTag && !otherIds.has(r.id) && (
                    <span className={styles.exclusiveTag} title="Not found by the other ranker">
                      only here
                    </span>
                  )}
                </div>
                <p className={styles.resultMeta}>
                  {r.company}
                  {r.location ? ` · ${r.location}` : ''}
                </p>
              </div>
              <span className={styles.score}>{r.score.toFixed(3)}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
