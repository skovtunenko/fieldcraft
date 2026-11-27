package shop

import (
	"context"
	"errors"
	"slices"
	"sync"
)

var (
	ErrOrderExists   = errors.New("order already exists")
	ErrOrderNotFound = errors.New("order not found")
)

// OrderID is chosen by the caller and also identifies the payment request.
type OrderID string

// OrderStatus is the recorded lifecycle state of an order.
type OrderStatus string

const OrderPaid OrderStatus = "paid"

// Order is a paid order with references used to reconcile stock and payment.
type Order struct {
	// ID is the caller's order identifier.
	ID OrderID
	// Items are the product quantities accepted during checkout.
	Items []Item
	// Total is the quoted amount in euro cents.
	Total Money
	// Status is the recorded order lifecycle state.
	Status OrderStatus
	// ReservationID links the order to the stock it holds.
	ReservationID ReservationID
	// PaymentID links the order to its accepted charge.
	PaymentID PaymentID
}

// MemoryOrders stores orders in memory and returns independent copies.
type MemoryOrders struct {
	mu     sync.Mutex
	orders map[OrderID]Order
}

func NewMemoryOrders() *MemoryOrders {
	return &MemoryOrders{orders: make(map[OrderID]Order)}
}

// Save creates a paid order; it never overwrites an existing identifier.
func (m *MemoryOrders) Save(ctx context.Context, order Order) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	if _, exists := m.orders[order.ID]; exists {
		return ErrOrderExists
	}
	order.Items = slices.Clone(order.Items)
	m.orders[order.ID] = order
	return nil
}

// Get returns a snapshot of an order, or ErrOrderNotFound.
func (m *MemoryOrders) Get(ctx context.Context, id OrderID) (Order, error) {
	if err := ctx.Err(); err != nil {
		return Order{}, err
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	order, exists := m.orders[id]
	if !exists {
		return Order{}, ErrOrderNotFound
	}
	order.Items = slices.Clone(order.Items)
	return order, nil
}
