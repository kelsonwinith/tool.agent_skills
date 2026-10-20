# Agent Skills

A collection of portable, composable agent skills for end-to-end software engineering workflows.

## Full-Loop Workflow (`/project-workflow`)

Install **`project-workflow`** once and it will automatically detect your project's tech stack and bootstrap any missing companion skills on first run:

```bash
npx skills add kelsonwinith/tool.agent_skills --skill project-workflow
```

Then run `/project-workflow [what you want to add, update, or remove]`:

```text
/project-workflow "add order cancellation"
   │
   ├─► Stage 0: Bootstrap               (auto-detect stack & install missing companion skills)
   ├─► Stage 1: /project-grill          (design-tree interview + glossary/requirement check) ──► [PAUSE FOR APPROVAL]
   ├─► Stage 2: /project-documentation  (sync docs/, glossary, ADRs + run doc linters)       ──► [PAUSE FOR APPROVAL]
   ├─► Stage 3: /project-plan           (scan layers + output ONLY ### Proposed File Tree)   ──► [PAUSE FOR APPROVAL]
   └─► Stage 4: /project-implement      (write code per stack architecture + run checks)     ──► [FINAL SIGN-OFF]
```

## Skills

| Skill | Role | What it does |
| :--- | :--- | :--- |
| [`project-workflow`](skills/project-workflow/) | **Orchestrator** | Master `/project-workflow` entrypoint. Auto-installs missing companion/stack skills and drives the 4 approval-gated stages in sequence. |
| [`project-grill`](skills/project-grill/) | **Stage 1 — Grill** | Silently inspects code & `docs/`, flags terminology or requirement conflicts, asks numbered design-tree questions with `(Recommended)` proposals, and outputs an Agreed Design Summary. |
| [`project-documentation`](skills/project-documentation/) | **Stage 2 — Docs** | Documentation guardian: canonical ubiquitous-language glossary (`docs/context/001-ubiquitous-language.md` bound to code identifiers), numbered `docs/` tree, ADRs, and deterministic validators. |
| [`project-plan`](skills/project-plan/) | **Stage 3 — Plan** | Scans existing project layers to prevent duplication, schedules glossary-driven code renames, and outputs **only** the annotated `### Proposed File Tree` (`[NEW]`, `[UPDATE]`, `[REUSE]`, `[PROMOTE]`, `[DELETE]`). |
| [`project-implement`](skills/project-implement/) | **Stage 4 — Implement** | Executes the approved `### Proposed File Tree` following the active stack architecture skill and canonical glossary names, then runs code and documentation verification. |
| [`project-react-architecture`](skills/project-react-architecture/) | **Stack — React/Next.js** | Layered React/Next.js SSR architecture with zero inline `className` in views/routes, strict root vs. feature scoping, `RequestState<T>`, and 5-line function doc blocks. |
| [`project-go-architecture`](skills/project-go-architecture/) | **Stack — Go Hexagonal** | Strict Go Hexagonal Architecture (`Fiber v3` + `GORM` + `PostgreSQL` + `JWT` + `Swaggo`) with 3-segment filenames, 6-section banners, and explicit 3-block import aliasing. |

## Install

Install the full workflow orchestrator (which auto-installs the rest when invoked):

```bash
npx skills add kelsonwinith/tool.agent_skills --skill project-workflow
```

Or install individual skills directly:

```bash
npx skills add kelsonwinith/tool.agent_skills --skill project-grill
npx skills add kelsonwinith/tool.agent_skills --skill project-documentation
npx skills add kelsonwinith/tool.agent_skills --skill project-plan
npx skills add kelsonwinith/tool.agent_skills --skill project-implement
npx skills add kelsonwinith/tool.agent_skills --skill project-react-architecture
npx skills add kelsonwinith/tool.agent_skills --skill project-go-architecture
```

## Update

Update every installed skill to its latest version:

```bash
npx skills update
```

Update specific skills by name:

```bash
npx skills update project-workflow
npx skills update project-workflow project-grill project-documentation project-plan project-implement
```

Scope flags: `-p` project-level only, `-g` global only, `-y` skip the scope prompt.

```bash
npx skills update -p -y     # project-level skills, no prompt
npx skills update -g -y     # global skills, no prompt
```

See what's installed, or remove a skill:

```bash
npx skills list
npx skills remove project-workflow
```

## License

MIT
