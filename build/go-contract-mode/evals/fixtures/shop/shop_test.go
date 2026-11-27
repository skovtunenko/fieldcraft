package shop_test

import (
	"context"
	"errors"
	"sync"
	"testing"

	shop "example.com/contractshop"
)

type fixture struct {
	catalog   *shop.Catalog
	inventory *shop.MemoryInventory
	payments  *shop.MemoryGateway
	orders    *shop.MemoryOrders
	checkout  *shop.Checkout
}

func newFixture(t *testing.T, balance shop.Money) fixture {
	t.Helper()
	catalog, err := shop.NewCatalog(map[shop.SKU]shop.Money{"book": 1200, "pen": 200})
	if err != nil {
		t.Fatal(err)
	}
	inventory, err := shop.NewMemoryInventory(map[shop.SKU]int{"book": 4, "pen": 10})
	if err != nil {
		t.Fatal(err)
	}
	payments, err := shop.NewMemoryGateway(balance)
	if err != nil {
		t.Fatal(err)
	}
	orders := shop.NewMemoryOrders()
	return fixture{catalog, inventory, payments, orders, shop.NewCheckout(catalog, inventory, payments, orders)}
}

func request(id shop.OrderID) shop.PlaceRequest {
	return shop.PlaceRequest{ID: id, Items: []shop.Item{{SKU: "book", Quantity: 1}}}
}

func TestPlacePersistsQuotedOrderAndItsReferences(t *testing.T) {
	f := newFixture(t, 10000)
	req := shop.PlaceRequest{ID: "order-1", Items: []shop.Item{
		{SKU: "book", Quantity: 1}, {SKU: "pen", Quantity: 2}, {SKU: "book", Quantity: 1},
	}}
	order, err := f.checkout.Place(context.Background(), req)
	if err != nil {
		t.Fatal(err)
	}
	if order.Total != 2800 || order.Status != shop.OrderPaid || order.PaymentID == "" || order.ReservationID == "" {
		t.Fatalf("incomplete paid order: %+v", order)
	}
	if f.inventory.Available("book") != 2 || f.inventory.Available("pen") != 8 || f.payments.Balance() != 7200 {
		t.Fatal("stock or payment did not match the quoted order")
	}
	// Neither the caller nor a returned snapshot can change a saved order.
	req.Items[0].Quantity = 99
	order.Items[1].Quantity = 99
	saved, err := f.orders.Get(context.Background(), "order-1")
	if err != nil || saved.Items[0].Quantity != 1 || saved.Items[1].Quantity != 2 {
		t.Fatalf("saved order shares mutable input: %+v, %v", saved, err)
	}
	saved.Items[0].Quantity = 77
	again, err := f.orders.Get(context.Background(), "order-1")
	if err != nil || again.Items[0].Quantity != 1 {
		t.Fatal("Get returned mutable storage")
	}
}

func TestRejectedOrdersLeaveStockAndBalanceUntouched(t *testing.T) {
	cases := []struct {
		name string
		req  shop.PlaceRequest
		want error
	}{
		{"missing ID", shop.PlaceRequest{Items: request("x").Items}, shop.ErrInvalidOrder},
		{"empty items", shop.PlaceRequest{ID: "x"}, shop.ErrInvalidOrder},
		{"zero quantity", shop.PlaceRequest{ID: "x", Items: []shop.Item{{SKU: "book", Quantity: 0}}}, shop.ErrInvalidOrder},
		{"negative quantity", shop.PlaceRequest{ID: "x", Items: []shop.Item{{SKU: "book", Quantity: -1}}}, shop.ErrInvalidOrder},
		{"unknown product", shop.PlaceRequest{ID: "x", Items: []shop.Item{{SKU: "missing", Quantity: 1}}}, shop.ErrUnknownSKU},
		{"no stock", shop.PlaceRequest{ID: "x", Items: []shop.Item{{SKU: "book", Quantity: 5}}}, shop.ErrOutOfStock},
		{"duplicate lines exceed stock", shop.PlaceRequest{ID: "x", Items: []shop.Item{{SKU: "book", Quantity: 3}, {SKU: "book", Quantity: 2}}}, shop.ErrOutOfStock},
		{"later product has no stock", shop.PlaceRequest{ID: "x", Items: []shop.Item{{SKU: "pen", Quantity: 1}, {SKU: "book", Quantity: 5}}}, shop.ErrOutOfStock},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			f := newFixture(t, 10000)
			_, err := f.checkout.Place(context.Background(), tc.req)
			if !errors.Is(err, tc.want) {
				t.Fatalf("got %v, want %v", err, tc.want)
			}
			if f.inventory.Available("book") != 4 || f.inventory.Available("pen") != 10 || f.payments.Balance() != 10000 {
				t.Fatal("rejected order changed stock or balance")
			}
			if _, err := f.orders.Get(context.Background(), tc.req.ID); !errors.Is(err, shop.ErrOrderNotFound) {
				t.Fatalf("rejected order was saved: %v", err)
			}
		})
	}
}

