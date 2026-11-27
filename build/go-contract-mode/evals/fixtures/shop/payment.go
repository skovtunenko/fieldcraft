package shop

import (
	"context"
	"errors"
	"strconv"
	"sync"
)

var (
	ErrPaymentDeclined = errors.New("payment declined")
	ErrPaymentConflict = errors.New("payment key reused with another amount")
	ErrPaymentNotFound = errors.New("payment not found")
	ErrPaymentRefunded = errors.New("payment already refunded")
)

// PaymentID identifies one accepted charge.
type PaymentID string

type charge struct {
	id       PaymentID
	amount   Money
	refunded bool
}

// MemoryGateway simulates a single customer's funded payment account.
// It makes no network calls and stores charge and refund state in memory.
type MemoryGateway struct {
	mu      sync.Mutex
	balance Money
	charges map[OrderID]charge
	next    uint64
}

// NewMemoryGateway opens a local account with a non-negative balance in cents.
func NewMemoryGateway(balance Money) (*MemoryGateway, error) {
	if balance < 0 {
		return nil, ErrInvalidOrder
	}
	return &MemoryGateway{balance: balance, charges: make(map[OrderID]charge)}, nil
}

// Charge debits amount using orderID as the idempotency key.
// An identical retry returns the first payment. A different amount conflicts;
// a refunded key cannot be charged again. Insufficient funds decline the charge.
func (m *MemoryGateway) Charge(ctx context.Context, orderID OrderID, amount Money) (PaymentID, error) {
	if err := ctx.Err(); err != nil {
		return "", err
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	if orderID == "" || amount <= 0 {
		return "", ErrInvalidOrder
	}
	if previous, ok := m.charges[orderID]; ok {
		if previous.amount != amount {
			return "", ErrPaymentConflict
		}
		if previous.refunded {
			return "", ErrPaymentRefunded
		}
		return previous.id, nil
	}
	if amount > m.balance {
		return "", ErrPaymentDeclined
	}
	m.next++
	id := PaymentID("p-" + strconv.FormatUint(m.next, 10))
	m.balance -= amount
	m.charges[orderID] = charge{id: id, amount: amount}
	return id, nil
}

// Refund restores the full charge once. Repeated refunds are successful no-ops.
func (m *MemoryGateway) Refund(ctx context.Context, id PaymentID) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	for orderID, payment := range m.charges {
		if payment.id == id {
			if !payment.refunded {
				m.balance += payment.amount
				payment.refunded = true
				m.charges[orderID] = payment
			}
			return nil
		}
	}
	return ErrPaymentNotFound
}

// Balance returns the remaining account balance in cents.
func (m *MemoryGateway) Balance() Money {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.balance
}
