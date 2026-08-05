"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import {
  Bookmark,
  Check,
  ChevronDown,
  ExternalLink,
  FileCheck2,
  Menu,
  MessageSquareText,
  Printer,
  Search,
  Send,
  ShieldCheck,
  ThumbsDown,
  ThumbsUp,
  X,
} from "lucide-react";
import { askCopilot, bookmarkAnswer, sendFeedback } from "@/lib/api";
import type { ChatMessage, CitedClaim, CopilotAnswer } from "@/lib/types";

const STARTERS = [
  "Can I hire a 15-year-old to clean a hog barn?",
  "What manure application records should I keep?",
  "What signs of African Swine Fever should employees report?",
  "What changed recently in Iowa confinement rules?",
];

function ClaimList({ claims, answer, ordered = false }: { claims: CitedClaim[]; answer: CopilotAnswer; ordered?: boolean }) {
  const Tag = ordered ? "ol" : "ul";
  return (
    <Tag className={`claim-list ${ordered ? "ordered" : ""}`}>
      {claims.map((claim, index) => (
        <li key={`${claim.text}-${index}`}>
          <span>{claim.text}</span>{" "}
          {claim.citations.map((citationId) => {
            const sourceIndex = answer.citations.findIndex((source) => source.id === citationId);
            if (sourceIndex < 0) return null;
            return (
              <a className="citation-chip" href={`#source-${citationId}`} key={citationId} aria-label={`View source ${sourceIndex + 1}`}>
                {sourceIndex + 1}
              </a>
            );
          })}
        </li>
      ))}
    </Tag>
  );
}

function AnswerCard({ answer }: { answer: CopilotAnswer }) {
  const [feedback, setFeedback] = useState<"helpful" | "not_helpful" | null>(null);
  const [bookmarked, setBookmarked] = useState(false);
  const confidenceClass = `confidence ${answer.applicability.level}`;

  async function rate(rating: "helpful" | "not_helpful") {
    setFeedback(rating);
    try {
      await sendFeedback(answer.id, rating);
    } catch {
      setFeedback(null);
    }
  }

  async function save() {
    setBookmarked(true);
    try {
      await bookmarkAnswer(answer.id);
    } catch {
      setBookmarked(false);
    }
  }

  return (
    <article className="answer-card" aria-label="Copilot answer">
      <div className="answer-topline">
        <span className={`evidence-badge ${answer.evidence_status}`}>
          <ShieldCheck size={15} aria-hidden="true" />
          {answer.evidence_status === "verified" ? "Verified against sources" : answer.evidence_status === "conflicting" ? "Sources conflict" : "Evidence incomplete"}
        </span>
        <span className={confidenceClass}>{answer.applicability.level} applicability</span>
      </div>

      <section className="answer-section short-answer">
        <p className="eyebrow">Short answer</p>
        <ClaimList claims={answer.short_answer} answer={answer} />
      </section>

      <div className="answer-grid">
        <section className="answer-section">
          <h3>Why this applies</h3>
          <ClaimList claims={answer.why} answer={answer} />
        </section>
        <section className="answer-section">
          <h3>Rules that apply</h3>
          <ClaimList claims={answer.rules} answer={answer} />
        </section>
      </div>

      <section className="answer-section documentation">
        <h3><FileCheck2 size={20} aria-hidden="true" /> Documentation to keep</h3>
        <ClaimList claims={answer.documentation} answer={answer} />
      </section>

      {answer.limitations.length > 0 && (
        <section className="limitations" aria-label="Limitations">
          <strong>What this answer cannot establish</strong>
          <ul>{answer.limitations.map((item) => <li key={item}>{item}</li>)}</ul>
        </section>
      )}

      <section className="sources" aria-labelledby={`sources-${answer.id}`}>
        <p className="eyebrow" id={`sources-${answer.id}`}>Official sources</p>
        {answer.citations.map((source, index) => (
          <details className="source" id={`source-${source.id}`} key={source.id}>
            <summary>
              <span className="source-number">{index + 1}</span>
              <span className="source-title"><strong>{source.title}</strong><small>{source.agency}</small></span>
              <ChevronDown size={18} aria-hidden="true" />
            </summary>
            <div className="source-body">
              <p>{source.excerpt}</p>
              <div className="source-meta">
                {source.effective_date && <span>Effective {source.effective_date}</span>}
                {source.publication_date && <span>Published {source.publication_date}</span>}
                <span>Retrieved {new Date(source.retrieved_at).toLocaleDateString()}</span>
              </div>
              <a href={source.url} target="_blank" rel="noreferrer">Open official source <ExternalLink size={14} aria-hidden="true" /></a>
            </div>
          </details>
        ))}
      </section>

      {answer.related_questions.length > 0 && (
        <section className="related">
          <p className="eyebrow">Useful follow-ups</p>
          <ul>{answer.related_questions.map((question) => <li key={question}>{question}</li>)}</ul>
        </section>
      )}

      <footer className="answer-actions">
        <span>Was this useful?</span>
        <button className={feedback === "helpful" ? "selected" : ""} onClick={() => rate("helpful")} aria-label="Mark helpful"><ThumbsUp size={16} /></button>
        <button className={feedback === "not_helpful" ? "selected" : ""} onClick={() => rate("not_helpful")} aria-label="Mark not helpful"><ThumbsDown size={16} /></button>
        <span className="action-spacer" />
        <button onClick={save} className={bookmarked ? "selected" : ""}>{bookmarked ? <Check size={16} /> : <Bookmark size={16} />} {bookmarked ? "Saved" : "Save"}</button>
        <button onClick={() => window.print()}><Printer size={16} /> Export PDF</button>
      </footer>
    </article>
  );
}