func TestDeclinedPaymentReleasesStock(t *testing.T) {
	f := newFixture(t, 100)
	_, err := f.checkout.Place(context.Background(), request("declined"))
	if !errors.Is(err, shop.ErrPaymentDeclined) || f.inventory.Available("book") != 4 || f.payments.Balance() != 100 {
		t.Fatalf("declined order did not restore state: %v", err)
	}
	if _, err := f.orders.Get(context.Background(), "declined"); !errors.Is(err, shop.ErrOrderNotFound) {
		t.Fatal("declined order was saved")
	}
}

type failingSave struct {
	shop.Orders
	err    error
	cancel context.CancelFunc
}

func (s failingSave) Save(context.Context, shop.Order) error {
	if s.cancel != nil {
		s.cancel()
	}
	return s.err
}

func TestSaveFailureRefundsAndReleasesEvenWhenCallerCancels(t *testing.T) {
	for _, cancelCaller := range []bool{false, true} {
		t.Run(map[bool]string{false: "live caller", true: "cancelled caller"}[cancelCaller], func(t *testing.T) {
			f := newFixture(t, 10000)
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			saveErr := errors.New("storage unavailable")
			store := failingSave{Orders: f.orders, err: saveErr}
			if cancelCaller {
				store.cancel = cancel
			}
			checkout := shop.NewCheckout(f.catalog, f.inventory, f.payments, store)
			_, err := checkout.Place(ctx, request("failed-save"))
			if !errors.Is(err, saveErr) || f.payments.Balance() != 10000 || f.inventory.Available("book") != 4 {
				t.Fatalf("failed save did not compensate: %v", err)
			}
			if _, err := f.payments.Charge(context.Background(), "failed-save", 1200); !errors.Is(err, shop.ErrPaymentRefunded) {
				t.Fatalf("payment was not charged and refunded: %v", err)
			}
			if _, err := f.orders.Get(context.Background(), "failed-save"); !errors.Is(err, shop.ErrOrderNotFound) {
				t.Fatal("failed save left an order")
			}
		})
	}
}

type failingRefund struct {
	shop.Payments
	err error
}

func (p failingRefund) Refund(context.Context, shop.PaymentID) error { return p.err }

type failingRelease struct {
	shop.Inventory
	err error
}

func (i failingRelease) Release(context.Context, shop.ReservationID) error { return i.err }

func TestAllCompensationsRunAndTheirErrorsRemainVisible(t *testing.T) {
	f := newFixture(t, 10000)
	saveErr, refundErr, releaseErr := errors.New("save"), errors.New("refund"), errors.New("release")
	checkout := shop.NewCheckout(f.catalog, failingRelease{f.inventory, releaseErr}, failingRefund{f.payments, refundErr}, failingSave{Orders: f.orders, err: saveErr})
	_, err := checkout.Place(context.Background(), request("cleanup-failed"))
	for _, want := range []error{saveErr, refundErr, releaseErr} {
		if !errors.Is(err, want) {
			t.Fatalf("lost failure %v in %v", want, err)
		}
	}
	if f.payments.Balance() != 8800 || f.inventory.Available("book") != 3 {
		t.Fatal("failed compensation state was hidden")
	}
}

