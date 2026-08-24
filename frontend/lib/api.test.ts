import { afterEach, describe, expect, it, vi } from "vitest";

import { askCopilot } from "./api";

describe("API error handling", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("replaces browser network errors with useful producer guidance", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(askCopilot({ question: "Do I need a permit?" })).rejects.toThrow(
      "could not reach the source service",
    );
  });

  it("preserves a controlled backend error message", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ detail: "Too many questions. Try again in one minute." }),
      { status: 429, headers: { "Content-Type": "application/json" } },
    )));
    await expect(askCopilot({ question: "Do I need a permit?" })).rejects.toThrow(
      "Too many questions",
    );
  });
});
