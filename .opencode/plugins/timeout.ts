import type { Plugin } from "@opencode-ai/plugin"

// OpenCode plugin — ensures bash/shell tool commands have at least a 1-hour timeout (3,600,000 ms).
// Prevents video generation, audio synthesis, and Playwright renders from being killed prematurely.

export const TimeoutPlugin: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      const tool = String(input?.tool ?? "").toLowerCase()
      if (tool !== "bash" && tool !== "shell") return
      const args = output?.args
      if (!args || typeof args !== "object") return

      const ONE_HOUR_MS = 3600000 // 1 hour
      const currentTimeout = Number((args as Record<string, unknown>).timeout) || 0
      if (currentTimeout < ONE_HOUR_MS) {
        ;(args as Record<string, unknown>).timeout = ONE_HOUR_MS
      }
    },
  }
}

export default TimeoutPlugin
