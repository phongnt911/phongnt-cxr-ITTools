# AGENTS.md — Development Guidelines & Agent Configuration

This repository integrates the **Ponytail + Superpowers + LeanCTX** engineering triad to guarantee minimal bloat, rigorous engineering workflows, and lean context efficiency.

All AI coding assistants (Antigravity, Gemini CLI, Claude Code, Cursor, Codex, OpenCode, Windsurf) working on **IT Tool SAGS-CXR 2026** MUST strictly adhere to these instructions.

---

## 1. 🐎 Ponytail: Lazy Senior Dev Mode (Anti-Over-Engineering)

> **"The best code is the code never written. Solve the whole problem with the least new code."**

### Before You Write
- Read the task and the surrounding code it touches.
- Determine the true blast radius: callers, tests, UI listeners, IPC sockets, and config.
- Never add abstractions, extra wrappers, speculative configuration, or "future-proofing" nobody asked for.
- Deletion and reuse beat addition.

### The Solution Ladder
Evaluate any code change against these rungs in order:
1. **Does it need to exist?** Skip unnecessary options and boilerplate (YAGNI).
2. **Already in this codebase?** Reuse existing helpers (`security_utils.py`, `runtime_diagnostics.py`, `web_api.py`, etc.).
3. **Python Standard Library or Native Windows API?** Prefer built-in modules (`pathlib`, `subprocess`, `ctypes`, `winreg`, `socket`) over adding new packages.
4. **Already installed dependency?** Use what's in `.venv` / PyInstaller spec; never add dependencies for a trivial task.
5. **Can it be a clear one-liner?** Write a clean, readable one-liner.
6. **Otherwise:** Implement the absolute minimum code that works correctly.

### Non-Negotiable Safety
- **Never cut:** trust-boundary validation, sanitization of inputs passed to shell/cmd/powershell, error handling preventing data loss, UAC elevation checks, or accessibility.
- **Root-cause fixes:** When fixing a bug, identify and resolve the root cause in shared code rather than patching symptoms downstream.
- **Accountability footer:** Conclude non-trivial code modifications with 1-2 lines detailing what was intentionally skipped/deferred and any residual risks or constraints.

---

## 2. ⚡ Superpowers: Disciplined Engineering Workflows

> **"Structure beats improvisation. Think, plan, verify."**

Workspace skills are located under `.agents/skills/`.

### Core Workflow Rules
1. **Think Before Coding (Brainstorming & Planning):**
   - For any multi-step feature or architectural change, first brainstorm the approach and specify the plan before touching code.
   - Use `.agents/skills/brainstorming` and `.agents/skills/writing-plans`.
2. **Test-Driven Development (TDD):**
   - Follow Red-Green-Refactor when introducing new features or fixing non-trivial bugs.
   - Maintain regression suites in `tests/`.
   - Use `.agents/skills/test-driven-development`.
3. **Systematic Debugging:**
   - Investigate issues with evidence and reproduction tests instead of guessing.
   - Trace logs via live drawer or `runtime_diagnostics.py`.
   - Use `.agents/skills/systematic-debugging`.
4. **Verification Before Completion:**
   - Always run the test suite (`python -m unittest discover tests`) before completing any task.
   - Verify zero regressions across core modules (Printer Fix, IP Manager, Fluent Cleaner, Startup, BitLocker, etc.).
   - Use `.agents/skills/verification-before-completion`.

---

## 3. 🎯 LeanCTX: Context Gateway & Optimization

> **"High signal, zero noise. Fewer round trips beat smaller outputs."**

Context gateway skills are available under `.agents/skills/lean-ctx` and `.agents/skills/lean-ctx-review`.

### Context Principles
1. **Fewer Round Trips Beat Smaller Outputs:**
   - One decisive, well-targeted tool call that resolves the question is vastly superior to multiple fragmented queries.
2. **Zero Busy-Polling:**
   - Never write shell `sleep` loops or repetitive polling commands to check status; utilize reactive triggers and bounded checks.
3. **Focused File Reading:**
   - Target specific line ranges, symbol definitions, or diffs rather than reading whole files unnecessarily.
4. **Clean Workspace State:**
   - Keep generated test artifacts, caches, and dumps inside ignored locations (`ITTools/scratch/` or `.system_generated/`).

---

## 4. 🛠️ Project Standards: IT Tool SAGS-CXR 2026

- **Runtime:** Python 3.10+ on Windows 10 / 11 / Server (x64).
- **Architecture:** Single-file Portable Windows App (`pywebview` Edge WebView2 frontend + Python Backend + local IPC socket `127.0.0.1:49285`).
- **Process Isolation:** All background processes (`subprocess.Popen` / `subprocess.run`) MUST use `CREATE_NO_WINDOW` and clean argument escaping (via `security_utils.py`) to prevent terminal flashing.
- **Testing:** Verify all changes by executing:
  ```bash
  python -m unittest discover -s tests -p "test_*.py"
  ```

