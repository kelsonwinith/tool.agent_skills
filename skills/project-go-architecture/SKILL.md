---
name: project-go-architecture
description: Design, scaffold, implement, and refactor Go backend code using this repository's strict Hexagonal Architecture (Ports and Adapters) template with Fiber v3, GORM, PostgreSQL, JWT auth, and Swaggo. Use this skill whenever creating a new module, adding or modifying a use case, HTTP handler, DTO, GORM model, mapper, PostgreSQL adapter, cross-module port/adapter, domain error, migration, seeder, or bootstrap wiring in a Go hexagonal project—or when bootstrapping a new Go project based on this template.
---

# Project Go Hexagonal Architecture

This skill encodes the architecture, structural conventions, code formatting rules, and implementation patterns of this Go Hexagonal Architecture template (`Fiber v3` + `GORM` + `PostgreSQL` + `JWT` + `Swaggo`). Follow these patterns so every module and layer remains predictable, testable, and decoupled.

---

## 1. Architectural Overview & Dependency Direction

Dependencies flow strictly **inward**:

```text
adapter/in (Fiber HTTP, DTOs) ──┐
                                ├──► application (Use Cases) ──► domain (Models, Errors, Ports)
adapter/out (GORM, JWT, etc.) ──┘
```

- **`domain/`**: Pure business logic—models, constructors, validation, ownership checks, domain events, domain errors, and input/output port interfaces. **Never** import Fiber, GORM, PostgreSQL, config, or `internal/infrastructure` packages here; only standard library packages and `sharedDomain` are allowed.
- **`application/`**: Orchestrates one business use case per file (`<module>_usecase_<operation>.go`). Depends only on `domain` ports and `sharedDomain`. Constructors return the `domain` use case port interface.
- **`adapter/in/fiber/`**: HTTP delivery layer. Binds/validates requests (`sharedFiber.Bind`), maps DTOs to domain types (`request.ToDomain(...)`), calls use case ports, and formats responses (`sharedFiber.Response*`).
- **`adapter/out/`**: Driven adapters implementing output ports defined in `domain` (`postgresql`, `password`, `eventLog`, or cross-module `<provider>` adapters).
- **`<module>_module.go` & `internal/bootstrap/`**: Composition root that instantiates concrete adapters, injects them into use cases, mounts Fiber routes, and connects cross-module dependencies.

---

## 2. Choosing the Right Reference Archetype

Pick the existing module whose shape matches the feature you are building:

| Archetype | Reference Module | When to Use | Key Patterns |
| --- | --- | --- | --- |
| **Identity / Auth** | `internal/modules/exampleUser` | User registration, login, password hashing, token issuance, profile lookup | `NewExampleUser` validation, `ExampleUserPasswordHasher` / `Comparer` (bcrypt), `sharedDomain.TokenService` (JWT), `GetByEmail` |
| **Single-Entity CRUD** | `internal/modules/exampleProduct` | Standard resource with create, get-by-ID, paginated search, update, and soft delete | `NewExampleProduct`, ownership check (`IsOwnedBy` -> `ErrForbidden`), `UpdateExampleProduct`, `sharedDomain.NewPagination`, soft delete (`deleted_by` + `Delete`) |
| **Aggregate + Cross-Module + Tx + Events** | `internal/modules/exampleOrder` | Multi-table aggregates, atomic writes, calling other modules, or publishing domain events | `WithinTransaction`, `Preload("Products")`, `<Provider>Module<Operation>` cross-module ports/adapters, `eventLog` output adapter |

For complete copy-pasteable code templates across all layers, read:
- [`references/domain-and-application.md`](references/domain-and-application.md) — Domain errors, models, events, ports, use cases, and `shared/domain` utilities.
- [`references/adapters-and-wiring.md`](references/adapters-and-wiring.md) — Fiber DTOs, handlers, Swagger annotations, PostgreSQL adapters/mappers, cross-module adapters, module `Init`, `bootstrap`, and `infrastructure`.

---

## 3. Project Directory Layout & 3-Segment File Naming

Every Go file (except `cmd/main.go`, `<module>_module.go`, and top-level infra files `config.go`, `config_schema.go`, `db.go`, `migrate.go`, `seed.go`) follows a strict **three-segment underscore-separated camelCase** naming convention: `<scope>_<layer>_<name>.go`.

