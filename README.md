# Agent Skills

A collection of portable, project-agnostic agent skills.

## Manage Skills

### Install

Install skills from this repository using the `skills` CLI:

```bash
# Interactive selection
npx skills add kelsonwinith/tool.agent_skills

# Or specify a skill name
npx skills add kelsonwinith/tool.agent_skills --skill <skill-name>
```

### List

View all installed skills:

```bash
npx skills list
```

### Update

Update all installed skills to their latest version:

```bash
npx skills update
```

Update specific skills:

```bash
npx skills update <skill-name>
```

Update with scope flags:

```bash
npx skills update -p -y     # project-level skills, skip prompt
npx skills update -g -y     # global skills, skip prompt
```

### Remove

Remove an installed skill:

```bash
npx skills remove <skill-name>
```

## License

MIT
