# Domain, Shared Domain, and Application Layer Templates

## Table of Contents

1. [Shared Domain (`internal/shared/domain/`)](#1-shared-domain-internalshareddomain)
   - [Error System (`shared_domain_error.go`)](#11-error-system-shared_domain_errorgo)
   - [Pagination (`shared_domain_pagination.go`)](#12-pagination-shared_domain_paginationgo)
   - [Token Service (`shared_domain_token.go`)](#13-token-service-shared_domain_tokengo)
2. [Module Domain Layer (`internal/modules/<module>/domain/`)](#2-module-domain-layer-internalmodulesmoduledomain)
   - [Domain Errors (`<module>_domain_error.go`)](#21-domain-errors-module_domain_errorgo)
   - [Domain Models & Validation (`<module>_domain_model.go`)](#22-domain-models--validation-module_domain_modelgo)
   - [Domain Events (`<module>_domain_event.go`)](#23-domain-events-module_domain_eventgo)
   - [Domain Ports (`<module>_domain_port.go`)](#24-domain-ports-module_domain_portgo)
3. [Application Layer Use Cases (`internal/modules/<module>/application/`)](#3-application-layer-use-cases-internalmodulesmoduleapplication)
   - [Create Use Case](#31-create-use-case)
   - [GetByID Use Case](#32-getbyid-use-case)
   - [GetPaginated Use Case](#33-getpaginated-use-case)
   - [Update Use Case (with Ownership Check)](#34-update-use-case-with-ownership-check)
   - [Delete Use Case (with Ownership Check)](#35-delete-use-case-with-ownership-check)
   - [Aggregate Create Use Case (Cross-Module + Transaction + Event)](#36-aggregate-create-use-case-cross-module--transaction--event)
   - [Auth Login Use Case (Email Lookup + Password Compare + JWT)](#37-auth-login-use-case-email-lookup--password-compare--jwt)

---

## 1. Shared Domain (`internal/shared/domain/`)

### 1.1 Error System (`shared_domain_error.go`)

Every module registers a 3-letter `ErrorPrefix` constant in `internal/shared/domain/shared_domain_error.go` (`SYS`, `FIB`, `EXU`, `EXP`, `EXO`, etc.) and constructs errors via `sharedDomain.NewError` + `sharedDomain.BuildErrorID`.

```go
// In internal/shared/domain/shared_domain_error.go:
const (
	SystemErrPrefixID         ErrorPrefix = "SYS"
	FiberErrPrefixID          ErrorPrefix = "FIB"
	ExampleUserErrPrefixID    ErrorPrefix = "EXU"
	ExampleProductErrPrefixID ErrorPrefix = "EXP"
	ExampleOrderErrPrefixID   ErrorPrefix = "EXO"
)
```

Available `ErrorStatus` values in `sharedDomain`:
- `sharedDomain.BadRequest` (`400`, `BAD_REQUEST`)
- `sharedDomain.Unauthorized` (`401`, `UNAUTHORIZED`)
- `sharedDomain.Forbidden` (`403`, `FORBIDDEN`)
- `sharedDomain.NotFound` (`404`, `NOT_FOUND`)
- `sharedDomain.InternalError` (`500`, `INTERNAL_SERVER_ERROR`)

### 1.2 Pagination (`shared_domain_pagination.go`)

Always use `sharedDomain.NewPagination(page, pageSize)` in paginated use cases rather than reimplementing clamping logic:
- Default page size: `10` (`DefaultPageSize`)
- Max page size: `100` (`MaxPageSize`)
- Optional override: `sharedDomain.NewPagination(page, pageSize, sharedDomain.PaginationLimits{DefaultPageSize: 20, MaxPageSize: 50})`
- Methods: `pagination.Limit()` and `pagination.Offset()`
- Return container: `*sharedDomain.Page[*<module>Domain.<Module>]`

### 1.3 Token Service (`shared_domain_token.go`)

```go
type TokenClaims struct {
	Subject string
}

type TokenService interface {
	Generate(ctx context.Context, subject string) (string, error)
	Parse(ctx context.Context, token string) (TokenClaims, error)
}
```

---

## 2. Module Domain Layer (`internal/modules/<module>/domain/`)

### 2.1 Domain Errors (`<module>_domain_error.go`)

```go
package domain

import (
	sharedDomain "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/shared/domain"
)

// ============================================================================
// Variables
// ============================================================================

var (
	ExampleProductErrNotFound           = sharedDomain.NewError(sharedDomain.NotFound, sharedDomain.BuildErrorID(sharedDomain.ExampleProductErrPrefixID, "001"), "example product not found", nil)
	ExampleProductErrInvalidName        = sharedDomain.NewError(sharedDomain.BadRequest, sharedDomain.BuildErrorID(sharedDomain.ExampleProductErrPrefixID, "002"), "product name is required and must be 255 characters or fewer", nil)
	ExampleProductErrDescriptionTooLong = sharedDomain.NewError(sharedDomain.BadRequest, sharedDomain.BuildErrorID(sharedDomain.ExampleProductErrPrefixID, "003"), "product description must be 255 characters or fewer", nil)
	ExampleProductErrInvalidPrice       = sharedDomain.NewError(sharedDomain.BadRequest, sharedDomain.BuildErrorID(sharedDomain.ExampleProductErrPrefixID, "004"), "product price must be zero or greater", nil)
	ExampleProductErrForbidden          = sharedDomain.NewError(sharedDomain.Forbidden, sharedDomain.BuildErrorID(sharedDomain.ExampleProductErrPrefixID, "005"), "product can only be modified by its creator", nil)
)
```

### 2.2 Domain Models & Validation (`<module>_domain_model.go`)

Domain models are pure Go structs without struct tags. All business validation belongs in `New<Module>`, `Update<Module>`, and unexported `validate*` functions at the bottom of the file.

```go
package domain

import (
	strings "strings"
	time "time"
	utf8 "unicode/utf8"
)

// ============================================================================
// Constants
// ============================================================================

const (
	ExampleProductNameMaxLength        = 255
	ExampleProductDescriptionMaxLength = 255
	ExampleProductMinPrice             = 0
)

// ============================================================================
// Types
// ============================================================================

type ExampleProduct struct {
	ID          string
	Name        string
	Description string
	Price       int64
	CreatedBy   string
	UpdatedBy   string
	CreatedAt   time.Time
	UpdatedAt   time.Time
}

// ============================================================================
// Constructors
// ============================================================================

func NewExampleProduct(name, description string, price int64, createdBy string) (*ExampleProduct, error) {
	name, description, price, err := validateExampleProduct(name, description, price)
	if err != nil {
		return nil, err
	}

	now := time.Now().UTC()

	return &ExampleProduct{
		Name:        name,
		Description: description,
		Price:       price,
		CreatedBy:   createdBy,
		UpdatedBy:   createdBy,
		CreatedAt:   now,
		UpdatedAt:   now,
	}, nil
}

// ============================================================================
// Methods
// ============================================================================

func (e *ExampleProduct) UpdateExampleProduct(name, description string, price int64, updatedBy string) error {
	name, description, price, err := validateExampleProduct(name, description, price)
	if err != nil {
		return err
	}

	e.Name = name
	e.Description = description
	e.Price = price
	e.UpdatedBy = updatedBy
	e.UpdatedAt = time.Now().UTC()

	return nil
}

func (e *ExampleProduct) IsOwnedBy(userID string) bool {
	return e.CreatedBy == userID
}

// ============================================================================
// Functions
// ============================================================================

func validateExampleProduct(name, description string, price int64) (string, string, int64, error) {
	name, err := validateExampleProductName(name)
	if err != nil {
		return "", "", 0, err
	}

	description, err = validateExampleProductDescription(description)
	if err != nil {
		return "", "", 0, err
	}

	price, err = validateExampleProductPrice(price)
	if err != nil {
		return "", "", 0, err
	}

	return name, description, price, nil
}

func validateExampleProductName(name string) (string, error) {
	name = strings.TrimSpace(name)

	if name == "" || utf8.RuneCountInString(name) > ExampleProductNameMaxLength {
		return "", ExampleProductErrInvalidName
	}

	return name, nil
}

func validateExampleProductDescription(description string) (string, error) {
	description = strings.TrimSpace(description)
	if utf8.RuneCountInString(description) > ExampleProductDescriptionMaxLength {
		return "", ExampleProductErrDescriptionTooLong
	}

	return description, nil
}

func validateExampleProductPrice(price int64) (int64, error) {
	if price < ExampleProductMinPrice {
		return 0, ExampleProductErrInvalidPrice
	}

	return price, nil
}
```

### 2.3 Domain Events (`<module>_domain_event.go`)

Include `<module>_domain_event.go` when a module publishes domain events through an output port:

```go
package domain

import (
	time "time"
)

// ============================================================================
// Constants
// ============================================================================

const (
	EventTypeOrderCreated = "ORDER_CREATED"
)

// ============================================================================
// Types
// ============================================================================

type ExampleOrderEvent struct {
	EventType string
	OrderID   string
	Timestamp time.Time
}

// ============================================================================
// Constructors
// ============================================================================

func NewExampleOrderEvent(eventType, orderID string) ExampleOrderEvent {
	return ExampleOrderEvent{
		EventType: eventType,
		OrderID:   orderID,
		Timestamp: time.Now().UTC(),
	}
}
```

### 2.4 Domain Ports (`<module>_domain_port.go`)

Use subgroup section banners (`Usecase Ports`, `PostgreSQL Ports`, `Event Ports`, `Cross-module Ports`, `Security Ports`). Notice how cross-module ports use the `<Provider>Module<Operation>` naming exception and return consumer-owned lightweight structs (`ExampleOrderUser`, `ExampleOrderProductInfo`):

```go
package domain

import (
	context "context"

	sharedDomain "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/shared/domain"
)

// ============================================================================
// Usecase Ports
// ============================================================================

type ExampleOrderUsecaseCreate interface {
	Execute(ctx context.Context, input ExampleOrder) (*ExampleOrder, error)
}

type ExampleOrderUsecaseGetByID interface {
	Execute(ctx context.Context, id string) (*ExampleOrder, error)
}

type ExampleOrderUsecaseGetPaginated interface {
	Execute(ctx context.Context, page, pageSize int, search string) (*sharedDomain.Page[*ExampleOrder], error)
}

// ============================================================================
// PostgreSQL Ports
// ============================================================================

type ExampleOrderPostgresqlTransaction interface {
	WithinTransaction(ctx context.Context, fn func(ctx context.Context) error) error
}

type ExampleOrderPostgresqlCreate interface {
	Execute(ctx context.Context, order *ExampleOrder) error
}

type ExampleOrderProductPostgresqlCreateMultiple interface {
	Execute(ctx context.Context, products []*ExampleOrderProduct) error
}

type ExampleOrderPostgresqlGetByID interface {
	Execute(ctx context.Context, id string) (*ExampleOrder, error)
}

type ExampleOrderPostgresqlGetPaginated interface {
	Execute(ctx context.Context, limit, offset int, search string) ([]*ExampleOrder, int64, error)
}

// ============================================================================
// Event Ports
// ============================================================================

type ExampleOrderEventPublisher interface {
	Execute(ctx context.Context, event ExampleOrderEvent) error
}

// ============================================================================
// Cross-module Ports
// ============================================================================

type ExampleOrderUser struct {
	ID   string
	Name string
}

type ExampleOrderProductInfo struct {
	ID   string
	Name string
}

type ExampleUserModuleGetByID interface {
	Execute(ctx context.Context, id string) (ExampleOrderUser, error)
}

type ExampleProductModuleGetByID interface {
	Execute(ctx context.Context, id string) (ExampleOrderProductInfo, error)
}
```

---

## 3. Application Layer Use Cases (`internal/modules/<module>/application/`)

### 3.1 Create Use Case (`<module>_usecase_create.go`)

```go
package application

import (
	context "context"

	exampleProductDomain "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleProduct/domain"
)

// ============================================================================
// Types
// ============================================================================

type ExampleProductUsecaseCreate struct {
	exampleProductCreatePostgres exampleProductDomain.ExampleProductPostgresqlCreate
}

// ============================================================================
// Constructors
// ============================================================================

func NewExampleProductUsecaseCreate(exampleProductCreatePostgres exampleProductDomain.ExampleProductPostgresqlCreate) exampleProductDomain.ExampleProductUsecaseCreate {
	return &ExampleProductUsecaseCreate{
		exampleProductCreatePostgres: exampleProductCreatePostgres,
	}
}

// ============================================================================
// Methods
// ============================================================================

func (uc *ExampleProductUsecaseCreate) Execute(ctx context.Context, exampleProductInput exampleProductDomain.ExampleProduct) (*exampleProductDomain.ExampleProduct, error) {
	exampleProduct, err := exampleProductDomain.NewExampleProduct(
		exampleProductInput.Name,
		exampleProductInput.Description,
		exampleProductInput.Price,
		exampleProductInput.CreatedBy,
	)
	if err != nil {
		return nil, err
	}

	if err := uc.exampleProductCreatePostgres.Execute(ctx, exampleProduct); err != nil {
		return nil, err
	}

	return exampleProduct, nil
}
```

### 3.2 GetByID Use Case (`<module>_usecase_getByID.go`)

```go
package application

import (
	context "context"

	exampleProductDomain "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleProduct/domain"
)

// ============================================================================
// Types
// ============================================================================

type ExampleProductUsecaseGetByID struct {
	exampleProductGetByIDPostgres exampleProductDomain.ExampleProductPostgresqlGetByID
}

// ============================================================================
// Constructors
// ============================================================================

func NewExampleProductUsecaseGetByID(exampleProductGetByIDPostgres exampleProductDomain.ExampleProductPostgresqlGetByID) exampleProductDomain.ExampleProductUsecaseGetByID {
	return &ExampleProductUsecaseGetByID{
		exampleProductGetByIDPostgres: exampleProductGetByIDPostgres,
	}
}

// ============================================================================
// Methods
// ============================================================================

func (uc *ExampleProductUsecaseGetByID) Execute(ctx context.Context, id string) (*exampleProductDomain.ExampleProduct, error) {
	return uc.exampleProductGetByIDPostgres.Execute(ctx, id)
}
```

### 3.3 GetPaginated Use Case (`<module>_usecase_getPaginated.go`)

```go
package application

import (
	context "context"

	exampleProductDomain "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleProduct/domain"
	sharedDomain "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/shared/domain"
)

// ============================================================================
// Types
// ============================================================================

type ExampleProductUsecaseGetPaginated struct {
	exampleProductGetPaginatedPostgres exampleProductDomain.ExampleProductPostgresqlGetPaginated
}

// ============================================================================
// Constructors
// ============================================================================

func NewExampleProductUsecaseGetPaginated(exampleProductGetPaginatedPostgres exampleProductDomain.ExampleProductPostgresqlGetPaginated) exampleProductDomain.ExampleProductUsecaseGetPaginated {
	return &ExampleProductUsecaseGetPaginated{
		exampleProductGetPaginatedPostgres: exampleProductGetPaginatedPostgres,
	}
}

// ============================================================================
// Methods
// ============================================================================

func (uc *ExampleProductUsecaseGetPaginated) Execute(ctx context.Context, page, pageSize int, search string) (*sharedDomain.Page[*exampleProductDomain.ExampleProduct], error) {
	pagination := sharedDomain.NewPagination(page, pageSize)

	exampleProducts, total, err := uc.exampleProductGetPaginatedPostgres.Execute(ctx, pagination.Limit(), pagination.Offset(), search)
	if err != nil {
		return nil, err
	}

	return &sharedDomain.Page[*exampleProductDomain.ExampleProduct]{
		Items:      exampleProducts,
		Pagination: pagination,
		Total:      total,
	}, nil
}
```

### 3.4 Update Use Case (with Ownership Check) (`<module>_usecase_update.go`)

```go
package application

import (
	context "context"

	exampleProductDomain "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleProduct/domain"
)

// ============================================================================
// Types
// ============================================================================

type ExampleProductUsecaseUpdate struct {
	exampleProductGetByIDPostgres exampleProductDomain.ExampleProductPostgresqlGetByID
	exampleProductUpdatePostgres  exampleProductDomain.ExampleProductPostgresqlUpdate
}

// ============================================================================
// Constructors
// ============================================================================

func NewExampleProductUsecaseUpdate(
	exampleProductGetByIDPostgres exampleProductDomain.ExampleProductPostgresqlGetByID,
	exampleProductUpdatePostgres exampleProductDomain.ExampleProductPostgresqlUpdate,
) exampleProductDomain.ExampleProductUsecaseUpdate {
	return &ExampleProductUsecaseUpdate{
		exampleProductGetByIDPostgres: exampleProductGetByIDPostgres,
		exampleProductUpdatePostgres:  exampleProductUpdatePostgres,
	}
}

// ============================================================================
// Methods
// ============================================================================

func (uc *ExampleProductUsecaseUpdate) Execute(ctx context.Context, id string, exampleProductInput exampleProductDomain.ExampleProduct) (*exampleProductDomain.ExampleProduct, error) {
	exampleProduct, err := uc.exampleProductGetByIDPostgres.Execute(ctx, id)
	if err != nil {
		return nil, err
	}

	if !exampleProduct.IsOwnedBy(exampleProductInput.UpdatedBy) {
		return nil, exampleProductDomain.ExampleProductErrForbidden
	}

	if err := exampleProduct.UpdateExampleProduct(
		exampleProductInput.Name,
		exampleProductInput.Description,
		exampleProductInput.Price,
		exampleProductInput.UpdatedBy,
	); err != nil {
		return nil, err
	}

	if err := uc.exampleProductUpdatePostgres.Execute(ctx, exampleProduct); err != nil {
		return nil, err
	}

	return exampleProduct, nil
}
```

### 3.5 Delete Use Case (with Ownership Check) (`<module>_usecase_delete.go`)

```go
package application

import (
	context "context"

	exampleProductDomain "github.com/kelsonwinith/learn.go-hexagonal-architecture/internal/modules/exampleProduct/domain"
)

// ============================================================================
// Types
// ============================================================================

type ExampleProductUsecaseDelete struct {
	exampleProductGetByIDPostgres exampleProductDomain.ExampleProductPostgresqlGetByID
	exampleProductDeletePostgres  exampleProductDomain.ExampleProductPostgresqlDelete
}

// ============================================================================
// Constructors
// ============================================================================

func NewExampleProductUsecaseDelete(
	exampleProductGetByIDPostgres exampleProductDomain.ExampleProductPostgresqlGetByID,
	exampleProductDeletePostgres exampleProductDomain.ExampleProductPostgresqlDelete,
) exampleProductDomain.ExampleProductUsecaseDelete {
	return &ExampleProductUsecaseDelete{
		exampleProductGetByIDPostgres: exampleProductGetByIDPostgres,
		exampleProductDeletePostgres:  exampleProductDeletePostgres,
	}
}

// ============================================================================
// Methods
// ============================================================================

func (uc *ExampleProductUsecaseDelete) Execute(ctx context.Context, id, userID string) error {
	exampleProduct, err := uc.exampleProductGetByIDPostgres.Execute(ctx, id)
	if err != nil {
		return err
	}

	if !exampleProduct.IsOwnedBy(userID) {
		return exampleProductDomain.ExampleProductErrForbidden
	}

	return uc.exampleProductDeletePostgres.Execute(ctx, id, userID)
}
```

### 3.6 Aggregate Create Use Case (Cross-Module + Transaction + Event) (`exampleOrder_usecase_create.go`)

```go
func (uc *ExampleOrderUsecaseCreate) Execute(ctx context.Context, exampleOrderInput exampleOrderDomain.ExampleOrder) (*exampleOrderDomain.ExampleOrder, error) {
	// Cross-module: ensure the referenced user exists.
	if _, err := uc.exampleUserModuleGetByID.Execute(ctx, exampleOrderInput.UserID); err != nil {
		return nil, err
	}

	// Cross-module: resolve each referenced product and use its name.
	for _, exampleOrderProduct := range exampleOrderInput.Products {
		exampleOrderProductInfo, err := uc.exampleProductModuleGetByID.Execute(ctx, exampleOrderProduct.ProductID)
		if err != nil {
			return nil, err
		}
		exampleOrderProduct.Name = exampleOrderProductInfo.Name
	}

	exampleOrder, err := exampleOrderDomain.NewExampleOrder(exampleOrderInput.Name, exampleOrderInput.Description, exampleOrderInput.UserID, exampleOrderInput.Products, exampleOrderInput.CreatedBy)
	if err != nil {
		return nil, err
	}

	err = uc.exampleOrderPostgresqlTransaction.WithinTransaction(ctx, func(ctx context.Context) error {
		if err := uc.exampleOrderCreatePostgres.Execute(ctx, exampleOrder); err != nil {
			return err
		}

		for _, exampleOrderProduct := range exampleOrder.Products {
			exampleOrderProduct.OrderID = exampleOrder.ID
		}

		return uc.exampleOrderCreateProductsPostgres.Execute(ctx, exampleOrder.Products)
	})
	if err != nil {
		return nil, err
	}

	exampleOrderEvent := exampleOrderDomain.NewExampleOrderEvent(exampleOrderDomain.EventTypeOrderCreated, exampleOrder.ID)
	if err := uc.exampleOrderEventPublisher.Execute(ctx, exampleOrderEvent); err != nil {
		return nil, err
	}

	return exampleOrder, nil
}
```

### 3.7 Auth Login Use Case (Email Lookup + Password Compare + JWT) (`exampleUser_usecase_login.go`)

```go
func (uc *ExampleUserUsecaseLogin) Execute(ctx context.Context, email, password string) (string, *exampleUserDomain.ExampleUser, error) {
	email = strings.ToLower(strings.TrimSpace(email))
	if email == "" || password == "" {
		return "", nil, exampleUserDomain.ExampleUserErrInvalidCredentials
	}

	exampleUser, err := uc.exampleUserGetByEmailPostgres.Execute(ctx, email)
	if err != nil {
		if errors.Is(err, exampleUserDomain.ExampleUserErrNotFound) {
			return "", nil, exampleUserDomain.ExampleUserErrInvalidCredentials
		}
		return "", nil, err
	}

	if err := uc.exampleUserPasswordComparer.Execute(exampleUser.PasswordHash, password); err != nil {
		return "", nil, exampleUserDomain.ExampleUserErrInvalidCredentials
	}

	token, err := uc.exampleUserTokenService.Generate(ctx, exampleUser.ID)
	if err != nil {
		return "", nil, err
	}

	return token, exampleUser, nil
}
```