```text
internal/
├── bootstrap/
│   ├── bootstrap_config_init.go          # InitConfig()
│   ├── bootstrap_database_init.go        # InitDatabase(cfg), CloseDatabase(db)
│   ├── bootstrap_app_init.go             # InitApp() -> Fiber + StructValidator
│   ├── bootstrap_middleware_init.go      # InitMiddleware(app) -> logger, CORS, Swagger
│   ├── bootstrap_auth_init.go            # InitAuth(cfg) -> TokenService, authMiddleware
│   ├── bootstrap_module_init.go          # InitModules(...) -> module & cross-module wiring
│   └── bootstrap_server_run.go           # RunServer(app, cfg) -> graceful shutdown
├── infrastructure/
│   ├── config/
│   │   ├── config.go                     # LoadConfig() via godotenv + envconfig
│   │   └── config_schema.go              # Config structs with envconfig/default/required tags
│   └── postgresql/
│       ├── db.go                         # NewDBConnection(cfg) with SingularTable: true
│       ├── migrate.go                    # allModels() + RunMigrations(db)
│       ├── seed.go                       # allSeeds() + RunSeeders(db)
│       ├── model/
│       │   ├── default/
│       │   │   ├── model_postgresql_base.go
│       │   │   └── model_postgresql_delete.go
│       │   └── model_postgresql_<entity>.go
│       └── seed/
│           └── seed_postgresql_<module>.go
├── modules/
│   └── <module>/                         # camelCase folder, e.g. exampleProduct
│       ├── domain/
│       │   ├── <module>_domain_error.go
│       │   ├── <module>_domain_model.go
│       │   ├── <module>_domain_event.go  # optional: when publishing domain events
│       │   └── <module>_domain_port.go
│       ├── application/
│       │   └── <module>_usecase_<operation>.go
│       ├── adapter/
│       │   ├── in/
│       │   │   └── fiber/
│       │   │       ├── dto/
│       │   │       │   └── <module>_fiber_dto.go
│       │   │       └── <module>_fiber_<operation>.go
│       │   └── out/
│       │       ├── postgresql/
│       │       │   ├── mapper/
│       │       │   │   └── <module>_postgresql_mapper.go
│       │       │   └── <module>_postgresql_<operation>.go
│       │       └── <providerOrAdapter>/
│       │           └── <module>_<providerOrAdapter>_<operation>.go
│       └── <module>_module.go
└── shared/
    ├── domain/
    │   ├── shared_domain_error.go
    │   ├── shared_domain_pagination.go
    │   └── shared_domain_token.go
    └── adapter/
        ├── in/
        │   └── fiber/
        │       ├── shared_fiber_auth.go
        │       ├── shared_fiber_request.go
        │       └── shared_fiber_response.go
        └── out/
            ├── jwt/
            │   └── shared_jwt_service.go
            └── postgresql/
                ├── shared_postgresql.go
                └── shared_postgresql_transaction.go
```

---

## 4. Universal Code Formatting & Naming Conventions

Every file in the repository adheres to four non-negotiable conventions so any file can be scanned at a glance.

### 4.1 Six-Section File Banners

Divide every Go file into labeled banner sections using this exact 3-line header:

```go
// ============================================================================
// <Title>
// ============================================================================
```

Order sections strictly as follows, **omitting any empty section**:
1. `Constants` — `const` declarations.
2. `Variables` — package-level `var` declarations (such as domain errors).
3. `Types` — structs, interfaces, and type definitions.
   - *Subgroup exception*: In `<module>_domain_port.go`, replace `Types` with specific subgroup banners in this order: `Usecase Ports`, `PostgreSQL Ports`, and any other port groups (`Security Ports`, `Event Ports`, `Cross-module Ports`).
4. `Constructors` — `New<Type>` functions.
5. `Methods` — functions with a receiver.
6. `Functions` — package-level functions (`Init`, `To<Module>Response`, `validate*`, mappers).

**Banner placement rules:**
- Leave one blank line between a banner and the code below it, and one blank line above a banner when it follows imports or another section.
- Even a file with only one category gets its banner (e.g., `Init` in `<module>_module.go` sits under `Functions`).
- On HTTP handlers, place the `Methods` banner, a blank line, and then the `// Handle ...` Swagger annotation comment directly attached to `func (h *...) Handle(c fiber.Ctx) error`.
- Never place banner headers inside a function body. Use simple one-line comments (`// Adapters Out - PostgreSQL`, `// Use Cases`, `// Adapters In - Fiber`) inside `Init`.

### 4.2 Explicit Import Aliasing & 3-Block Grouping

