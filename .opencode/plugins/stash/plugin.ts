/**
 * Stash plugin for opencode.
 *
 * Thin TS shim: each opencode event handler serializes its input and pipes it
 * into the matching Python hook script via stdin. All real work happens in
 * the `stashai.plugin` package (shipped via pip install stashai), reused
 * from every other agent's plugin.
 *
 * Bus events (session.*, message.*, file.*, etc.) are delivered through the
 * single `event` hook, NOT as keyed properties. Only the explicit allow-list
 * in opencode's `Hooks` interface (chat.message, tool.execute.*, etc.) is
 * dispatched by key.
 *
 * Install: reference this file from your opencode `plugin` config. See README.
 */

import { spawn, execSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { platform } from "node:os";

const PLUGIN_ROOT = dirname(fileURLToPath(import.meta.url));
const SCRIPTS = join(PLUGIN_ROOT, "scripts");
const RUN_SH = join(SCRIPTS, "_run.sh");

// opencode never emits a clean session-end signal. After this much idle time
// inside a live opencode process, treat the session as ended and fire
// on_session_end.py. Reset on every activity event (chat, tool, session.idle).
const IDLE_END_MS = 10 * 60 * 1000;

let idleTimer: ReturnType<typeof setTimeout> | null = null;
let activeSessionId = "";
let activeCwd = "";

function scheduleIdleEnd(sessionId: string): void {
  if (idleTimer) clearTimeout(idleTimer);
  if (!sessionId) return;
  activeSessionId = sessionId;
  idleTimer = setTimeout(() => {
    runHook("on_session_end.py", { session_id: sessionId, cwd: activeCwd });
    activeSessionId = "";
    idleTimer = null;
  }, IDLE_END_MS);
}

function cancelIdleEnd(): void {
  if (idleTimer) clearTimeout(idleTimer);
  idleTimer = null;
  activeSessionId = "";
}

function findPython(): string {
  // Resolve the python that has stashai installed.
  try {
    const out = execSync("py -3 -c \"import stashai; import sys; print(sys.executable)\"", { timeout: 5000 });
    return out.toString().trim();
  } catch {
    try {
      const out = execSync("python -c \"import stashai; import sys; print(sys.executable)\"", { timeout: 5000 });
      return out.toString().trim();
    } catch {
      return "python";
    }
  }
}

const PYTHON = findPython();

function runHook(script: string, payload: unknown, showOutput = false): void {
  // Fire-and-forget. We never want a flaky Stash backend to stall opencode.
  // detached + unref so the child belongs to its own process group and gets
  // reaped independently — otherwise zombies accumulate over long sessions.
  const hookName = script.replace(/\.py$/, "");
  try {
    const scriptPath = join(SCRIPTS, script);
    const isWin = platform() === "win32";
    const stdio: ["pipe", "pipe", "pipe"] | ["pipe", "ignore", "ignore"] =
      showOutput ? ["pipe", "pipe", "pipe"] : ["pipe", "ignore", "ignore"];

    let cmd: string;
    let args: string[];
    if (isWin) {
      cmd = PYTHON;
      args = ["-u", scriptPath];
    } else {
      cmd = "bash";
      args = [RUN_SH, hookName];
    }
    const child = spawn(cmd, args, {
      stdio,
      detached: !showOutput,
    });
    child.on("error", () => { /* bash missing / crash — swallow */ });
    if (showOutput) {
      child.stdout?.on("data", (chunk) => process.stderr.write(chunk));
      child.stderr?.on("data", (chunk) => process.stderr.write(chunk));
    }
    child.stdin?.write(JSON.stringify(payload));
    child.stdin?.end();
    if (!showOutput) {
      child.unref();
    }
  } catch {
    // spawn failed synchronously — swallow
  }
}

function extractText(parts: any[] | undefined): string {
  if (!Array.isArray(parts)) return "";
  return parts
    .filter((p) => p?.type === "text")
    .map((p) => p?.text ?? "")
    .join("\n");
}

export const StashPlugin = async ({
  project,
  worktree,
}: {
  project?: { worktree?: string };
  worktree?: string;
}) => {
  const cwd = worktree ?? project?.worktree ?? "";
  activeCwd = cwd;

  return {
    // Keyed hook: fires once per user message.
    "chat.message": async (
      _input: unknown,
      output: { message: any; parts: any[] },
    ) => {
      const text = extractText(output?.parts) || output?.message?.content || "";
      const sid = output?.message?.sessionID ?? "";
      runHook("on_prompt.py", { session_id: sid, prompt: text, cwd });
      scheduleIdleEnd(sid);
    },

    // Keyed hook: fires once per tool call, after execution.
    // Real signature: (input, output) where
    //   input = {tool, sessionID, callID, args}
    //   output = {title, output, metadata}
    "tool.execute.after": async (
      input: { tool: string; sessionID: string; callID: string; args: any },
      output: { title: string; output: string; metadata: any },
    ) => {
      runHook("on_tool_use.py", {
        session_id: input?.sessionID ?? "",
        tool_name: input?.tool ?? "",
        tool_input: input?.args ?? {},
        tool_response: {
          title: output?.title,
          output: output?.output,
          metadata: output?.metadata,
        },
        cwd,
      });
      scheduleIdleEnd(input?.sessionID ?? "");
    },

    // Generic bus-event dispatcher. Every session.* / message.* / file.* event
    // lands here — we switch on event.type.
    event: async ({ event }: { event: { type: string; properties?: any } }) => {
      switch (event?.type) {
        case "session.created": {
          const info = event.properties?.info;
          const sid = info?.id ?? "";
          runHook("on_session_start.py", { session_id: sid, cwd }, true);
          scheduleIdleEnd(sid);
          break;
        }
        case "session.deleted": {
          const info = event.properties?.info;
          runHook("on_session_end.py", { session_id: info?.id ?? "", cwd });
          cancelIdleEnd();
          break;
        }
        case "session.idle": {
          // session.idle fires every turn completion — refresh the idle timer
          // so the 10-min countdown only fires after real inactivity.
          scheduleIdleEnd(activeSessionId);
          break;
        }
      }
    },
  };
};

export default StashPlugin;
