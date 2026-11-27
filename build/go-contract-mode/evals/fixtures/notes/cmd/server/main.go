package main

import (
	"flag"
	"log"
	"net/http"

	notes "example.com/contractnotes"
)

func main() {
	addr := flag.String("addr", "127.0.0.1:8080", "listen address")
	flag.Parse()

	// The local server uses the memory store. A deployment registers its SQL
	// driver, opens the database, runs notes.Migrate, and passes
	// notes.NewSQLStore(db) here.
	store := notes.NewMemoryStore()
	service := notes.NewService(store)

	log.Printf("notes server listens on %s", *addr)
	log.Fatal(http.ListenAndServe(*addr, notes.NewHandler(service)))
}
