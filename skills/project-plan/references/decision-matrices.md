# Layer & Scope Decision Matrices

Reference companion for `project-plan` (Stage 3). Pick the matrix matching the repository's tech stack.

## Contents
1. [React / Next.js Decision Matrix (`project-react-architecture`)](#1-react--nextjs-decision-matrix-project-react-architecture)
2. [Go Hexagonal Decision Matrix (`project-go-architecture`)](#2-go-hexagonal-decision-matrix-project-go-architecture)
3. [Generic Clean-Architecture Decision Matrix](#3-generic-clean-architecture-decision-matrix)

---

## 1. React / Next.js Decision Matrix (`project-react-architecture`)

| Question | Decision | Target Path & Tag |
| :--- | :--- | :--- |
| Does an exact `.ui.tsx` or `.layout.tsx` already exist? | Reuse as-is (zero duplication) | `[REUSE]` `/components/[module]/[name].ui.tsx` or `/layouts/[category]/[name].layout.tsx` |
| Does a partial `.ui.tsx` or `.layout.tsx` match exist (missing variant/size)? | Extend existing primitive & its `.constant.ts` | `[UPDATE]` `/components/[module]/[name].ui.tsx` + `/constants/[name].constant.ts` |
| Is it a brand-new visual primitive (raw CSS/Tailwind, no domain logic)? | Create canonical placement-agnostic primitive at root | `[NEW]` `/components/[module]/[name].ui.tsx` |
| Is it pure structural geometry (flex/grid/spacing/border, no visuals or logic)? | Create categorized layout container at root | `[NEW]` `/layouts/[category]/[name].layout.tsx` |
| Is it a hook, type, constant, or helper used by **≥2 features** or app-wide? | Place at project root (or promote if previously in 1 feature) | `[NEW]` or `[PROMOTE]` `/hooks/`, `/types/`, `/constants/`, `/utils/` (and `[DELETE]` old feature-local path) |
| Is it a hook, type, constant, or helper used by **1 feature only**? | Keep inside the single feature module | `[NEW]` `features/[feature]/hooks\|types\|constants\|utils/` |
| Does it connect business state/hooks to `.ui.tsx` + `.layout.tsx` primitives? | Create a feature component folder (zero inline `className`) | `[NEW]` `features/[feature]/components/[name]/[name].{component.tsx,hook.ts,type.ts}` |
| Is it a sub-component used exclusively by **1 parent component**? | Nest under the parent component (Level 1) | `[NEW]` `features/[feature]/components/[parent]/components/[child]/` |
| Is it a Next.js route/page (`app/**/page.tsx`, `app/**/layout.tsx`)? | Keep as SSR Server Component (no `'use client'`), zero `className`, importing only `.ui.tsx`, `.layout.tsx`, and `[feature].feature.ts` | `[NEW]` or `[UPDATE]` `app/**/{page,layout}.tsx` |
| Is an existing file obsolete, duplicated, or replaced by promotion/slicing? | Remove the redundant or old file | `[DELETE]` path to obsolete/duplicate file |

---

## 2. Go Hexagonal Decision Matrix (`project-go-architecture`)

| Question | Decision | Target Path & Tag |
| :--- | :--- | :--- |
| Does a new module need an error prefix? | Register `<Module>ErrPrefixID` in shared domain errors | `[UPDATE]` `internal/shared/domain/shared_domain_error.go` |
| Domain errors, models, events, or ports for `<module>`? | Place pure Go domain files under `domain/` (zero infra imports) | `[NEW]` or `[UPDATE]` `internal/modules/<module>/domain/<module>_domain_{error,model,event,port}.go` |
| Business use case operation for `<module>`? | One file per operation under `application/` | `[NEW]` or `[UPDATE]` `internal/modules/<module>/application/<module>_usecase_<operation>.go` |
| Database table GORM model, migration, or seeder? | Place in `internal/infrastructure/postgresql/` | `[NEW]` `model/model_postgresql_<entity>.go`, `[UPDATE]` `migrate.go`, `[NEW]`/`[UPDATE]` `seed/` |
| Outbound PostgreSQL mapper or adapter? | Place under `adapter/out/postgresql/` | `[NEW]` or `[UPDATE]` `internal/modules/<module>/adapter/out/postgresql/<module>_postgresql_<operation>.go` |
| Cross-module outbound call to `<provider>`? | Consumer-owned port in `domain/` + adapter in `adapter/out/<provider>/` | `[NEW]` `internal/modules/<module>/adapter/out/<provider>/<module>_<provider>_<operation>.go` |
| Inbound HTTP DTO or Fiber handler? | Place under `adapter/in/fiber/` with Swagger annotations | `[NEW]` or `[UPDATE]` `internal/modules/<module>/adapter/in/fiber/<module>_fiber_<operation>.go` |
| Module route/dependency wiring & app bootstrap? | Wire in `<module>_module.go` and `bootstrap_module_init.go` | `[NEW]` or `[UPDATE]` `internal/modules/<module>/<module>_module.go` + `[UPDATE]` `internal/bootstrap/bootstrap_module_init.go` |

---

## 3. Generic Clean-Architecture Decision Matrix

| Question | Decision | Target Path & Tag |
| :--- | :--- | :--- |
| Does an existing shared helper, type, or component already cover this? | Reuse or extend in place | `[REUSE]` or `[UPDATE]` existing shared file |
| Is code used across **≥2 modules/features**? | Place or promote to root/shared layer | `[NEW]` or `[PROMOTE]` shared directory (and `[DELETE]` old module-local file) |
| Is code specific to **1 domain module/feature**? | Keep encapsulated inside that module | `[NEW]` or `[UPDATE]` module directory |
| Did a glossary term rename in `docs/ubiquitous-language.md`? | Rename file and/or update all identifiers inside affected files | `[UPDATE]` or `[NEW]`/`[DELETE]` affected code files |
| Was a feature, flow, or endpoint removed? | Delete dead files and prune references | `[DELETE]` obsolete files + `[UPDATE]` callers/routers |
