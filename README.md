# Agent Skills

A small collection of portable, project-agnostic agent skills.

## Skills

| Skill | What it does |
| :--- | :--- |
| [`project-documentation`](skills/project-documentation/) | Documentation guardian: canonical context (ubiquitous language), a numbered `docs/` tree, pre-implementation grilling, requirement-mismatch detection, and bundled validators. |
| [`project-react-architecture`](skills/project-react-architecture/) | Layered React/Next.js component and file architecture with zero inline styling. |

## Install

Install a skill straight from this repo with the `skills` CLI:

```bash
npx skills add kelsonwinith/tool.agent_skills --skill project-react-architecture
npx skills add kelsonwinith/tool.agent_skills --skill project-documentation
```

## Update

Update every installed skill to its latest version:

```bash
npx skills update
```

Update specific skills by name:

```bash
npx skills update project-react-architecture
npx skills update project-react-architecture project-documentation
```

Scope flags: `-p` project-level only, `-g` global only, `-y` skip the scope prompt.

```bash
npx skills update -p -y     # project-level skills, no prompt
npx skills update -g -y     # global skills, no prompt
```

See what's installed, or remove a skill:

```bash
npx skills list
npx skills remove project-react-architecture
```

## Structure

```text
skills/<name>/
├── SKILL.md          # entry point: frontmatter (name + description) and instructions
├── references/       # formats, examples, and templates loaded on demand
├── scripts/          # scaffolders + validators (Python 3 standard library only)
└── CHANGELOG.md
evals/<name>/         # trigger-eval query sets
tools/                # repo tooling (trigger evaluation)
```

## Development

Run the script test suites:

```bash
python3 skills/project-documentation/scripts/tests/test_scripts.py
python3 skills/project-react-architecture/scripts/tests/test_new_feature.py
```

Check that a skill's description actually makes opencode load it (trigger eval):

```bash
python3 tools/trigger_eval_opencode.py \
  --skill-path skills/project-react-architecture \
  --eval-set evals/project-react-architecture/trigger_eval.json
```

## License

MIT
