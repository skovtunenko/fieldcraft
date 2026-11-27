package shop

import (
	"context"
	"errors"
	"fmt"
	"strconv"
	"sync"
)

var ErrOutOfStock = errors.New("out of stock")

// ReservationID identifies stock held for an order.
type ReservationID string

// MemoryInventory holds available stock and active reservations in memory.
type MemoryInventory struct {
	mu           sync.Mutex
	stock        map[SKU]int
	reservations map[ReservationID]map[SKU]int
	next         uint64
}

// NewMemoryInventory copies non-negative stock counts.
func NewMemoryInventory(stock map[SKU]int) (*MemoryInventory, error) {
	copy := make(map[SKU]int, len(stock))
	for sku, quantity := range stock {
		if sku == "" || quantity < 0 {
			return nil, ErrInvalidOrder
		}
		copy[sku] = quantity
	}
	return &MemoryInventory{stock: copy, reservations: make(map[ReservationID]map[SKU]int)}, nil
}

// Reserve takes all requested units or none, including repeated SKUs.
// It returns ErrOutOfStock when the total quantity of a product is unavailable.
func (m *MemoryInventory) Reserve(ctx context.Context, items []Item) (ReservationID, error) {
	if err := ctx.Err(); err != nil {
		return "", err
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	if len(items) == 0 {
		return "", ErrInvalidOrder
	}
	requested := make(map[SKU]int)
	for _, item := range items {
		if item.Quantity <= 0 || item.SKU == "" {
			return "", ErrInvalidOrder
		}
		// Compare before adding so duplicate SKUs cannot oversell or overflow.
		if item.Quantity > m.stock[item.SKU]-requested[item.SKU] {
			return "", fmt.Errorf("reserve %s: %w", item.SKU, ErrOutOfStock)
		}
		requested[item.SKU] += item.Quantity
	}
	m.next++
	id := ReservationID("r-" + strconv.FormatUint(m.next, 10))
	for sku, quantity := range requested {
		m.stock[sku] -= quantity
	}
	m.reservations[id] = requested
	return id, nil
}

// Release restores the held stock. Releasing an unknown reservation is a no-op.
func (m *MemoryInventory) Release(ctx context.Context, id ReservationID) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	for sku, quantity := range m.reservations[id] {
		m.stock[sku] += quantity
	}
	delete(m.reservations, id)
	return nil
}

// Available returns the number of units not held by a reservation.
func (m *MemoryInventory) Available(sku SKU) int {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.stock[sku]
}