Every single import **must** have an explicit alias, even when the alias is identical to the package name. Group imports into up to three blocks separated by a single blank line:
1. **Standard library** (lowercase alias: `context "context"`, `errors "errors"`, `time "time"`, `utf8 "unicode/utf8"`)
2. **Third-party packages** (lowercase or disambiguated camelCase alias: `fiber "github.com/gofiber/fiber/v3"`, `gorm "gorm.io/gorm"`, `validator "github.com/go-playground/validator/v10"`)
3. **Internal packages** (`github.com/...`, camelCase alias prefixed with module or `shared`):
   - Module packages: `<module>Domain`, `<module>Usecase`, `<module>Fiber`, `<module>Dto`, `<module>Postgresql`, `<module>Mapper`, `<module>EventLog`
   - Cross-module adapter packages in `bootstrap`: `<consumer><Provider>` (e.g. `exampleOrderExampleUser`)
   - Shared packages: `sharedDomain`, `sharedFiber`, `sharedPostgresql`, `sharedJwt`
   - Infrastructure packages: `config`, `postgresql`, `postgresqlModel`, `defaultModel`, `postgresqlSeed`

*(Exception: blank import `_ "<repo>/docs"` in `cmd/main.go` and `bootstrap_middleware_init.go`.)*

```go
import (
	context "context"
	errors "errors"

	gorm "gorm.io/gorm"

	exampleProductMapper "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleProduct/adapter/out/postgresql/mapper"
	exampleProductDomain "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleProduct/domain"
	postgresqlModel "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/infrastructure/postgresql/model"
	sharedPostgresql "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/shared/adapter/out/postgresql"
)
```

### 4.3 Identifier, Variable, and Receiver Naming

- **Module Prefixing**: Prefix every exported type/constant/function in a module with `<Module>` (`ExampleProductUsecaseCreate`, `ExampleProductErrNotFound`) and every unexported identifier with `<module>` (`validateExampleProduct`).
- **Cross-Module Exception**: Cross-module ports and their adapters are named `<Provider>Module<Operation>` (`ExampleUserModuleGetByID`, `NewExampleUserModuleGetByID`) so the provider operation is immediately clear.
- **Injected Collaborators (Fields & Constructor Params)**: Name `<module><Operation><Adapter>` (`exampleProductCreatePostgres`, `exampleOrderEventPublisher`, `exampleUserPasswordHasher`, `exampleUserModuleGetByID`).
- **Domain Variables**: Name `<module>` (singular), `<module>s` (slice), `<module>Input` (input value), or `<module><Sub>` (`exampleOrderProduct`).
- **Unprefixed Idioms & Primitives**: Keep standard Go idioms and primitive/audit parameters unprefixed: `ctx`, `err`, `ok`, `i`, `id`, `email`, `password`, `createdBy`, `updatedBy`, `deletedBy`, `userID`, `page`, `pageSize`, `search`, `total`, `pagination`, `limit`, `offset`, `now`, `req`, `res`, `entity`, `entities`, `result`, `token`.
- **Receivers**:
  - `uc` for application use cases
  - `h` for Fiber handlers (and password hasher)
  - `request` for DTO methods (`ToDomain`)
  - `e` for domain models and PostgreSQL adapters
  - `p` for `sharedPostgresql.Postgresql` and event publishers
  - `r` for cross-module adapters

---

## 5. Step-by-Step Workflow: Building a New Module or Feature

When adding a new module (e.g., `exampleItem`) or extending an existing module, follow this exact sequence:

### Step 1: Error Prefix & Domain Layer (`internal/modules/<module>/domain/`)
1. **Register Error Prefix**: Add `<Module>ErrPrefixID ErrorPrefix = "<3-LETTER-CODE>"` to `internal/shared/domain/shared_domain_error.go`.
2. **Domain Errors (`<module>_domain_error.go`)**: Define reusable `*sharedDomain.Error` variables using `sharedDomain.NewError` and `sharedDomain.BuildErrorID`.
3. **Domain Model (`<module>_domain_model.go`)**:
   - Define pure Go structs with no JSON or GORM tags.
   - Write `New<Module>(...) (*<Module>, error)` that trims strings, validates rules using `utf8.RuneCountInString`, sets `now := time.Now().UTC()`, and initializes `CreatedBy`/`UpdatedBy` and `CreatedAt`/`UpdatedAt`.
   - Add domain mutation methods (`Update<Module>`) and ownership helpers (`IsOwnedBy(userID string) bool`).
4. **Domain Ports (`<module>_domain_port.go`)**:
   - Group interfaces under `Usecase Ports`, `PostgreSQL Ports`, and any `Event Ports` or `Cross-module Ports`.
   - Use `Execute(ctx context.Context, ...)` on every use case and adapter interface (except `WithinTransaction` on transaction ports and pure CPU helpers like password hashing).
   - For cross-module calls, define lightweight consumer-owned structs (e.g., `ExampleOrderUser`) in the consumer's `domain` so the consumer's domain never imports the provider's domain.

