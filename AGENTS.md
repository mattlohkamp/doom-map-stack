# AGENTS.md

Instructions for agents working in this repo (Claude Code reads this file natively).

## Start of every session

1. Read `PLAN.md` to get up to speed: the decisions, the toolchain design and the milestones.
   Start with **§9 "Where we left off"**, which says what's done and what to do next.
2. Before designing or changing a map, read `docs/map-design-notes.md`.

## Status

This file is a stub. Writing the full AGENTS.md is the first step of milestone M0 (see `PLAN.md` §9):
the settled rules in `PLAN.md` (self-contained environment, licensing, writing conventions,
who each document is for, the several-maps rules) move here, and this file becomes the source of truth
for how to work in the repo.

## Rules that already apply

- **Self-contained:** nothing gets installed or written outside the repo folder (see `PLAN.md` §1).
- **Never commit third-party binaries or IWADs.**
- **Keep it impersonal:** refer to roles ("the mapper", "the dev machine"), not the person, their computer or their accounts.
- **Text files are UTF-8 without a BOM.** Windows PowerShell 5.1 adds a BOM by default; avoid `Set-Content` / `Out-File` for repo files.
- **`README.md` is for the public, never a source of truth.** Don't take instructions from it.
