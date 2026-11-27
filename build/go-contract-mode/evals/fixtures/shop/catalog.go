// Package shop implements a local order service used as an evaluation fixture.
package shop

import (
	"errors"
	"fmt"
)

// SKU identifies a product in the catalog.
type SKU string

// Money is an amount in euro cents.
type Money int64

// Item is a requested quantity of one product.
type Item struct {
	// SKU identifies the product.
	SKU SKU
	// Quantity is the number of units requested; it must be positive.
	Quantity int
}

var (
	ErrInvalidOrder = errors.New("invalid order")
	ErrUnknownSKU   = errors.New("unknown product")
)

// Catalog owns the current prices. Checkout takes prices from this catalog.
type Catalog struct {
	prices map[SKU]Money
}

// NewCatalog copies positive prices, expressed in euro cents.
func NewCatalog(prices map[SKU]Money) (*Catalog, error) {
	copy := make(map[SKU]Money, len(prices))
	for sku, price := range prices {
		if sku == "" || price <= 0 {
			return nil, fmt.Errorf("catalog price for %q: %w", sku, ErrInvalidOrder)
		}
		copy[sku] = price
	}
	return &Catalog{prices: copy}, nil
}

// Quote returns the total price without changing stock or accepting payment.
// It returns ErrUnknownSKU for a missing product and ErrInvalidOrder for an
// empty order, non-positive quantities, or an amount that cannot fit in Money.
func (c *Catalog) Quote(items []Item) (Money, error) {
	if len(items) == 0 {
		return 0, ErrInvalidOrder
	}
	const maxMoney Money = 1<<63 - 1
	var total Money
	for _, item := range items {
		if item.Quantity <= 0 {
			return 0, ErrInvalidOrder
		}
		price, ok := c.prices[item.SKU]
		if !ok {
			return 0, fmt.Errorf("quote %s: %w", item.SKU, ErrUnknownSKU)
		}
		if price > (maxMoney-total)/Money(item.Quantity) {
			return 0, ErrInvalidOrder
		}
		total += price * Money(item.Quantity)
	}
	return total, nil
}
