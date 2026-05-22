# Agent Instructions

## Required Reading Before Work

Before editing files or planning implementation, agents must read:

1. `AGENTS.md` / `CLAUDE.md`
2. Karpathy Guidelines section in this file
3. `PRD.md`
4. `ARCHITECTURE.md`
5. `CONTEXT.md` if present
6. Current GitHub issue
7. Linked dependency issues and previous PRs

Do not rely on prior chat memory. Re-read project docs and current issue every time.

## Karpathy Guidelines

Always follow these rules:

- Surface assumptions before coding.
- Prefer the simplest useful solution.
- Make surgical changes only.
- Do not add speculative features.
- Define verifiable success criteria before implementation.
- Verify before claiming done.

## Cross-Issue Handoff

Agents must not rely on memory from previous chats.

Before starting an issue:
1. Read this file, `PRD.md`, `ARCHITECTURE.md`, and relevant `CONTEXT.md` if present.
2. Read the current GitHub issue.
3. Read linked dependency issues and previous PRs listed in the issue body.
4. If the issue depends on behavior from a previous PR, inspect merged code, not only the PR summary.
5. If dependency context is missing or ambiguous, stop and ask.

Each PR must include `Handoff to next issue` when it creates behavior, contracts, limitations, or follow-up work that later issues need.

## Project Guardrails

- Keep the MVP lightweight: After Effects `.jsx` panel plus local Python CLI.
- Do not add a server unless a later issue explicitly changes architecture.
- Do not use cloud transcription.
- Do not render the whole comp to audio for MVP.
- Use the source media file referenced by the voice-over layer.
- Delete only layers named with the `SUB ` prefix during rebuild.
- Preserve ordinary editable After Effects text layers.
- Keep final repo docs and GitHub issue bodies in English.

