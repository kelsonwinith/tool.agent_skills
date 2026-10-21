# Agent Skills

A collection of portable, composable agent skills for end-to-end software engineering workflows.

## Full-Loop Workflow (`/project-workflow`)

Install **`project-workflow`** once and it will automatically detect your project's tech stack and bootstrap any missing companion skills on first run:

```bash
npx skills add kelsonwinith/tool.agent_skills --skill project-workflow
```

Calling `/project-workflow` **directly launches the local website** at `http://localhost:4321` where you enter your prompt directly in the browser:

```text
/project-workflow
   │
   ├─► Step 0: Directly launches website at http://localhost:4321
   │          (User enters prompt & configures stages directly on the website)
   │
   ├─► Stage 1: /project-grill     (🔒 FORCED: design-tree interview + conflict check)  ──► [WEB APPROVAL]
   ├─► Stage 2: /project-documentation (TOGGLEABLE: sync docs/, flows, ADRs + linters)  ──► [WEB APPROVAL]
   ├─► Stage 3: /project-plan      (TOGGLEABLE: scan layers + ONLY ### Proposed File Tree)──► [WEB APPROVAL]
   └─► Stage 4: /project-implement (🔒 FORCED: code implementation & verification)      ──► [COMPLETED]
```

### Interactive Web Dashboard

When `/project-workflow` runs, it starts a zero-dependency local server and opens your browser (`http://localhost:4321`):
- **Web-First Prompt Entry**: Enter what you want to build, refactor, or fix directly into the browser prompt card.
- **Pipeline & Skills Config**: View attached skills per stage, toggle optional stages on/off (Stage 2 Docs and Stage 3 Plan), and switch architecture stacks (`React / Next.js`, `Go Hexagonal`, or `Generic Clean`).
- **Stage Artifact Viewer**: Inspect grilling questions, updated `docs/`, colored `### Proposed File Tree` badges (`[NEW]`, `[UPDATE]`, `[REUSE]`, `[PROMOTE]`, `[DELETE]`), and verification output.
- **Interactive Action Bar**: Type answers or instructions directly on the website and click **`Approve & Next Step`** (or `Cmd/Ctrl + Enter`) or **`Request Revisions`**.

## Documentation Structure (`project-documentation`)

Singletons sit flat without running numbers; ordered multi-item collections use `<NNN>-<name>.md`:

```text
docs/
├── README.md                              # Documentation index
├── ubiquitous-language.md                 # Single canonical glossary (Term | Meaning | Avoid)
├── product.md                             # Core product overview, personas & global business rules
├── architecture.md                        # System architecture, code structure, data model & APIs
├── development.md                         # Setup, build, test, and verification commands
├── flows/                                 # Running number per user/system flow
│   ├── 001-create-order.md
│   └── 002-cancel-order.md
└── decisions/                             # Running number per ADR (one file per decision)
    ├── 001-store-orders-in-memory.md
    └── 002-hexagonal-module-boundary.md
```

## Skills

| Skill | Role | What it does |
| :--- | :--- | :--- |
| [`project-workflow`](skills/project-workflow/) | **Orchestrator** | Master `/project-workflow` entrypoint. Launches local browser dashboard directly, handles web-first prompting, stage toggles, and stack switching. |
| [`project-grill`](skills/project-grill/) | **Stage 1 — Grill (🔒)** | Silently inspects code & `docs/`, flags terminology or requirement conflicts, asks numbered design-tree questions with `(Recommended)` proposals, and outputs an Agreed Design Summary. |
| [`project-documentation`](skills/project-documentation/) | **Stage 2 — Docs** | Documentation guardian: flat canonical singletons (`docs/ubiquitous-language.md` bound to code identifiers, `product.md`, `architecture.md`, `development.md`), numbered `docs/flows/<NNN>-<name>.md`, one-file-per-decision `docs/decisions/<NNN>-<name>.md`, and deterministic validators. |
| [`project-plan`](skills/project-plan/) | **Stage 3 — Plan** | Scans existing project layers to prevent duplication, schedules glossary-driven code renames, and outputs **only** the annotated `### Proposed File Tree` (`[NEW]`, `[UPDATE]`, `[REUSE]`, `[PROMOTE]`, `[DELETE]`). |
| [`project-implement`](skills/project-implement/) | **Stage 4 — Implement (🔒)** | Executes the approved `### Proposed File Tree` following the active stack architecture skill and canonical glossary names, then runs code and documentation verification. |
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
