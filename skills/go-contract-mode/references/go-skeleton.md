# Go skeleton patterns

Use these patterns when writing bodies and tests. Adapt names and types to the
project. The examples illustrate allowed structure, not a required architecture.

## Choose a stub return

Every new body ends with a stub return after its intent.

- With an `error` result, reuse a suitable project not-implemented error.
  Check its identity and how callers recognize wrapped errors. If none exists,
  propose the error and its location, then create it only after consent.
- Without an `error` result, return the type's zero value and add a
  `TODO(contract)` marker. Keep the intended signature. Where the caller uses
  the result at once, return a value that is safe to use: a stub that derives
  a context returns its input context and a release function that does nothing.
- In a transport adapter body, write the not-implemented response of the
  transport after the intent: `w.WriteHeader(http.StatusNotImplemented)` in an
  HTTP handler, code `Unimplemented` in a gRPC method. Its pending tests skip
  on that response.
- Use no panic stub. An intentionally unsupported operation is a different
  contract from unfinished implementation; do not use `errors.ErrUnsupported`
  to mean not implemented.

For an approved error declaration, the ordinary form is:

```go
// ErrNotImplemented marks behavior whose implementation is pending.
var ErrNotImplemented = errors.New("not implemented")
```

## Facade: write the intent in the public body

This fragment assumes the types, receiver dependencies, and the stub error have
already been agreed. The flow lives in one public body as ordered intent.

```go
// Place reserves the requested items and records an order.
// It returns ErrEmptyOrder for an order without items and ErrOutOfStock
// when the requested quantity cannot be reserved.
func (s *Service) Place(ctx context.Context, request PlaceRequest) (OrderID, error) {
    // TODO(contract):
    //  1. Return ErrEmptyOrder when request.Items is empty or a quantity is not positive.
    //  2. Return the OrderID that request.Key already placed, found with
    //     s.store.Find; a repeated request has no new effect.
    //  3. Reserve request.Items with s.inventory.Reserve; keep ErrOutOfStock,
    //     and nothing is reserved.
    //  4. Record the order with s.store.Record under request.Key.
    //  5. When step 4 fails, release the reservation with s.inventory.Release
    //     and return the record error; a release failure joins it, and the
    //     stock stays reserved.
    //  6. Return the recorded OrderID.
    return "", ErrNotImplemented
}

// Total returns the order total in minor currency units.
func Total(items []Item) Money {
    // TODO(contract): sum Item.Price × Item.Quantity; all items share one currency.
    return 0
}
```

Each step names a declared dependency, field, or error, so a reviewer can check
the intent against the declarations. Each step that can fail states its
outcome. Constructors can assign dependencies so
the skeleton is testable; they do not connect to a real database or start a
server.

## Internals: connect the public body to internal stubs

The internals phase replaces the public body's intent with calls to new stubs. Each stub
owns one responsibility and takes over the intent steps for it. The public
body shows the flow as code: stub calls, wrapped-error returns, and the
branches, loops, and early returns between them. It can also hold an existing
receiver lock around those calls. Every condition is a stub result or a check
of a declared error. Calculations, dependency calls, and result assembly
belong to a stub. A return from the first stub does not demonstrate that later
steps ran.

```go
func (s *Service) Place(ctx context.Context, request PlaceRequest) (OrderID, error) {
    if err := validate(request); err != nil {
        return "", fmt.Errorf("validate order: %w", err)
    }
    // Early return: a repeated request returns the order it already placed.
    if id, found := s.placed(ctx, request); found {
        return id, nil
    }
    reservation, err := s.reserve(ctx, request.Items)
    if err != nil {
        return "", fmt.Errorf("reserve order: %w", err)
    }
    id, err := s.record(ctx, request, reservation)
    if err != nil {
        // Compensation is visible in the flow; its work stays in the stub.
        return "", s.release(ctx, reservation, err)
    }
    return id, nil
}

func (s *Service) placed(ctx context.Context, request PlaceRequest) (OrderID, bool) {
    // TODO(contract): look up request.Key with s.store.Find; report the
    // OrderID of the order that this key already placed.
    return "", false
}

func (s *Service) release(ctx context.Context, reservation ReservationID, cause error) error {
    // TODO(contract): release reservation with s.inventory.Release and
    // return cause; a release failure joins it, and the stock stays reserved.
    return ErrNotImplemented
}

func validate(request PlaceRequest) error {
    // TODO(contract): return ErrEmptyOrder when request.Items is empty or a
    // quantity is not positive.
    return ErrNotImplemented
}

func (s *Service) reserve(ctx context.Context, items []Item) (ReservationID, error) {
    // TODO(contract): reserve items with s.inventory.Reserve; keep ErrOutOfStock.
    return "", ErrNotImplemented
}

func (s *Service) record(ctx context.Context, request PlaceRequest, reservation ReservationID) (OrderID, error) {
    // TODO(contract):
    //  1. Record the order with s.store.Record under request.Key; on failure
    //     return its error, and no order exists.
    //  2. Return the recorded OrderID.
    return "", ErrNotImplemented
}
```

