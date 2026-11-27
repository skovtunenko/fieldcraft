# Local notes service

This module is a working source project for Go contract-mode evaluations that
need a database schema and a composition root. It uses only the Go standard
library.

## Existing behavior

`Service.Create` trims the title, rejects a blank title with `ErrEmptyTitle`,
and stores the note. `Service.Get` returns a note or `ErrNoteNotFound`.

`Store` has two implementations. `SQLStore` uses `database/sql` and the
`notes` table. `MemoryStore` serves the tests and the local server.

`migrations/` holds the schema as numbered SQL files. `Migrate` applies each
file once, in file-name order, and records it in `schema_migrations`. A new
schema change is a new file; an applied file does not change.

`NewHandler` registers the HTTP routes. `cmd/server/main.go` is the
composition root: it constructs the store and the service, and starts the
server.

## Source map

| File | Responsibility |
| --- | --- |
| `note.go` | Note model, `Store` interface, and service rules |
| `sqlstore.go` | SQL implementation of `Store` |
| `memstore.go` | Memory implementation of `Store` |
| `migrate.go`, `migrations/` | Schema files and the function that applies them |
| `http.go` | HTTP routes |
| `cmd/server/main.go` | Composition root |
| `notes_test.go` | Executed checks of the existing behavior |

## Checks

```bash
go build ./...
go vet ./...
go test -race -count=1 ./...
```

## Local scope

The module registers no SQL driver, so no test opens a database. The fixture
does not model authentication, pagination, or note deletion.
