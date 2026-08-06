"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import {
  Bookmark,
  Check,
  ChevronDown,
  ExternalLink,
  FileCheck2,
  MessageSquareText,
  Printer,
  Search,
  Send,
  ShieldCheck,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import { askCopilot, bookmarkAnswer, getSources, getSourceUpdates, sendFeedback } from "@/lib/api";
import type { ChatMessage, CitedClaim, CopilotAnswer, FarmContext, SourceSummary, SourceUpdate } from "@/lib/types";

const STARTERS = [
  "Do I need a permit before I build a new hog barn?",
  "How much land do I need to apply manure from my pigs?",
  "Can I hire a 15-year-old to clean a hog barn?",
  "What signs of African Swine Fever should employees report?",
];

const TOPICS = [
  ["", "All compliance topics"],
  ["permits", "Barns and permits"],
  ["manure", "Manure and environment"],
  ["labor", "Workers and youth labor"],
  ["animal_health", "Animal health"],
  ["safety", "Worker safety"],
  ["animal_welfare", "Animal care and markets"],
] as const;

const DEFAULT_FARM_CONTEXT: FarmContext = {
  operation_type: "unknown",
  manure_storage: "unknown",
  workers: "unknown",
  sells_into_california: "unknown",
};

type SavedAnswer = { question: string; answer: CopilotAnswer; savedAt: string };

function ClaimList({ claims, answer }: { claims: CitedClaim[]; answer: CopilotAnswer }) {
  if (!claims.length) return <p className="empty-section">No additional cited requirement was established.</p>;
  return (
    <ul className="claim-list">
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
    </ul>
  );
}

function AnswerCard({ answer, question, saved, onSave, onAsk }: {
  answer: CopilotAnswer;
  question: string;
  saved: boolean;
  onSave: () => void;
  onAsk: (question: string) => void;
}) {
  const [feedback, setFeedback] = useState<"helpful" | "not_helpful" | null>(null);
  const [comment, setComment] = useState("");
  const [showComment, setShowComment] = useState(false);

  async function rate(rating: "helpful" | "not_helpful") {
    setFeedback(rating);
    if (rating === "not_helpful") setShowComment(true);
    try {
      await sendFeedback(answer.id, rating);
    } catch {
      setFeedback(null);
    }
  }

  async function submitComment() {
    if (!comment.trim()) return;
    await sendFeedback(answer.id, "not_helpful", comment.trim());
    setShowComment(false);
  }

  async function save() {
    onSave();
    if (!saved) bookmarkAnswer(answer.id).catch(() => undefined);
  }

  const evidenceLabel = answer.evidence_status === "verified"
    ? "Authoritative sources found"
    : answer.evidence_status === "conflicting" ? "Sources conflict" : "Source evidence missing";

  return (
    <article className="answer-card" aria-label="Copilot answer">
      <div className="answer-topline">
        <span className={`evidence-badge ${answer.evidence_status}`}><ShieldCheck size={15} aria-hidden="true" />{evidenceLabel}</span>
        <div className="applicability-block">
          <span className={`confidence ${answer.applicability.level}`}>{answer.applicability.level} applicability</span>
          <small>{answer.applicability.explanation}</small>
        </div>
      </div>

      <section className="answer-section short-answer">
        <p className="eyebrow">Short answer</p>
        <ClaimList claims={answer.short_answer} answer={answer} />
      </section>

      {answer.missing_facts.length > 0 && (
        <section className="missing-facts" aria-label="Facts needed for this farm">
          <strong>Facts needed for your operation</strong>
          <p>The sources establish the rule, but these details could change how it applies:</p>
          <ul>{answer.missing_facts.map((fact) => <li key={fact}>{fact}</li>)}</ul>
        </section>
      )}

      <div className="answer-grid">
        <section className="answer-section"><h3>Why this applies</h3><ClaimList claims={answer.why} answer={answer} /></section>
        <section className="answer-section"><h3>Rules that apply</h3><ClaimList claims={answer.rules} answer={answer} /></section>
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
        {answer.citations.length === 0 && <p className="empty-section">No source was strong enough to cite for this answer.</p>}
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
          <div>{answer.related_questions.map((item) => <button key={item} onClick={() => onAsk(item)}>{item}</button>)}</div>
        </section>
      )}

      <footer className="answer-actions">
        <span>Was this useful?</span>
        <button className={feedback === "helpful" ? "selected" : ""} onClick={() => rate("helpful")} aria-label="Mark helpful"><ThumbsUp size={16} /></button>
        <button className={feedback === "not_helpful" ? "selected" : ""} onClick={() => rate("not_helpful")} aria-label="Mark not helpful"><ThumbsDown size={16} /></button>
        <span className="action-spacer" />
        <button onClick={save} className={saved ? "selected" : ""}>{saved ? <Check size={16} /> : <Bookmark size={16} />} {saved ? "Saved on this device" : "Save"}</button>
        <button onClick={() => window.print()}><Printer size={16} /> Export PDF</button>
      </footer>
      {showComment && (
        <div className="feedback-comment">
          <label htmlFor={`feedback-${answer.id}`}>What was missing or wrong?</label>
          <textarea id={`feedback-${answer.id}`} value={comment} onChange={(event) => setComment(event.target.value)} rows={2} />
          <button onClick={submitComment} disabled={!comment.trim()}>Send feedback</button>
        </div>
      )}
    </article>
  );
}