export default function Home() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [mobileNav, setMobileNav] = useState(false);
  const [sourceTiers, setSourceTiers] = useState<number[]>([1, 2]);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), [messages, loading]);

  async function submit(event?: FormEvent, starter?: string) {
    event?.preventDefault();
    const text = (starter || question).trim();
    if (!text || loading) return;
    setError(undefined);
    setQuestion("");
    setMessages((current) => [...current, { role: "user", question: text }]);
    setLoading(true);
    try {
      const answer = await askCopilot({ question: text, conversation_id: conversationId, source_tiers: sourceTiers });
      setConversationId(answer.conversation_id);
      setMessages((current) => [...current, { role: "assistant", answer }]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The copilot could not answer right now.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="Iowa Pork Compliance Copilot home">
          <span className="brand-mark">IA</span>
          <span><strong>Iowa Pork</strong><small>Compliance Copilot</small></span>
        </a>
        <nav className={mobileNav ? "open" : ""} aria-label="Main navigation">
          <a href="#ask">Ask a question</a>
          <a href="#how-it-works">How evidence works</a>
          <a href="#sources">Source policy</a>
        </nav>
        <div className="top-actions">
          <span className="iowa-pill"><span /> Iowa-first</span>
          <button className="menu-button" onClick={() => setMobileNav(!mobileNav)} aria-expanded={mobileNav} aria-label="Toggle menu">{mobileNav ? <X /> : <Menu />}</button>
        </div>
      </header>

      <div className="workspace" id="top">
        <aside className="sidebar" id="how-it-works">
          <p className="eyebrow">Evidence, then answer</p>
          <h2>Built to show its work.</h2>
          <p>This copilot searches an approved collection of official rules and guidance before it answers. It cannot rely on model memory.</p>
          <div className="trust-list">
            <div><span>01</span><p><strong>Iowa by default</strong><small>Jurisdiction is applied before search.</small></p></div>
            <div><span>02</span><p><strong>Official sources first</strong><small>Government material outranks industry guidance.</small></p></div>
            <div><span>03</span><p><strong>No evidence, no claim</strong><small>Missing facts and conflicts remain visible.</small></p></div>
          </div>
          <div className="filter-box" id="sources">
            <label>Sources included</label>
            {[{ tier: 1, label: "Government and statutes" }, { tier: 2, label: "Official and extension guidance" }, { tier: 3, label: "Industry guidance" }].map(({ tier, label }) => (
              <label className="check-row" key={tier}>
                <input type="checkbox" checked={sourceTiers.includes(tier)} onChange={() => setSourceTiers((current) => current.includes(tier) ? current.filter((value) => value !== tier) : [...current, tier])} />
                <span>{label}</span><small>Tier {tier}</small>
              </label>
            ))}
          </div>
          <p className="sidebar-note">For compliance preparation. Not legal advice, veterinary diagnosis, or emergency reporting.</p>
        </aside>

        <section className="chat" id="ask">
          {messages.length === 0 ? (
            <div className="welcome">
              <p className="eyebrow orange"><MessageSquareText size={15} /> Ask the compliance copilot</p>
              <h1>Know the rule.<br /><span>See the source.</span></h1>
              <p className="lede">Get an Iowa-specific answer, why it applies, and the records you should keep. If the evidence is not strong enough, the copilot will tell you.</p>
              <form className="ask-box" onSubmit={submit}>
                <Search size={21} aria-hidden="true" />
                <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about labor, manure, animal health, safety, or inspections…" aria-label="Compliance question" rows={3} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); submit(); } }} />
                <button type="submit" disabled={!question.trim()} aria-label="Ask question"><Send size={18} /></button>
              </form>
              <div className="starters" aria-label="Example questions">
                {STARTERS.map((starter) => <button key={starter} onClick={() => submit(undefined, starter)}>{starter}</button>)}
              </div>
              <div className="source-strip">
                <span>Searches approved sources from</span>
                <div><strong>IOWA DNR</strong><strong>USDA APHIS</strong><strong>U.S. DOL</strong><strong>OSHA</strong><strong>IOWA CODE</strong></div>
              </div>
            </div>
          ) : (
            <div className="conversation">
              <div className="conversation-heading">
                <p className="eyebrow">Current compliance question</p>
                <button onClick={() => { setMessages([]); setConversationId(undefined); }}>New question</button>
              </div>
              {messages.map((message, index) => message.role === "user" ? (
                <div className="user-message" key={index}><span>You asked</span><p>{message.question}</p></div>
              ) : message.answer ? <AnswerCard key={message.answer.id} answer={message.answer} /> : null)}
              {loading && <div className="loading-card" role="status"><span className="loader" /><div><strong>Checking official sources</strong><small>Retrieving, comparing, and validating citations…</small></div></div>}
              {error && <div className="error" role="alert">{error} <button onClick={() => setError(undefined)}>Dismiss</button></div>}
              <form className="follow-up" onSubmit={submit}>
                <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Add a fact or ask a follow-up…" rows={2} aria-label="Follow-up question" />
                <button disabled={loading || !question.trim()}><Send size={17} /> Ask</button>
              </form>
              <div ref={endRef} />
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