## Composition root and other resources

- In `main` or the project's wiring code, write the construction of the
  feature's types, the passing of dependencies, and the registration of routes
  and handlers. The program builds and starts as before. Work that runs at
  startup, such as a background loop or a connection to a new system, is
  intent.
- Write in full the declarative files that the feature needs: schema
  migrations, OpenAPI or protobuf definitions, configuration keys with
  defaults, and code regenerated by the project's own command.
- A statement or script that changes data is behavior. Write it as an intent
  comment in that file's comment syntax. A migration runner that records each
  applied file would record an intent-only file as applied, and the change
  would never run. Put the data change in its own file, keep that file out of
  the files that the runner applies, for example with a suffix that the
  runner does not match, and show its target name in the contract map.
- Follow the project's conventions for each resource and run its own check,
  such as a linter or a generator, when the project has one.

## Write test scenarios

Follow the project's test conventions first: its layout, helpers, assertion
and mock libraries, and naming. The form below applies when the project has
none.

For each public entry, write its test scenarios as a table-driven test. A case
is data: a name, the inputs the conversation settled, and the expected outcome,
all as Go values. A description of the case in a string is not a scenario.
Cover the agreed meaningful success and failure scenarios. Assert the agreed
effects and the agreed absence of effects, such as a stored record, as well as
the returned values: a case that checks only the error passes an
implementation that saves before it fails. Where no decision
settled a detail, leave a `TODO(contract)` line in the case; do not invent
domain rules to fill a table. Use compile-time satisfaction assertions for the
interface/implementation pairs already present in the design.

When a case must prepare dependencies, give the table a factory function that
returns them, so that each case owns its preparation:

```go
func TestService_Place(t *testing.T) {
    type fields struct {
        inventory Inventory
        store     Store
    }
    type args struct {
        request PlaceRequest
    }
    tests := []struct {
        name       string
        fieldsFunc func(t *testing.T) fields // prepares the dependencies of the case
        args       args
        want       OrderID
        wantErr    error
        wantStored bool // an order exists under request.Key after the call
    }{
        {
            name: "out of stock records no order",
            fieldsFunc: func(t *testing.T) fields {
                t.Helper()
                return fields{inventory: NewMemoryInventory(nil), store: NewMemoryStore()}
            },
            args:    args{request: PlaceRequest{Key: "k1", Items: []Item{{SKU: "book", Quantity: 2}}}},
            wantErr:    ErrOutOfStock,
            wantStored: false,
        },
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            f := tt.fieldsFunc(t)
            got, err := NewService(f.inventory, f.store).Place(context.Background(), tt.args.request)
            skipIfStub(t, err)
            if !errors.Is(err, tt.wantErr) {
                t.Fatalf("Place() error = %v, want %v", err, tt.wantErr)
            }
            if got != tt.want {
                t.Errorf("Place() = %q, want %q", got, tt.want)
            }
            if _, stored, err := f.store.Find(context.Background(), tt.args.request.Key); err != nil || stored != tt.wantStored {
                t.Errorf("order stored = %v (err %v), want %v", stored, err, tt.wantStored)
            }
        })
    }
}
```

For error-returning paths, call the entry and skip only when it actually returns
the project's stub error. Use the project's normal error inspection convention.
For a sentinel that supports `errors.Is`, the helper can be:

```go
func skipIfStub(t *testing.T, err error) {
    t.Helper()
    if errors.Is(err, ErrNotImplemented) {
        t.Skip("contract stub: behavior not implemented")
    }
}
```

Run the helper before the behavior assertions. Once the leaf no longer returns
the stub error, those assertions run. Report which cases skipped; this is not a
claim that every branch of the call chain was exercised.

For a body without an error result, put an explicit `t.Skip` with a contract
reason that names the body in its pending behavior test. Do the same when an
internals-phase coordinating body can return success without reaching a stub,
for example a loop over a collection stub that returns an empty result: in
the internals phase, check each case again, and replace its skip on the stub
error with an explicit skip that names the pending bodies. Retain real inputs and expected outcomes
below the skip, so that only the skip keeps the test from running. Keep the expectation
the domain needs, even where the stub's zero result fails it.

At contract approval, keep `TODO(contract)` intent, stub returns, and
contract-related `t.Skip` calls. They mark the pending behavior. Preserve unrelated skips that already belong to the project.
