"use client";

import { FormEvent, useState } from "react";
import { ArrowLeft, Database, SearchX, ThumbsDown, ThumbsUp } from "lucide-react";

type Summary = {
  corpus: { documents: number; chunks: number; outdated_documents: number };
  last_7_days: { questions: number; failed_questions: number; insufficient_answers: number; helpful: number; not_helpful: number };
  top_evidence_gaps: { question: string; count: number }[];
};

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

export default function AdminPage() {
  const [key, setKey] = useState("");
  const [summary, setSummary] = useState<Summary>();
  const [error, setError] = useState("");

  async function load(event: FormEvent) {
    event.preventDefault();
    setError("");
    const response = await fetch(`${API_BASE}/api/admin/summary`, { headers: { "X-Admin-Key": key } });
    if (!response.ok) {
      setError(response.status === 401 ? "That admin key was not accepted." : "The dashboard could not load.");
      return;
    }
    setSummary(await response.json());
    setKey("");
  }

  return (
    <main className="admin-page">
      <a href="/copilot/" className="back-link"><ArrowLeft size={16} /> Back to copilot</a>
      <p className="eyebrow orange">Private operations view</p>
      <h1>Compliance signal desk</h1>
      <p>Monitor source coverage and questions that the evidence system could not safely answer.</p>
      {!summary ? (
        <form onSubmit={load} className="admin-login">
          <label htmlFor="admin-key">Render admin key</label>
          <input id="admin-key" type="password" value={key} onChange={(event) => setKey(event.target.value)} autoComplete="off" />
          <button disabled={!key}>Load dashboard</button>
          {error && <span role="alert">{error}</span>}
        </form>
      ) : (
        <div className="metric-grid">
          <article><Database /><span>Approved corpus</span><strong>{summary.corpus.documents}</strong><small>{summary.corpus.chunks} searchable excerpts</small></article>
          <article><SearchX /><span>Evidence gaps</span><strong>{summary.last_7_days.insufficient_answers}</strong><small>insufficient answers in 7 days</small></article>
          <article><ThumbsUp /><span>Helpful</span><strong>{summary.last_7_days.helpful}</strong><small>positive ratings in 7 days</small></article>
          <article><ThumbsDown /><span>Needs review</span><strong>{summary.last_7_days.not_helpful}</strong><small>negative ratings in 7 days</small></article>
          <article><Database /><span>Source freshness</span><strong>{summary.corpus.outdated_documents}</strong><small>sources older than 45 days</small></article>
          <article><SearchX /><span>Failed questions</span><strong>{summary.last_7_days.failed_questions}</strong><small>technical failures in 7 days</small></article>
          {summary.top_evidence_gaps.length > 0 && (
            <section className="gap-list">
              <h2>Questions the corpus could not answer</h2>
              <p>Use this list to prioritize source additions and retrieval fixes.</p>
              <ol>{summary.top_evidence_gaps.map((gap) => <li key={gap.question}><span>{gap.question}</span><strong>{gap.count}</strong></li>)}</ol>
            </section>
          )}
        </div>
      )}
      <style jsx>{`
        .admin-page{max-width:1120px;margin:0 auto;padding:54px 24px;min-height:100vh}.back-link{display:inline-flex;gap:7px;align-items:center;color:#111;margin-bottom:60px}.admin-page h1{font-size:clamp(48px,7vw,80px);line-height:.95;letter-spacing:-2.4px;font-weight:400;margin:10px 0 20px}.admin-page>p:not(.eyebrow){font-size:18px;color:#626260;max-width:620px}.admin-login{margin-top:38px;border:1px solid #dedbd6;background:#fff;padding:24px;max-width:540px;display:grid;grid-template-columns:1fr auto;gap:10px;border-radius:8px}.admin-login label{grid-column:1/-1;font-size:12px;text-transform:uppercase;letter-spacing:.7px}.admin-login input{height:44px;border:1px solid #111;border-radius:4px;padding:0 12px}.admin-login button{border:0;border-radius:4px;background:#111;color:white;padding:0 18px}.admin-login span{grid-column:1/-1;color:#a51c1c;font-size:13px}.metric-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:44px}.metric-grid article{border:1px solid #dedbd6;background:#fff;padding:24px;border-radius:8px;display:grid;grid-template-columns:1fr auto}.metric-grid svg{grid-column:2;grid-row:1/3;color:#ff5600}.metric-grid span{font-size:12px;text-transform:uppercase;letter-spacing:.6px}.metric-grid article strong{font-size:52px;font-weight:400;letter-spacing:-1.5px;margin:20px 0 8px}.metric-grid small{grid-column:1/-1;color:#7b7b78}.gap-list{grid-column:1/-1;background:#fff;border:1px solid #dedbd6;border-radius:8px;padding:24px;margin-top:10px}.gap-list h2{margin:0;font-size:24px}.gap-list p{color:#626260}.gap-list ol{padding-left:22px}.gap-list li{padding:11px 0;border-top:1px solid #dedbd6;display:grid;grid-template-columns:1fr auto;gap:20px}.gap-list li span{text-transform:none;letter-spacing:0;font-size:14px}.gap-list li strong{font-family:monospace;color:#ff5600}@media(max-width:700px){.metric-grid{grid-template-columns:1fr}.admin-login{grid-template-columns:1fr}.admin-login button{height:44px}}
      `}</style>
    </main>
  );
}
