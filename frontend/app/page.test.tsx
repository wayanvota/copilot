import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import Home from "./page";
import { askCopilot, getSources, getSourceUpdates } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  askCopilot: vi.fn(),
  bookmarkAnswer: vi.fn().mockResolvedValue(undefined),
  getSources: vi.fn().mockResolvedValue([]),
  getSourceUpdates: vi.fn().mockResolvedValue([]),
  sendFeedback: vi.fn().mockResolvedValue(undefined),
}));

const answer = {
  id: "answer-1",
  conversation_id: "conversation-1",
  short_answer: [{ text: "The cited rule applies conditionally.", citations: ["chunk-1"] }],
  why: [],
  rules: [],
  documentation: [],
  related_questions: [],
  applicability: { level: "medium" as const, explanation: "More farm facts are needed." },
  evidence_status: "verified" as const,
  missing_facts: ["Animal-unit capacity"],
  limitations: [],
  citations: [{
    id: "chunk-1",
    title: "Official source",
    agency: "Nebraska agency",
    url: "https://example.test/source",
    retrieved_at: "2026-08-24T12:00:00Z",
    excerpt: "Controlling source excerpt.",
  }],
  created_at: "2026-08-24T12:00:00Z",
};

describe("producer chat interface", () => {
  afterEach(() => cleanup());

  beforeEach(() => {
    localStorage.clear();
    vi.mocked(askCopilot).mockReset();
    vi.mocked(getSources).mockResolvedValue([]);
    vi.mocked(getSourceUpdates).mockResolvedValue([]);
  });

  it("starts with an accessible disabled submit control", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { name: /know the rule/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ask question" })).toBeDisabled();
    expect(screen.getByRole("textbox", { name: "Compliance question" })).toHaveAttribute("placeholder");
  });

  it("has no automatically detectable accessibility violations on the start screen", async () => {
    render(<Home />);
    const results = await axe.run(screen.getByRole("main"), {
      rules: { "color-contrast": { enabled: false } },
    });
    expect(results.violations.map((violation) => violation.id)).toEqual([]);
  });

  it("supports keyboard focus and keyboard activation", async () => {
    vi.mocked(askCopilot).mockResolvedValue(answer);
    const user = userEvent.setup();
    render(<Home />);

    await user.tab();
    expect(
      screen.getByRole("link", { name: "Nebraska Pork Compliance Copilot home" }),
    ).toHaveFocus();

    const example = screen.getByRole("button", {
      name: /permit before i build a new hog barn/i,
    });
    example.focus();
    await user.keyboard("{Enter}");

    expect(askCopilot).toHaveBeenCalledTimes(1);
    expect(await screen.findByText("The cited rule applies conditionally.")).toBeInTheDocument();
  });

  it("shows loading and then a cited answer for Unicode input", async () => {
    let resolveAnswer: (value: typeof answer) => void = () => undefined;
    vi.mocked(askCopilot).mockImplementation(() => new Promise((resolve) => { resolveAnswer = resolve; }));
    const user = userEvent.setup();
    render(<Home />);

    const input = screen.getByRole("textbox", { name: "Compliance question" });
    await user.type(input, "Does my barn near Niobrara need records? 🐖");
    await user.click(screen.getByRole("button", { name: "Ask question" }));
    expect(screen.getByRole("status")).toHaveTextContent("Checking official sources");

    resolveAnswer(answer);
    expect(await screen.findByText("The cited rule applies conditionally.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "View source 1" })).toBeInTheDocument();
  });

  it("keeps the interface usable after an API failure", async () => {
    vi.mocked(askCopilot).mockRejectedValue(new Error("The service is temporarily unavailable."));
    const user = userEvent.setup();
    render(<Home />);
    await user.click(screen.getByRole("button", { name: /permit before i build/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent("temporarily unavailable");
    await user.click(screen.getByRole("button", { name: "Dismiss" }));
    await waitFor(() => expect(screen.queryByRole("alert")).not.toBeInTheDocument());
    expect(screen.getByRole("textbox", { name: "Follow-up question" })).toBeEnabled();
  });

  it("restores a locally saved session after refresh", async () => {
    localStorage.setItem("nebraska-copilot-session-v2", JSON.stringify({
      messages: [{ role: "user", question: "Restored compliance question" }],
      sourceTiers: [1, 2],
      topic: "",
      farmContext: {},
    }));
    render(<Home />);
    expect(await screen.findByText("Restored compliance question")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "New question" })).toBeInTheDocument();
  });
});