### Step 2: Application Use Cases (`internal/modules/<module>/application/`)
1. Create one file per operation: `<module>_usecase_<operation>.go`.
2. Return the domain interface from `New<Module>Usecase<Operation>`.
3. Keep business orchestration here:
   - **Pagination**: Call `pagination := sharedDomain.NewPagination(page, pageSize)` and return `&sharedDomain.Page[*<module>Domain.<Module>]{Items: ..., Pagination: pagination, Total: total}`.
   - **Ownership**: Fetch entity via `GetByID`, verify `if !entity.IsOwnedBy(userID) { return ..., <Module>ErrForbidden }` before updating or deleting.
   - **Multi-table atomic writes**: Wrap repository calls inside `uc.<module>PostgresqlTransaction.WithinTransaction(ctx, func(ctx context.Context) error { ... })`.

### Step 3: Persistence Model, Migration & Seed (`internal/infrastructure/postgresql/`)
1. **Model (`model/model_postgresql_<entity>.go`)**:
   - One file per database table.
   - Embed `defaultModel.BaseModel` and `defaultModel.DeleteModel`.
   - Implement `TableName() string` and `<Entity>Table() string` returning the singular `snake_case` constant `<entity>TableName`.
2. **Migration (`migrate.go`)**: Append `&postgresqlModel.<Entity>Model{}` to `allModels()`.
3. **Seeder (`seed/seed_postgresql_<module>.go` & `seed.go`)**: Optional—add deterministic seed data and register in `allSeeds()`.

### Step 4: Output Adapters (`internal/modules/<module>/adapter/out/`)
1. **Mapper (`postgresql/mapper/<module>_postgresql_mapper.go`)**: Write `To<Module>Model`, `To<Module>Models`, `To<Module>Domain`, and `To<Module>Domains`.
2. **PostgreSQL Adapters (`postgresql/<module>_postgresql_<operation>.go`)**:
   - Embed `*sharedPostgresql.Postgresql` and always query with `e.GetExecutor(ctx)` so transactions propagate via `context.Context`.
   - Map `errors.Is(err, gorm.ErrRecordNotFound)` to `<module>Domain.<Module>ErrNotFound`.
   - On `Update` and `Delete`, check `result.RowsAffected == 0` and return `<Module>ErrNotFound`.
   - On soft `Delete`, first `.Update("deleted_by", deletedBy)` then `.Delete(&postgresqlModel.<Module>Model{})`.
3. **Cross-Module Adapters (`<provider>/<consumer>_<provider>_<operation>.go`)**:
   - Implement `<Provider>Module<Operation>` by calling the provider's exported use case port and mapping the result to the consumer's domain struct.

### Step 5: Input Adapters — Fiber DTOs & Handlers (`internal/modules/<module>/adapter/in/fiber/`)
1. **DTOs (`dto/<module>_fiber_dto.go`)**:
   - Define request structs with `json`/`query`/`uri` tags and `validate` tags (`required`, `uuid4`, `min=1`, `max=255`, `dive`).
   - Add `(request <Module>CreateRequest) ToDomain(createdBy string)` methods and `To<Module>Response` / `To<Module>Responses` functions.
2. **Handlers (`<module>_fiber_<operation>.go`)**:
   - Bind input with `sharedFiber.Bind[URI, Query, Body](c)` using `sharedFiber.Empty` for unused parts.
   - Read authenticated user ID via `sharedFiber.GetAuthUserID(c)` on protected routes—never read headers manually.
   - Return `sharedFiber.ResponseCreated`, `ResponseSuccess`, `ResponsePaginated`, `ResponseNoContent`, or `ResponseError`.
   - Place complete Swagger annotations directly above `Handle`:
     - `@Tags` must be Title Case with spaces (`Example Product`), identical across all handlers in the module.
     - `@Router` uses lowercase path (`/api/v1/exampleproduct`).
     - Include `@Security BearerAuth` only on routes guarded by `authMiddleware` (do not add a manual `Authorization` header `@Param`).

### Step 6: Wiring & Verification (`<module>_module.go`, `bootstrap/`, `Makefile`)
1. **Module Wiring (`<module>_module.go`)**: Wire Outbound Adapters -> Use Cases -> Inbound Fiber Handlers -> Route Group. Register static routes (`/paginated`) **before** parameterized routes (`/:id`). Return any use case ports needed by other modules.
2. **Bootstrap (`internal/bootstrap/bootstrap_module_init.go`)**: Call `<module>.Init(...)` and wire any cross-module adapters.
3. **Config (if modified)**: Any change in `internal/infrastructure/config/config_schema.go` must have a matching empty key in `.env.example`.
4. **Makefile Commands**: Only run project commands via `Makefile` targets:
   - `make fmt` — format Go code
   - `make swagger` — regenerate Swagger docs after handler/DTO changes
   - `make test` — run unit/handler tests (`httptest` with `app.Test` for HTTP, fake port structs for use cases)
   - `make build` — verify compilation
