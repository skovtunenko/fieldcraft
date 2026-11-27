package main

import (
	"context"
	"fmt"
	"log"

	shop "example.com/contractshop"
)

func main() {
	catalog, err := shop.NewCatalog(map[shop.SKU]shop.Money{"book": 1200})
	if err != nil {
		log.Fatal(err)
	}
	inventory, err := shop.NewMemoryInventory(map[shop.SKU]int{"book": 5})
	if err != nil {
		log.Fatal(err)
	}
	payments, err := shop.NewMemoryGateway(10000)
	if err != nil {
		log.Fatal(err)
	}
	orders := shop.NewMemoryOrders()
	checkout := shop.NewCheckout(catalog, inventory, payments, orders)
	order, err := checkout.Place(context.Background(), shop.PlaceRequest{ID: "demo-order", Items: []shop.Item{{SKU: "book", Quantity: 2}}})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("order=%s status=%s total_cents=%d stock=%d balance_cents=%d\n", order.ID, order.Status, order.Total, inventory.Available("book"), payments.Balance())
}
