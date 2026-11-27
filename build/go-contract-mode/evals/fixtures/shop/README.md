# Local order service

This module is the working source project for Go contract-mode evaluations.
It uses only the Go standard library. All state stays in memory.

## Existing behavior

`Checkout.Place` quotes catalog prices, reserves stock, charges the account,
and saves a paid order. The caller supplies an order ID and product quantities.
`Money` stores euro cents. The catalog owns prices; the caller supplies no total.

An order keeps its payment ID and reservation ID for reconciliation. A repeated
saved order ID returns `ErrOrderExists` before any further stock or payment effect.

Payment failure releases the stock reservation. Save failure refunds the charge
and releases the reservation. Cleanup uses a separate five-second deadline, so
caller cancellation does not prevent compensation. The returned error retains
the original failure and each cleanup failure through `errors.Is`.

`MemoryGateway` simulates one funded account. Its charge key is the order ID.
An identical charge retry returns the original payment ID. A different amount
returns `ErrPaymentConflict`. Refunded keys return `ErrPaymentRefunded` on a
later charge. Refund and reservation release are idempotent.

`MemoryOrders.Save` creates records. It does not update existing records.
`Get` returns independent snapshots. The only existing order status is `paid`.
There is no cancellation operation or status update method yet.

## Source map

| File | Responsibility |
| --- | --- |
| `catalog.go` | Product types, catalog prices, and checked quoting |
| `inventory.go` | Atomic stock reservation and release |
| `payment.go` | Local charge, decline, and refund state |
| `orders.go` | Paid order records and memory storage |
| `checkout.go` | Consumer interfaces and the placement flow |
| `shop_test.go` | Executed checks of the existing behavior |
| `cmd/demo/main.go` | Complete purchase using the memory adapters |

## Checks

From this module, run:

```bash
go build ./...
go vet ./...
go test -race -count=1 ./...
go run ./cmd/demo
```

The demo starts with five books and a balance of 10000 cents. It buys two books
at 1200 cents each. Its output is:

```text
order=demo-order status=paid total_cents=2400 stock=3 balance_cents=7600
```

Run `gofmt -l .` as well: it must print nothing.

## Local scope

Use one `Checkout` instance per process with the supplied adapters. Placement
is serialized through that instance. The memory adapters have their own locks.
The fixture does not model multiple service instances, process restart recovery,
a remote payment provider, or an HTTP transport. A failed compensation remains
visible as an error and residual local state; there is no recovery worker.
