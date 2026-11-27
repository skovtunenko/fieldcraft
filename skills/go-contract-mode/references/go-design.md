# Go contract design

Use these conventions when you design a contract and the project has no
convention of its own. A project convention always wins. Each rule makes the
contract easier to review or keeps it stable while bodies are regenerated.

## Shape a feature

These steps apply to every project.

1. Start from the caller's scenario: inputs, useful result, failure outcomes,
   and constraints. Propose the smallest public operation that expresses it.
2. Place responsibilities deliberately. Identify which type owns each invariant
   and state change, which operation coordinates steps, and which dependency
   supplies an external capability. An invariant is a condition that must
   remain true. Explain these choices in the domain's terms.
3. Design models and signatures around those responsibilities. Give fields
   meaningful types; explain their units, identity, optionality, or lifecycle
   when relevant. Expose the errors and ordering constraints callers need to
   understand. Reuse project conventions and types.
4. Keep dependencies explicit. Introduce a small consumer-side interface when
   existing code is an external system, storage, or a dependency that tests
   replace; use a concrete type when no such abstraction is needed. Assert at
   compile time that the existing type implements the interface, for example
   `var _ Inventory = (*MemoryInventory)(nil)`. Extend an existing type or
   interface instead of declaring a parallel one. Explain a new package or
   interface by the responsibility it owns.
5. Prefer existing project code, then the standard library, then an installed
   dependency.

## Packages and files

- One package owns one responsibility. Name it with a short, lowercase,
  singular noun that says what it does: `order`, `cache`, `email`.
- Do not create `util`, `common`, `helpers`, or `misc` packages. Do not add a
  `pkg/` directory. Put private application code under `internal/` and
  executables under `cmd/`.
- Avoid stutter: `order.Service`, not `order.OrderService`.
- Split files by responsibility when a package grows, for example
  `model.go`, `service.go`, `errors.go`, `handlers.go`, `routes.go`.

## Types and signatures

- Return concrete types. Accept an interface only where the consumer needs a
  boundary.
- Construct with `NewXxx` and pass every dependency explicitly. Do not use
  `init()`, package-level mutable state, or a service locator.
- Make `ctx context.Context` the first parameter of any operation that can block,
  call a dependency, or be cancelled. Never store a context in a struct.
- Use functional options only when the caller really chooses optional settings;
  required inputs stay positional.
- Prefer standard library interfaces, such as `io.Reader`, over a custom
  interface with the same method.

## Interfaces at boundaries

- Declare an interface in the package that consumes it, next to the code that
  calls it. The implementation satisfies it implicitly.
- Keep it small: only the methods the consumer calls. Compose small interfaces
  when one consumer needs several capabilities.
- Do not create an interface for a single implementation that nobody needs to
  replace. A dependency that tests must replace is a real boundary.

```go
// Inventory supplies stock reservation for ordering.
type Inventory interface {
    // Reserve reserves the requested product units.
    // It returns ErrOutOfStock when stock is insufficient.
    Reserve(ctx context.Context, items []Item) error
}
```

## Errors as part of the contract

- Expose the failures that callers must tell apart as sentinel errors in
  `errors.go`, or as an error type when callers need structured details.
- Document in the godoc of each public operation which errors it returns.
- Wrap errors with `fmt.Errorf("<step>: %w", err)` so callers inspect them with
  `errors.Is` or `errors.As`. Never compare error strings.
- Return errors for expected failures. A panic is not part of a contract.

## Time and asynchronous behavior

Inject a clock or random source only when the domain needs a controlled value,
for example an expiry time recorded in a model. For tests of timers, timeouts,
and goroutines, prefer `testing/synctest` when the project's Go version provides
it; do not add a clock interface only for tests.

## Transport adapters

A transport adapter is the code that connects a transport to a public
operation: an HTTP handler, a gRPC method, a queue consumer, or a CLI command.
The project decides how to write it: its router, libraries, and code layout.
These rules hold for every transport:

- The adapter translates the request into one call of a public operation and
  translates the result back. It holds no domain rule.
- Its doc comment names the entry point, such as the route, the RPC, or the
  topic, and every response outcome with its meaning.
- Each error of the contract maps to one named outcome of the transport, such
  as a status code.
- While contract mode is active, the body lists the TODO steps and gives the
  not-implemented response of the transport, for example HTTP status 501 or
  gRPC code `Unimplemented`.
