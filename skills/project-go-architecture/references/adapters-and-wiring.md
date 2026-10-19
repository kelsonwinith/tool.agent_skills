# Adapters, Infrastructure, and Bootstrap Wiring Templates

## Table of Contents

1. [Inbound Fiber Adapters (`internal/modules/<module>/adapter/in/fiber/`)](#1-inbound-fiber-adapters-internalmodulesmoduleadapterinfiber)
   - [DTOs & Domain Mapping (`dto/<module>_fiber_dto.go`)](#11-dtos--domain-mapping-dtomodule_fiber_dtogo)
   - [Fiber Handlers & Swagger Annotations (`<module>_fiber_<operation>.go`)](#12-fiber-handlers--swagger-annotations-module_fiber_operationgo)
2. [Outbound PostgreSQL Adapters (`internal/modules/<module>/adapter/out/postgresql/`)](#2-outbound-postgresql-adapters-internalmodulesmoduleadapteroutpostgresql)
   - [Domain <-> GORM Model Mapper (`mapper/<module>_postgresql_mapper.go`)](#21-domain---gorm-model-mapper-mappermodule_postgresql_mappergo)
   - [Create Adapter (`<module>_postgresql_create.go`)](#22-create-adapter-module_postgresql_creatego)
   - [GetByID Adapter (`<module>_postgresql_getByID.go`)](#23-getbyid-adapter-module_postgresql_getbyidgo)
   - [GetPaginated Adapter (`<module>_postgresql_getPaginated.go`)](#24-getpaginated-adapter-module_postgresql_getpaginatedgo)
   - [Update Adapter (`<module>_postgresql_update.go`)](#25-update-adapter-module_postgresql_updatego)
   - [Soft Delete Adapter (`<module>_postgresql_delete.go`)](#26-soft-delete-adapter-module_postgresql_deletego)
3. [Cross-Module & Non-Database Outbound Adapters](#3-cross-module--non-database-outbound-adapters)
   - [Cross-Module Adapter (`adapter/out/<provider>/<consumer>_<provider>_<operation>.go`)](#31-cross-module-adapter-adapteroutproviderconsumer_provider_operationgo)
   - [Event Publisher Adapter (`adapter/out/eventLog/<module>_eventLog_publisher.go`)](#32-event-publisher-adapter-adapterouteventlogmodule_eventlog_publishergo)
4. [Infrastructure: Persistence Models, Migrations, Seeds & Config](#4-infrastructure-persistence-models-migrations-seeds--config)
   - [GORM Persistence Model (`model/model_postgresql_<entity>.go`)](#41-gorm-persistence-model-modelmodel_postgresql_entitygo)
   - [Migrations & Seeders (`migrate.go`, `seed.go`, `seed_postgresql_<module>.go`)](#42-migrations--seeders-migratego-seedgo-seed_postgresql_modulego)
   - [Config Schema (`config_schema.go` & `.env.example`)](#43-config-schema-config_schemago--envexample)
5. [Module Initializer & Bootstrap Wiring](#5-module-initializer--bootstrap-wiring)
   - [Module `Init` (`<module>_module.go`)](#51-module-init-module_modulego)
   - [Bootstrap Wiring (`internal/bootstrap/bootstrap_module_init.go`)](#52-bootstrap-wiring-internalbootstrapbootstrap_module_initgo)

---

## 1. Inbound Fiber Adapters (`internal/modules/<module>/adapter/in/fiber/`)

### 1.1 DTOs & Domain Mapping (`dto/<module>_fiber_dto.go`)

- Receiver on request DTO `ToDomain` methods is always named `request`.
- Response mapping uses `To<Module>Response` and `To<Module>Responses` under the `Functions` banner.
- Validation tags (`validate:"..."`) work across `json`, `query`, `params`, and `uri` tags.

```go
package dto

import (
	time "time"

	exampleProductDomain "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleProduct/domain"
)

// ============================================================================
// Types
// ============================================================================

type ExampleProductResponse struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Description string    `json:"description"`
	Price       int64     `json:"price"`
	CreatedBy   string    `json:"created_by"`
	UpdatedBy   string    `json:"updated_by"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

type ExampleProductRequestParams struct {
	ID string `uri:"id" validate:"required,uuid4"`
}

type ExampleProductGetPaginatedQuery struct {
	Page     int    `query:"page" validate:"omitempty,min=1"`
	PageSize int    `query:"page_size" validate:"omitempty,min=1"`
	Search   string `query:"search" validate:"omitempty,max=255"`
}

type ExampleProductCreateRequest struct {
	Name        string `json:"name" validate:"required,max=255"`
	Description string `json:"description" validate:"max=255"`
	Price       int64  `json:"price" validate:"min=0"`
}

type ExampleProductUpdateRequest struct {
	Name        string `json:"name" validate:"required,max=255"`
	Description string `json:"description" validate:"max=255"`
	Price       int64  `json:"price" validate:"min=0"`
}

// ============================================================================
// Methods
// ============================================================================

func (request ExampleProductCreateRequest) ToDomain(createdBy string) exampleProductDomain.ExampleProduct {
	return exampleProductDomain.ExampleProduct{
		Name:        request.Name,
		Description: request.Description,
		Price:       request.Price,
		CreatedBy:   createdBy,
		UpdatedBy:   createdBy,
	}
}

func (request ExampleProductUpdateRequest) ToDomain(updatedBy string) exampleProductDomain.ExampleProduct {
	return exampleProductDomain.ExampleProduct{
		Name:        request.Name,
		Description: request.Description,
		Price:       request.Price,
		UpdatedBy:   updatedBy,
	}
}

// ============================================================================
// Functions
// ============================================================================

func ToExampleProductResponse(exampleProduct *exampleProductDomain.ExampleProduct) ExampleProductResponse {
	return ExampleProductResponse{
		ID:          exampleProduct.ID,
		Name:        exampleProduct.Name,
		Description: exampleProduct.Description,
		Price:       exampleProduct.Price,
		CreatedBy:   exampleProduct.CreatedBy,
		UpdatedBy:   exampleProduct.UpdatedBy,
		CreatedAt:   exampleProduct.CreatedAt,
		UpdatedAt:   exampleProduct.UpdatedAt,
	}
}

func ToExampleProductResponses(exampleProducts []*exampleProductDomain.ExampleProduct) []ExampleProductResponse {
	responses := make([]ExampleProductResponse, len(exampleProducts))
	for i, exampleProduct := range exampleProducts {
		responses[i] = ToExampleProductResponse(exampleProduct)
	}
	return responses
}
```

### 1.2 Fiber Handlers & Swagger Annotations (`<module>_fiber_<operation>.go`)

**Handler & Swagger rules:**
- Use `sharedFiber.Bind[URI, Query, Body](c)` and pass `sharedFiber.Empty` for unused generic slots.
- Use `sharedFiber.GetAuthUserID(c)` on routes protected by `authMiddleware`.
- Use `sharedFiber.ResponseCreated` (`201`), `ResponseSuccess` (`200`), `ResponsePaginated` (`200`), `ResponseNoContent` (`204`), and `ResponseError`.
- Keep `@Tags` in Title Case with spaces (`Example Product`), identical across all handlers in a module.
- Keep `@Router` lowercase (`/api/v1/exampleproduct`).
- Add `@Security BearerAuth` only on protected routes; never add an `Authorization` header `@Param`.

#### Create Handler (`POST /api/v1/exampleproduct`)
```go
package fiber

import (
	fiber "github.com/gofiber/fiber/v3"

	exampleProductDto "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleProduct/adapter/in/fiber/dto"
	exampleProductDomain "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleProduct/domain"
	sharedFiber "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/shared/adapter/in/fiber"
)

// ============================================================================
// Types
// ============================================================================

type ExampleProductFiberCreate struct {
	usecase exampleProductDomain.ExampleProductUsecaseCreate
}

// ============================================================================
// Constructors
// ============================================================================

func NewExampleProductFiberCreate(usecase exampleProductDomain.ExampleProductUsecaseCreate) *ExampleProductFiberCreate {
	return &ExampleProductFiberCreate{usecase: usecase}
}

// ============================================================================
// Methods
// ============================================================================

// Handle CreateExampleProduct
// @Summary Create a new example product
// @Description Create a new example product with the input payload
// @Tags Example Product
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param example body exampleProductDto.ExampleProductCreateRequest true "Create ExampleProduct"
// @Success 201 {object} exampleProductDto.ExampleProductResponse
// @Failure 400 {object} map[string]string
// @Failure 401 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /api/v1/exampleproduct [post]
func (h *ExampleProductFiberCreate) Handle(c fiber.Ctx) error {
	req, err := sharedFiber.Bind[sharedFiber.Empty, sharedFiber.Empty, exampleProductDto.ExampleProductCreateRequest](c)
	if err != nil {
		return sharedFiber.ResponseError(c, err)
	}

	userID := sharedFiber.GetAuthUserID(c)

	res, err := h.usecase.Execute(c.Context(), req.Body.ToDomain(userID))
	if err != nil {
		return sharedFiber.ResponseError(c, err)
	}

	return sharedFiber.ResponseCreated(c, exampleProductDto.ToExampleProductResponse(res))
}
```

#### Paginated Handler (`GET /api/v1/exampleproduct/paginated`)
```go
// ============================================================================
// Methods
// ============================================================================

// Handle GetPaginatedExampleProducts
// @Summary Get example products with pagination
// @Description Get a page of example products ordered by creation date
// @Tags Example Product
// @Produce json
// @Param page query int false "Page number (default 1)"
// @Param page_size query int false "Items per page (default 10, max 100)"
// @Param search query string false "Search by name or description"
// @Success 200 {object} sharedFiber.ResponsePaginatedData[exampleProductDto.ExampleProductResponse]
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /api/v1/exampleproduct/paginated [get]
func (h *ExampleProductFiberGetPaginated) Handle(c fiber.Ctx) error {
	req, err := sharedFiber.Bind[sharedFiber.Empty, exampleProductDto.ExampleProductGetPaginatedQuery, sharedFiber.Empty](c)
	if err != nil {
		return sharedFiber.ResponseError(c, err)
	}

	res, err := h.usecase.Execute(c.Context(), req.Query.Page, req.Query.PageSize, req.Query.Search)
	if err != nil {
		return sharedFiber.ResponseError(c, err)
	}

	return sharedFiber.ResponsePaginated(c, exampleProductDto.ToExampleProductResponses(res.Items), res.Pagination, res.Total)
}
```

#### Update & Delete Handlers (`PUT / DELETE /api/v1/exampleproduct/:id`)
- **Update**: binds `sharedFiber.Bind[exampleProductDto.ExampleProductRequestParams, sharedFiber.Empty, exampleProductDto.ExampleProductUpdateRequest](c)`, gets `userID := sharedFiber.GetAuthUserID(c)`, calls `h.usecase.Execute(c.Context(), req.URI.ID, req.Body.ToDomain(userID))`, returns `sharedFiber.ResponseSuccess(c, exampleProductDto.ToExampleProductResponse(res))`.
- **Delete**: binds `sharedFiber.Bind[exampleProductDto.ExampleProductRequestParams, sharedFiber.Empty, sharedFiber.Empty](c)`, gets `userID := sharedFiber.GetAuthUserID(c)`, calls `h.usecase.Execute(c.Context(), req.URI.ID, userID)`, returns `sharedFiber.ResponseNoContent(c)`.

---

## 2. Outbound PostgreSQL Adapters (`internal/modules/<module>/adapter/out/postgresql/`)

### 2.1 Domain <-> GORM Model Mapper (`mapper/<module>_postgresql_mapper.go`)

```go
package mapper

import (
	postgresqlModel "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/infrastructure/postgresql/model"
	defaultModel "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/infrastructure/postgresql/model/default"
	exampleProductDomain "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleProduct/domain"
)

// ============================================================================
// Functions
// ============================================================================

func ToExampleProductModel(exampleProduct *exampleProductDomain.ExampleProduct) *postgresqlModel.ExampleProductModel {
	if exampleProduct == nil {
		return nil
	}

	return &postgresqlModel.ExampleProductModel{
		BaseModel: defaultModel.BaseModel{
			ID:        exampleProduct.ID,
			CreatedBy: exampleProduct.CreatedBy,
			CreatedAt: exampleProduct.CreatedAt,
			UpdatedBy: exampleProduct.UpdatedBy,
			UpdatedAt: exampleProduct.UpdatedAt,
		},
		Name:        exampleProduct.Name,
		Description: exampleProduct.Description,
		Price:       exampleProduct.Price,
	}
}

func ToExampleProductDomain(entity *postgresqlModel.ExampleProductModel) *exampleProductDomain.ExampleProduct {
	if entity == nil {
		return nil
	}

	return &exampleProductDomain.ExampleProduct{
		ID:          entity.ID,
		Name:        entity.Name,
		Description: entity.Description,
		Price:       entity.Price,
		CreatedBy:   entity.CreatedBy,
		UpdatedBy:   entity.UpdatedBy,
		CreatedAt:   entity.CreatedAt,
		UpdatedAt:   entity.UpdatedAt,
	}
}

func ToExampleProductDomains(entities []*postgresqlModel.ExampleProductModel) []*exampleProductDomain.ExampleProduct {
	exampleProducts := make([]*exampleProductDomain.ExampleProduct, len(entities))
	for i, entity := range entities {
		exampleProducts[i] = ToExampleProductDomain(entity)
	}
	return exampleProducts
}
```

### 2.2 Create Adapter (`<module>_postgresql_create.go`)

Always call `e.GetExecutor(ctx)` so `WithinTransaction` works automatically, and copy the DB-assigned fields back to the domain pointer:

```go
package postgresql

import (
	context "context"

	exampleProductMapper "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleProduct/adapter/out/postgresql/mapper"
	exampleProductDomain "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleProduct/domain"
	sharedPostgresql "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/shared/adapter/out/postgresql"
)

// ============================================================================
// Types
// ============================================================================

type ExampleProductPostgresqlCreate struct {
	*sharedPostgresql.Postgresql
}

// ============================================================================
// Constructors
// ============================================================================

func NewExampleProductPostgresqlCreate(p *sharedPostgresql.Postgresql) *ExampleProductPostgresqlCreate {
	return &ExampleProductPostgresqlCreate{Postgresql: p}
}

// ============================================================================
// Methods
// ============================================================================

func (e *ExampleProductPostgresqlCreate) Execute(ctx context.Context, exampleProduct *exampleProductDomain.ExampleProduct) error {
	entity := exampleProductMapper.ToExampleProductModel(exampleProduct)

	if err := e.GetExecutor(ctx).Create(entity).Error; err != nil {
		return err
	}

	*exampleProduct = *exampleProductMapper.ToExampleProductDomain(entity)
	return nil
}
```

### 2.3 GetByID Adapter (`<module>_postgresql_getByID.go`)

Map `errors.Is(err, gorm.ErrRecordNotFound)` to `<module>Domain.<Module>ErrNotFound` (and chain `.Preload("Products")` when loading an aggregate like `ExampleOrder`):

```go
func (e *ExampleProductPostgresqlGetByID) Execute(ctx context.Context, id string) (*exampleProductDomain.ExampleProduct, error) {
	var entity postgresqlModel.ExampleProductModel

	err := e.GetExecutor(ctx).
		Where("id = ?", id).
		First(&entity).Error
	if err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, exampleProductDomain.ExampleProductErrNotFound
		}
		return nil, err
	}

	return exampleProductMapper.ToExampleProductDomain(&entity), nil
}
```

### 2.4 GetPaginated Adapter (`<module>_postgresql_getPaginated.go`)

```go
// ============================================================================
// Methods
// ============================================================================

func (e *ExampleProductPostgresqlGetPaginated) Execute(ctx context.Context, limit, offset int, search string) ([]*exampleProductDomain.ExampleProduct, int64, error) {
	var entities []*postgresqlModel.ExampleProductModel
	var total int64

	db := exampleProductSearchScope(e.GetExecutor(ctx), search)

	if err := db.Model(&postgresqlModel.ExampleProductModel{}).Count(&total).Error; err != nil {
		return nil, 0, err
	}

	err := db.
		Order("created_at DESC").
		Limit(limit).
		Offset(offset).
		Find(&entities).Error
	if err != nil {
		return nil, 0, err
	}

	return exampleProductMapper.ToExampleProductDomains(entities), total, nil
}

// ============================================================================
// Functions
// ============================================================================

func exampleProductSearchScope(db *gorm.DB, search string) *gorm.DB {
	search = strings.TrimSpace(search)
	if search == "" {
		return db
	}

	pattern := "%" + search + "%"
	return db.Where("name ILIKE ? OR description ILIKE ?", pattern, pattern)
}
```

### 2.5 Update Adapter (`<module>_postgresql_update.go`)

```go
func (e *ExampleProductPostgresqlUpdate) Execute(ctx context.Context, exampleProduct *exampleProductDomain.ExampleProduct) error {
	entity := exampleProductMapper.ToExampleProductModel(exampleProduct)

	result := e.GetExecutor(ctx).
		Model(&postgresqlModel.ExampleProductModel{}).
		Where("id = ?", entity.ID).
		Updates(map[string]interface{}{
			"name":        entity.Name,
			"description": entity.Description,
			"price":       entity.Price,
			"updated_by":  entity.UpdatedBy,
			"updated_at":  entity.UpdatedAt,
		})
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return exampleProductDomain.ExampleProductErrNotFound
	}

	return nil
}
```

### 2.6 Soft Delete Adapter (`<module>_postgresql_delete.go`)

Always record `deleted_by` first, verify `RowsAffected > 0`, and then trigger GORM soft delete:

```go
func (e *ExampleProductPostgresqlDelete) Execute(ctx context.Context, id, deletedBy string) error {
	result := e.GetExecutor(ctx).
		Model(&postgresqlModel.ExampleProductModel{}).
		Where("id = ?", id).
		Update("deleted_by", deletedBy)
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return exampleProductDomain.ExampleProductErrNotFound
	}

	return e.GetExecutor(ctx).
		Where("id = ?", id).
		Delete(&postgresqlModel.ExampleProductModel{}).Error
}
```

---

## 3. Cross-Module & Non-Database Outbound Adapters

### 3.1 Cross-Module Adapter (`adapter/out/<provider>/<consumer>_<provider>_<operation>.go`)

Placed in the **consumer** module (`internal/modules/exampleOrder/adapter/out/exampleUser/exampleOrder_exampleUser_getByID.go`). Uses the `<Provider>Module<Operation>` naming exception and receiver `r`:

```go
package exampleUser

import (
	context "context"

	exampleOrderDomain "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleOrder/domain"
	exampleUserDomain "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleUser/domain"
)

// ============================================================================
// Types
// ============================================================================

type ExampleUserModuleGetByID struct {
	exampleUserGetByID exampleUserDomain.ExampleUserUsecaseGetByID
}

// ============================================================================
// Constructors
// ============================================================================

func NewExampleUserModuleGetByID(exampleUserGetByID exampleUserDomain.ExampleUserUsecaseGetByID) *ExampleUserModuleGetByID {
	return &ExampleUserModuleGetByID{
		exampleUserGetByID: exampleUserGetByID,
	}
}

// ============================================================================
// Methods
// ============================================================================

func (r *ExampleUserModuleGetByID) Execute(ctx context.Context, id string) (exampleOrderDomain.ExampleOrderUser, error) {
	exampleUser, err := r.exampleUserGetByID.Execute(ctx, id)
	if err != nil {
		return exampleOrderDomain.ExampleOrderUser{}, err
	}

	return exampleOrderDomain.ExampleOrderUser{
		ID:   exampleUser.ID,
		Name: exampleUser.Name,
	}, nil
}
```

### 3.2 Event Publisher Adapter (`adapter/out/eventLog/<module>_eventLog_publisher.go`)

```go
package eventLog

import (
	context "context"
	log "log"

	exampleOrderDomain "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleOrder/domain"
)

// ============================================================================
// Types
// ============================================================================

type ExampleOrderEventLogPublisher struct{}

// ============================================================================
// Constructors
// ============================================================================

func NewExampleOrderEventLogPublisher() *ExampleOrderEventLogPublisher {
	return &ExampleOrderEventLogPublisher{}
}

// ============================================================================
// Methods
// ============================================================================

func (p *ExampleOrderEventLogPublisher) Execute(ctx context.Context, exampleOrderEvent exampleOrderDomain.ExampleOrderEvent) error {
	log.Printf("[EventLog] Event Published: Type=%s, OrderID=%s, Timestamp=%s\n",
		exampleOrderEvent.EventType,
		exampleOrderEvent.OrderID,
		exampleOrderEvent.Timestamp.Format("2006-01-02T15:04:05Z07:00"),
	)
	return nil
}
```

---

## 4. Infrastructure: Persistence Models, Migrations, Seeds & Config

### 4.1 GORM Persistence Model (`model/model_postgresql_<entity>.go`)

One file per database table in `internal/infrastructure/postgresql/model/`. Embed `defaultModel.BaseModel` and `defaultModel.DeleteModel`:

```go
package model

import (
	defaultModel "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/infrastructure/postgresql/model/default"
)

// ============================================================================
// Constants
// ============================================================================

const exampleProductTableName = "example_product"

// ============================================================================
// Types
// ============================================================================

type ExampleProductModel struct {
	defaultModel.BaseModel
	defaultModel.DeleteModel

	Name        string `gorm:"column:name;type:varchar(255);not null"`
	Description string `gorm:"column:description;type:varchar(255)"`
	Price       int64  `gorm:"column:price;type:bigint;not null;default:0"`
}

// ============================================================================
// Methods
// ============================================================================

func (ExampleProductModel) TableName() string {
	return exampleProductTableName
}

// ============================================================================
// Functions
// ============================================================================

func ExampleProductTable() string {
	return exampleProductTableName
}
```

### 4.2 Migrations & Seeders (`migrate.go`, `seed.go`, `seed_postgresql_<module>.go`)

- Register every new GORM model in `allModels()` inside `internal/infrastructure/postgresql/migrate.go`.
- Register any new seeder function `postgresqlSeed.Seed<Module>` in `allSeeds()` inside `internal/infrastructure/postgresql/seed.go`.

### 4.3 Config Schema (`config_schema.go` & `.env.example`)

Whenever you add, rename, or remove a field in `internal/infrastructure/config/config_schema.go`, update `.env.example` in the same change with an empty value (`NEW_ENV_VAR=`).

---

## 5. Module Initializer & Bootstrap Wiring

### 5.1 Module `Init` (`<module>_module.go`)

Wire dependencies in four clear blocks (`// Adapters Out - PostgreSQL`, `// Adapters Out - <Other>`, `// Use Cases`, `// Adapters In - Fiber`), register `/paginated` before `/:id`, and return any use case port consumed by other modules:

```go
package exampleProduct

import (
	fiber "github.com/gofiber/fiber/v3"
	gorm "gorm.io/gorm"

	exampleProductFiber "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleProduct/adapter/in/fiber"
	exampleProductPostgresql "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleProduct/adapter/out/postgresql"
	exampleProductUsecase "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleProduct/application"
	exampleProductDomain "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleProduct/domain"
	sharedPostgresql "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/shared/adapter/out/postgresql"
)

// ============================================================================
// Functions
// ============================================================================

func Init(app *fiber.App, db *gorm.DB, authMiddleware fiber.Handler) exampleProductDomain.ExampleProductUsecaseGetByID {
	// Adapters Out - PostgreSQL
	postgresql := sharedPostgresql.NewPostgresql(db)

	exampleProductCreatePostgres := exampleProductPostgresql.NewExampleProductPostgresqlCreate(postgresql)
	exampleProductGetByIDPostgres := exampleProductPostgresql.NewExampleProductPostgresqlGetByID(postgresql)
	exampleProductGetPaginatedPostgres := exampleProductPostgresql.NewExampleProductPostgresqlGetPaginated(postgresql)
	exampleProductUpdatePostgres := exampleProductPostgresql.NewExampleProductPostgresqlUpdate(postgresql)
	exampleProductDeletePostgres := exampleProductPostgresql.NewExampleProductPostgresqlDelete(postgresql)

	// Use Cases
	exampleProductUsecaseCreate := exampleProductUsecase.NewExampleProductUsecaseCreate(exampleProductCreatePostgres)
	exampleProductUsecaseGetByID := exampleProductUsecase.NewExampleProductUsecaseGetByID(exampleProductGetByIDPostgres)
	exampleProductUsecaseGetPaginated := exampleProductUsecase.NewExampleProductUsecaseGetPaginated(exampleProductGetPaginatedPostgres)
	exampleProductUsecaseUpdate := exampleProductUsecase.NewExampleProductUsecaseUpdate(exampleProductGetByIDPostgres, exampleProductUpdatePostgres)
	exampleProductUsecaseDelete := exampleProductUsecase.NewExampleProductUsecaseDelete(exampleProductGetByIDPostgres, exampleProductDeletePostgres)

	// Adapters In - Fiber
	exampleProductFiberCreate := exampleProductFiber.NewExampleProductFiberCreate(exampleProductUsecaseCreate)
	exampleProductFiberGetByID := exampleProductFiber.NewExampleProductFiberGetByID(exampleProductUsecaseGetByID)
	exampleProductFiberGetPaginated := exampleProductFiber.NewExampleProductFiberGetPaginated(exampleProductUsecaseGetPaginated)
	exampleProductFiberUpdate := exampleProductFiber.NewExampleProductFiberUpdate(exampleProductUsecaseUpdate)
	exampleProductFiberDelete := exampleProductFiber.NewExampleProductFiberDelete(exampleProductUsecaseDelete)

	exampleProductRoutes := app.Group("/api/v1/exampleproduct")
	exampleProductRoutes.Post("/", authMiddleware, exampleProductFiberCreate.Handle)
	exampleProductRoutes.Get("/paginated", exampleProductFiberGetPaginated.Handle)
	exampleProductRoutes.Get("/:id", exampleProductFiberGetByID.Handle)
	exampleProductRoutes.Put("/:id", authMiddleware, exampleProductFiberUpdate.Handle)
	exampleProductRoutes.Delete("/:id", authMiddleware, exampleProductFiberDelete.Handle)

	return exampleProductUsecaseGetByID
}
```

### 5.2 Bootstrap Wiring (`internal/bootstrap/bootstrap_module_init.go`)

```go
func InitModules(app *fiber.App, db *gorm.DB, tokenService sharedDomain.TokenService, authMiddleware fiber.Handler) {
	exampleUserService := exampleUser.Init(app, db, tokenService)
	exampleProductService := exampleProduct.Init(app, db, authMiddleware)

	exampleUserModuleGetByID := exampleOrderExampleUser.NewExampleUserModuleGetByID(exampleUserService)
	exampleProductModuleGetByID := exampleOrderExampleProduct.NewExampleProductModuleGetByID(exampleProductService)

	exampleOrder.Init(app, db, exampleUserModuleGetByID, exampleProductModuleGetByID, authMiddleware)
}
```
