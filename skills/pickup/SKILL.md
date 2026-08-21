---
name: pickup
description: Orient at the start of a session that will touch the knowledge-base vault — the durable cross-session memory for engineering work (a separate git repo / Obsidian vault spanning every project I work on). Reads the current orientation document for the thread being picked up, audits it against the one before it to catch anything that vanished without a disposition, judges how fresh each live item actually is, and opens with what needs the owner's decision. Read-only; it ends in plan mode. Invoke at the start of a session, when resuming work someone else handed off, or when asked to "pick up where we left off", "get oriented", "what's the state of X", or "read the handoff".
---

# pickup — orient before you write

The counterpart to `context-dump`. A handoff wrote an orientation; you read it, check it, and say what the
owner needs to decide. **You write nothing.**

The audit lives here because you have the budget the handing-off agent did not, and no stake in the answer.

## Do

1. **Resolve where you are.**

   ```bash
   cd "$(lipika vault-config path)"
   git log -12 --name-only --pretty=format:'%h %ad %s' --date=short -- workstreams/
   lipika pass-log active                     # is another agent in here right now?
   ```

   Name the thread and let the owner redirect you. If the task described matches no live workstream, say
   so — that is usually a new thread rather than a wrong guess.

2. **Read the newest orientation, and only that one.**
   `workstreams/<ws>/orientation/` sorts by name; the last is current. Older ones are records of past
   moments, not rival accounts of the present. Read one.

3. **Audit it against its predecessor.**

   ```bash
   lipika orientation-audit workstreams/<ws>     # exit 1 = an item vanished with no disposition
   ```

   Every item live in the previous orientation must appear as carried, resolved, dropped or escalated. A
   silent disappearance is the one failure this document class has. Report what the check found; do not
   fix it by hand — the correction goes in your own dump later.

4. **Judge how fresh each item is.** More recent supersedes older and is trusted more — **a prior, not a
   rule**: reach back into dumps when the newest document is thin or wrong.

   **Weigh each item's own `as-of`, not the document's date.** An item carried unchanged through six
   handoffs inherits today's filename and reads as fresh. A stale GATE with a checkable death condition is
   worth one command before you trust it.

5. **Ask whether a portrait is missing.** You are the agent reading cold, so you are the one who feels it:
   is there a system here you must work on that nothing describes?

   ```bash
   lipika architecture-candidates          # traces cited from 2+ workstreams with no architecture node
   ```

   The check is mechanical and your own experience is not; report both. **Recommend, never write** —
   `architecture/` is the owner's, because an agent-authored portrait becomes the most-linked document in
   the vault with no dated evidence positioned to contradict it. Carry pointers: which system, which
   traces back it, which dumps disagree, and the question a portrait would answer.

6. **Open with what the owner needs, then enter plan mode.** Your first message is, in this order:

   - **Needs a decision** — every ESCALATED item. This is the most useful thing you will say; put it first.
   - **Where this is** — two or three sentences, from the orientation. Not a summary of the whole thread.
   - **What the audit found** — drops caught, or that it was clean, with the exit code.
   - **Stale live items** — anything whose `as-of` argues it should be re-checked before being relied on.
   - **A missing portrait**, if you found one.

   Then call `EnterPlanMode`. Nothing is written yet and nothing is agreed; the plan is where that
   happens.

## Don't

- **Don't read every dump.** The orientation exists so you do not have to. Reach into one for evidence
  behind a specific item, not to reconstruct the story.
- **Don't read two orientations as two accounts of now.** The older one is a record of a past moment.
- **Don't fix what the audit found.** You are read-only. It goes in your report, and into your dump later.
- **Don't write, move or edit anything** — no records, no views, and not `architecture/`.
- **Don't skip the escalations** because they look like context. They are the reason a human is reading.

## When there is no orientation

A workstream still in the old task shape, or a thread nobody has handed off yet, has no `orientation/`.
Say so plainly, read the routing note and the newest two or three dumps instead, and report that the first
handoff out of this session will create one. Do not build one yourself: it would be a view written by
someone who has not done the work.
