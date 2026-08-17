---
type: concept
status: evergreen
tags: [principle]
---

# Parse, Don't Validate (Alexis King, 2019)

Source: https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/

**Thesis:** Push constraint-checking into types at the system boundary. A function
should turn less-structured input into more-structured output and *encode what it
learned in the return type* — don't just check and throw the knowledge away.

## Parse vs. Validate
- **Validate** = check a condition, return `()` / `void` / `bool`. The proof is
  discarded; downstream callers can't rely on it and re-check.
- **Parse** = consume input, return a *refined type* that makes the guarantee
  accessible to all callers. The proof travels with the data.
- Canonical example: `validateNonEmpty :: [a] -> IO ()` (throws) vs
  `parseNonEmpty :: [a] -> Maybe (NonEmpty a)` (returns the evidence).

## Why validation is a smell — "shotgun parsing"
Input-checking scattered and interleaved with processing logic. Consequences:
- Errors discovered late mean invalid input was *already partially processed* →
  state is unpredictable, rollback is hard.
- Redundant checks drift out of sync; no single source of truth.

## The lever: make illegal states unrepresentable
`head` evolution shows the spectrum:
- `[a] -> a` — partial, can't implement totally.
- `[a] -> Maybe a` — total, but pushes redundant checks onto every caller.
- `NonEmpty a -> a` — total, no caller checks, the precondition is a type. If the
  upstream source later permits emptiness, the type must change → **the compiler
  flags every affected call site**.

## Rules of thumb
1. **Parse once, at the boundary.** External/untrusted data is refined where it
   enters; interior code trusts the types.
2. **Use precise types by construction** (e.g. `Map` not `[(k,v)]`; `NonEmpty`
   not `[]`).
3. **Write for the types you wish you had**, then refactor data structures
   upward; let the compiler drive you to all the changes.
4. **Avoid redundant/denormalized data** — one source of truth behind an
   abstraction boundary.
5. **Be suspicious of functions returning `m ()`** whose main purpose is to raise
   errors — usually a parser is hiding there.
6. **Multi-pass / context-sensitive parsing is fine** — using already-parsed data
   to guide later parsing is not shotgun parsing.

**One-liner:** Don't write a function that *checks* X is valid; write one that
*returns a type that can only hold valid X*, and call it at the edge.