func TestConcurrentDuplicateRequestIsRejectedWithoutExtraEffects(t *testing.T) {
	f := newFixture(t, 10000)
	results := make(chan error, 12)
	var wg sync.WaitGroup
	for range 12 {
		wg.Add(1)
		go func() {
			defer wg.Done()
			_, err := f.checkout.Place(context.Background(), request("same-order"))
			results <- err
		}()
	}
	wg.Wait()
	close(results)
	successes := 0
	for err := range results {
		if err == nil {
			successes++
		} else if !errors.Is(err, shop.ErrOrderExists) {
			t.Fatal(err)
		}
	}
	if successes != 1 || f.inventory.Available("book") != 3 || f.payments.Balance() != 8800 {
		t.Fatalf("duplicate placement had extra effects; successes=%d", successes)
	}
}

func TestCancelledRequestHasNoEffects(t *testing.T) {
	f := newFixture(t, 10000)
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	_, err := f.checkout.Place(ctx, request("cancelled"))
	if !errors.Is(err, context.Canceled) || f.inventory.Available("book") != 4 || f.payments.Balance() != 10000 {
		t.Fatalf("cancelled request changed state: %v", err)
	}
}

func TestCatalogCopiesPricesAndRejectsOverflow(t *testing.T) {
	prices := map[shop.SKU]shop.Money{"book": 1200}
	catalog, err := shop.NewCatalog(prices)
	if err != nil {
		t.Fatal(err)
	}
	prices["book"] = 1
	if total, err := catalog.Quote(request("x").Items); err != nil || total != 1200 {
		t.Fatalf("catalog did not own its prices: %d, %v", total, err)
	}
	large, err := shop.NewCatalog(map[shop.SKU]shop.Money{"expensive": 1<<62 - 1})
	if err != nil {
		t.Fatal(err)
	}
	if _, err := large.Quote([]shop.Item{{SKU: "expensive", Quantity: 3}}); !errors.Is(err, shop.ErrInvalidOrder) {
		t.Fatalf("price overflow was accepted: %v", err)
	}
	accumulated, err := shop.NewCatalog(map[shop.SKU]shop.Money{"expensive": 1 << 62})
	if err != nil {
		t.Fatal(err)
	}
	if _, err := accumulated.Quote([]shop.Item{{SKU: "expensive", Quantity: 1}, {SKU: "expensive", Quantity: 1}}); !errors.Is(err, shop.ErrInvalidOrder) {
		t.Fatalf("accumulated price overflow was accepted: %v", err)
	}
}

func TestReservationReleaseAndPaymentRefundAreIdempotent(t *testing.T) {
	f := newFixture(t, 10000)
	ctx := context.Background()
	reservation, err := f.inventory.Reserve(ctx, request("x").Items)
	if err != nil {
		t.Fatal(err)
	}
	payment, err := f.payments.Charge(ctx, "x", 1200)
	if err != nil {
		t.Fatal(err)
	}
	if again, err := f.payments.Charge(ctx, "x", 1200); err != nil || again != payment || f.payments.Balance() != 8800 {
		t.Fatal("repeated charge was not idempotent")
	}
	if _, err := f.payments.Charge(ctx, "x", 1300); !errors.Is(err, shop.ErrPaymentConflict) {
		t.Fatal("different amount reused a payment key")
	}
	for range 2 {
		if err := f.inventory.Release(ctx, reservation); err != nil {
			t.Fatal(err)
		}
		if err := f.payments.Refund(ctx, payment); err != nil {
			t.Fatal(err)
		}
	}
	if f.inventory.Available("book") != 4 || f.payments.Balance() != 10000 {
		t.Fatal("repeated compensation created stock or money")
	}
	if _, err := f.payments.Charge(ctx, "x", 1200); !errors.Is(err, shop.ErrPaymentRefunded) {
		t.Fatal("refunded payment key was charged again")
	}
}
