package shop

import (
	"context"
	"errors"
	"fmt"
	"slices"
	"sync"
	"time"
)

// Inventory owns the stock used during checkout.
type Inventory interface {
	Reserve(context.Context, []Item) (ReservationID, error)
	Release(context.Context, ReservationID) error
}

// Payments accepts and compensates local payment requests.
type Payments interface {
	Charge(context.Context, OrderID, Money) (PaymentID, error)
	Refund(context.Context, PaymentID) error
}

// Orders stores and reads the paid orders produced by checkout.
type Orders interface {
	Save(context.Context, Order) error
	Get(context.Context, OrderID) (Order, error)
}

var (
	_ Inventory = (*MemoryInventory)(nil)
	_ Payments  = (*MemoryGateway)(nil)
	_ Orders    = (*MemoryOrders)(nil)
)

// PlaceRequest identifies an order and the products to purchase.
type PlaceRequest struct {
	// ID is chosen by the caller; reusing a saved ID returns ErrOrderExists.
	ID OrderID
	// Items specify positive product quantities. Catalog owns their prices.
	Items []Item
}

// Checkout coordinates quoting, stock reservation, payment, and order storage.
// A single Checkout serializes placement to avoid duplicate stock reservations.
type Checkout struct {
	mu        sync.Mutex
	catalog   *Catalog
	inventory Inventory
	payments  Payments
	orders    Orders
}

func NewCheckout(catalog *Catalog, inventory Inventory, payments Payments, orders Orders) *Checkout {
	return &Checkout{catalog: catalog, inventory: inventory, payments: payments, orders: orders}
}

// Place returns a saved paid order. It quotes catalog prices before any effects.
// Payment failure releases the reservation. Save failure refunds and releases.
// Compensation has its own five-second deadline, independent of caller cancellation.
// Returned errors preserve both the original failure and any compensation failures.
func (c *Checkout) Place(ctx context.Context, request PlaceRequest) (Order, error) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if err := ctx.Err(); err != nil {
		return Order{}, err
	}
	if request.ID == "" {
		return Order{}, ErrInvalidOrder
	}
	if _, err := c.orders.Get(ctx, request.ID); err == nil {
		return Order{}, ErrOrderExists
	} else if !errors.Is(err, ErrOrderNotFound) {
		return Order{}, fmt.Errorf("check order: %w", err)
	}
	items := slices.Clone(request.Items)
	total, err := c.catalog.Quote(items)
	if err != nil {
		return Order{}, fmt.Errorf("quote: %w", err)
	}
	reservation, err := c.inventory.Reserve(ctx, items)
	if err != nil {
		return Order{}, fmt.Errorf("reserve: %w", err)
	}
	cleanup := func() (context.Context, context.CancelFunc) {
		return context.WithTimeout(context.WithoutCancel(ctx), 5*time.Second)
	}
	payment, err := c.payments.Charge(ctx, request.ID, total)
	if err != nil {
		cleanupCtx, cancel := cleanup()
		defer cancel()
		return Order{}, errors.Join(fmt.Errorf("charge: %w", err), c.inventory.Release(cleanupCtx, reservation))
	}
	order := Order{ID: request.ID, Items: items, Total: total, Status: OrderPaid, ReservationID: reservation, PaymentID: payment}
	if err := c.orders.Save(ctx, order); err != nil {
		cleanupCtx, cancel := cleanup()
		defer cancel()
		refundErr := c.payments.Refund(cleanupCtx, payment)
		releaseErr := c.inventory.Release(cleanupCtx, reservation)
		return Order{}, errors.Join(fmt.Errorf("save: %w", err), refundErr, releaseErr)
	}
	return order, nil
}
