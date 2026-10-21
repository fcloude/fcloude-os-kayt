# Decisions

## 2026-10-18
- KAYT is built separately from the FCLOUDE OS customization (KAYT first, OS later).
- Repo name: fcloude-os-kayt (private). Differs from the roadmap's `fcloude-kayt`; intentional.
- Language: Python.
- Model strategy: mock provider first; one real provider (Ollama) only after security tests pass.
- Dev environment: Windows 11 host, no VM for now. Linux testing (VM or WSL) deferred to Goals 6-8.
- Ubuntu 24.04 LTS is the proposed OS base; re-verify before ISO work.
- License: undecided (MIT vs Apache-2.0).

## Deferred (do not build in MVP)
Shell execution, root/admin access, arbitrary file search, voice, telemetry,
multi-agent, custom kernel/updater/package manager.

## Known gaps (from Milestone 2.4)
- Symlinks are followed by is_file(). Fix in Milestone 3.2 (grants): resolve once, read from the opened handle.
- Whitespace-only files are accepted as non-empty. Revisit later.
- Size limit: 100 KB = 102,400 bytes.
- Permission-denied branch exists but is not tested on Windows.
- Question is required even when --file is given (product decision, deferred).
- Symlink defence verified 2026-10-20 on Windows 11, Python 3.13 (passed, not skipped); re-verify on Linux/WSL in Goal 6.
- O_NOFOLLOW constrains only the final path component; parent symlinks rely on resolve().
- O_NOFOLLOW and O_NONBLOCK are inert on Windows, so the early is_symlink() check is the only guard there.
- Junctions are rejected only by the "not a regular file" branch (accidental, not designed).
- Session equals process: the CLI builds a throwaway GrantStore per invocation, so grants die with the process; revisit when a session spans several turns.
- Grant expiry: grants are session-only and expire when clear() ends the session; there are no timestamps or TTLs, and a cleared id is never reused.