export default function Home() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [sourceTiers, setSourceTiers] = useState<number[]>([1, 2]);
  const [topic, setTopic] = useState("");
  const [farmContext, setFarmContext] = useState<FarmContext>(DEFAULT_FARM_CONTEXT);
  const [savedAnswers, setSavedAnswers] = useState<SavedAnswer[]>([]);
  const [sources, setSources] = useState<SourceSummary[]>([]);
  const [updates, setUpdates] = useState<SourceUpdate[]>([]);
  const [hydrated, setHydrated] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    try {
      const session = JSON.parse(localStorage.getItem("iowa-copilot-session-v2") || "null");
      if (session) {
        setMessages(session.messages || []);
        setConversationId(session.conversationId);
        setSourceTiers(session.sourceTiers || [1, 2]);
        setTopic(session.topic || "");
        setFarmContext({ ...DEFAULT_FARM_CONTEXT, ...(session.farmContext || {}) });
      }
      setSavedAnswers(JSON.parse(localStorage.getItem("iowa-copilot-saved-v2") || "[]"));
    } catch {
      localStorage.removeItem("iowa-copilot-session-v2");
    }
    setHydrated(true);
    getSources().then(setSources).catch(() => undefined);
    getSourceUpdates().then(setUpdates).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    localStorage.setItem("iowa-copilot-session-v2", JSON.stringify({ messages, conversationId, sourceTiers, topic, farmContext }));
  }, [hydrated, messages, conversationId, sourceTiers, topic, farmContext]);

  useEffect(() => {
    if (hydrated) localStorage.setItem("iowa-copilot-saved-v2", JSON.stringify(savedAnswers));
  }, [hydrated, savedAnswers]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  async function submit(event?: FormEvent, suppliedQuestion?: string) {
    event?.preventDefault();
    const text = (suppliedQuestion || question).trim();
    if (!text || loading) return;
    setError(undefined);
    setQuestion("");
    setMessages((current) => [...current, { role: "user", question: text }]);
    setLoading(true);
    try {
      const contextIsEmpty = JSON.stringify(farmContext) === JSON.stringify(DEFAULT_FARM_CONTEXT);
      const answer = await askCopilot({
        question: text,
        conversation_id: conversationId,
        source_tiers: sourceTiers,
        topics: topic ? [topic] : [],
        farm_context: contextIsEmpty ? undefined : farmContext,
      });
      setConversationId(answer.conversation_id);
      setMessages((current) => [...current, { role: "assistant", answer }]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The copilot could not answer right now.");
    } finally {
      setLoading(false);
    }
  }

  function toggleSaved(questionText: string, answer: CopilotAnswer) {
    setSavedAnswers((current) => current.some((item) => item.answer.id === answer.id)
      ? current.filter((item) => item.answer.id !== answer.id)
      : [{ question: questionText, answer, savedAt: new Date().toISOString() }, ...current]);
  }

  function setContext<K extends keyof FarmContext>(key: K, value: FarmContext[K]) {
    setFarmContext((current) => ({ ...current, [key]: value }));
  }

  const profileFacts = Object.entries(farmContext).filter(([, value]) => value && value !== "unknown").length;
  const latestRetrieved = sources.length
    ? new Date(Math.max(...sources.map((source) => new Date(source.retrieved_at).getTime())))
    : undefined;

  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="Iowa Pork Compliance Copilot home">
          <span className="brand-mark">IA</span><span><strong>Iowa Pork</strong><small>Compliance Copilot</small></span>
        </a>
      </header>

      <div className="workspace" id="top">
        <aside className="sidebar">
          <p className="eyebrow">Evidence, then answer</p>
          <h2>Built to show its work.</h2>
          <p>This copilot searches approved rules and guidance before it answers. It cannot rely on model memory.</p>

          <details className="control-panel">
            <summary>Farm facts <small>{profileFacts ? `${profileFacts} added` : "optional"}</small></summary>
            <div className="form-grid">
              <label>County<input value={farmContext.county || ""} onChange={(event) => setContext("county", event.target.value || undefined)} placeholder="Example: Story" /></label>
              <label>Operation<select value={farmContext.operation_type} onChange={(event) => setContext("operation_type", event.target.value as FarmContext["operation_type"])}><option value="unknown">Not specified</option><option value="confinement">Confinement</option><option value="open_feedlot">Open feedlot</option><option value="mixed">Mixed</option></select></label>
              <label>Animal-unit capacity<input type="number" min="1" value={farmContext.animal_unit_capacity || ""} onChange={(event) => setContext("animal_unit_capacity", event.target.value ? Number(event.target.value) : undefined)} placeholder="If known" /></label>
              <label>Manure storage<select value={farmContext.manure_storage} onChange={(event) => setContext("manure_storage", event.target.value as FarmContext["manure_storage"])}><option value="unknown">Not specified</option><option value="formed">Formed structure</option><option value="unformed">Unformed structure</option><option value="lagoon">Lagoon</option><option value="dry">Dry manure</option></select></label>
              <label>Workers<select value={farmContext.workers} onChange={(event) => setContext("workers", event.target.value as FarmContext["workers"])}><option value="unknown">Not specified</option><option value="family">Family only</option><option value="nonfamily">Nonfamily</option><option value="both">Both</option></select></label>
              <label>California sales<select value={farmContext.sells_into_california} onChange={(event) => setContext("sells_into_california", event.target.value as FarmContext["sells_into_california"])}><option value="unknown">Not specified</option><option value="yes">Yes</option><option value="no">No</option></select></label>
            </div>
            <button className="text-button" onClick={() => setFarmContext(DEFAULT_FARM_CONTEXT)}>Clear farm facts</button>
          </details>

          <details className="control-panel">
            <summary>Search scope <small>{topic ? "filtered" : "all topics"}</small></summary>
            <label className="select-label">Topic<select value={topic} onChange={(event) => setTopic(event.target.value)}>{TOPICS.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
            <div className="tier-list">
              {[{ tier: 1, label: "Government and statutes" }, { tier: 2, label: "Official and extension guidance" }, { tier: 3, label: "Industry guidance" }].map(({ tier, label }) => (
                <label className="check-row" key={tier}>
                  <input type="checkbox" checked={sourceTiers.includes(tier)} disabled={sourceTiers.length === 1 && sourceTiers.includes(tier)} onChange={() => setSourceTiers((current) => current.includes(tier) ? current.filter((value) => value !== tier) : [...current, tier])} />
                  <span>{label}</span><small>Tier {tier}</small>
                </label>
              ))}
            </div>
          </details>

          <details className="control-panel">
            <summary>Source status <small>{sources.length ? `${sources.length} sources` : "loading"}</small></summary>
            <p className="panel-copy">{latestRetrieved ? `Latest retrieval: ${latestRetrieved.toLocaleDateString()}.` : "Source status is unavailable."}</p>
            <p className="panel-copy">{updates.length ? `${updates.length} sources have multiple stored versions available for review.` : "No source has two distinct stored versions yet, so the copilot cannot claim what changed."}</p>
          </details>

          {savedAnswers.length > 0 && (
            <details className="control-panel">
              <summary>Saved answers <small>{savedAnswers.length}</small></summary>
              <div className="saved-list">{savedAnswers.map((item) => <button key={item.answer.id} onClick={() => { setMessages([{ role: "user", question: item.question }, { role: "assistant", answer: item.answer }]); setConversationId(item.answer.conversation_id); }}>{item.question}</button>)}</div>
            </details>
          )}
          <p className="sidebar-note">Farm facts are sent with each question but are not added to server conversation history. They and saved answers remain on this device. Do not enter names, exact addresses, or confidential records.</p>
        </aside>

        <section className="chat" id="ask">
          {messages.length === 0 ? (
            <div className="welcome">
              <p className="eyebrow orange"><MessageSquareText size={15} /> Ask the compliance copilot</p>
              <h1>Know the rule.<br /><span>See the source.</span></h1>
              <p className="lede">Get an Iowa-specific answer, why it applies, which farm facts could change it, and the records you should keep.</p>
              <form className="ask-box" onSubmit={submit}>
                <Search size={21} aria-hidden="true" />
                <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about labor, manure, animal health, safety, or inspections…" aria-label="Compliance question" rows={3} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); submit(); } }} />
                <button type="submit" disabled={!question.trim()} aria-label="Ask question"><Send size={18} /></button>
              </form>
              <div className="starters" aria-label="Example questions">{STARTERS.map((starter) => <button key={starter} onClick={() => submit(undefined, starter)}>{starter}</button>)}</div>
              <div className="source-strip"><span>Searches approved sources from</span><div><strong>IOWA DNR</strong><strong>USDA APHIS</strong><strong>U.S. DOL</strong><strong>OSHA</strong><strong>IOWA CODE</strong></div></div>
            </div>
          ) : (
            <div className="conversation">
              <div className="conversation-heading"><p className="eyebrow">Current compliance question</p><button onClick={() => { setMessages([]); setConversationId(undefined); }}>New question</button></div>
              {messages.map((message, index) => message.role === "user" ? (
                <div className="user-message" key={index}><span>You asked</span><p>{message.question}</p></div>
              ) : message.answer ? (
                <AnswerCard key={message.answer.id} answer={message.answer} question={messages[index - 1]?.question || "Saved answer"} saved={savedAnswers.some((item) => item.answer.id === message.answer?.id)} onSave={() => toggleSaved(messages[index - 1]?.question || "Saved answer", message.answer!)} onAsk={(item) => submit(undefined, item)} />
              ) : null)}
              {loading && <div className="loading-card" role="status"><span className="loader" /><div><strong>Checking official sources</strong><small>Retrieving, comparing, and validating citations…</small></div></div>}
              {error && <div className="error" role="alert">{error} <button onClick={() => setError(undefined)}>Dismiss</button></div>}
              <form className="follow-up" onSubmit={submit}><textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Add a fact or ask a follow-up…" rows={2} aria-label="Follow-up question" /><button disabled={loading || !question.trim()}><Send size={17} /> Ask</button></form>
              <div ref={endRef} />
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
