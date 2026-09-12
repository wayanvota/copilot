import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: { "@": fileURLToPath(new URL(".", import.meta.url)) },
  },
  test: {
    include: ["app/**/*.test.tsx", "lib/**/*.test.ts"],
    environment: "jsdom",
    environmentOptions: { jsdom: { url: "http://localhost/copilot/" } },
    setupFiles: ["./vitest.setup.ts"],
    restoreMocks: true,
  },
});
