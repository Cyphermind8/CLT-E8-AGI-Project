How to use on a fresh chat

Open a new ChatGPT thread.

Paste the “New Chat Starter” (from console or primer/PRIMER.md), fill the ASK fields at the end, then add your question.

First line after paste: Mode: Ultrathink (or concise) + any time constraints (e.g., “10 minutes”).

Run the positive-control probe (I’ll include one automatically next time as a code block).

Rituals that keep the system crisp

At end of each working block (not later than 60–80 turns):

I produce a 12–20 line Episode Baton with: Objectives, Decisions, Open Loops, Artifacts, Next Ask.

You run python .\scripts\make_primer.py and start a new chat.

We carry over only the Baton + Ask; everything else stays in files.

When a new chat starts:

I show *_VERSION for critical tools (sanity).

I run one probe test (e.g., import + assert known behavior).

We proceed.

When logs get noisy:

I give you a path to the log and a two-line summary. No giant pastes.

When memory drifts:

We update primer/PROJECT_SEED.md (rare) or re-generate RUN_SEED.md (often).

If a specific preference should persist (e.g., “default Ultrathink”), say “Remember this” and I’ll store it using memory so it survives fresh chats.

Why this works

Token thrift by design: We never re-paste the whole history—only a compressed, curated seed.

Deterministic reboots: New chats begin with the same skeleton and a fresh delta, so behavior stays aligned.

Separation of concerns: Discussion is for decisions; data lives in files; baton carries just enough to bridge.

Low ceremony: One short command makes the primer; the rest is copy-paste.

Optional upgrades (when you want to go further)

Add a tests/test_primer.py that fails CI if PRIMER.md is stale (> 24h) or missing key sections.

Add a scripts/make_primer.ps1 wrapper that opens PRIMER.md in your editor and copies the starter to clipboard.

Track a canary metric: “accepted micro-edits per 50 cycles” and include it in RUN_SEED.md. If it flatlines, we reset earlier.

Bottom line: we’re not going to arm-wrestle the chat window anymore. We’ll work in episodes, prime new chats with curated seeds, and automate the baton so continuity is effortless. That takes the sting out of resets—and turns them into a feature.