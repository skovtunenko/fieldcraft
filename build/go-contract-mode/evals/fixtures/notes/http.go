package notes

import (
	"encoding/json"
	"errors"
	"net/http"
	"strconv"
)

// NewHandler returns the HTTP API of the service. Register every route here.
func NewHandler(service *Service) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("POST /notes", func(w http.ResponseWriter, r *http.Request) {
		var request struct {
			Title string `json:"title"`
			Body  string `json:"body"`
		}
		if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
			http.Error(w, "invalid JSON", http.StatusBadRequest)
			return
		}
		note, err := service.Create(r.Context(), request.Title, request.Body)
		writeNote(w, http.StatusCreated, note, err)
	})
	mux.HandleFunc("GET /notes/{id}", func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.ParseInt(r.PathValue("id"), 10, 64)
		if err != nil {
			http.Error(w, "invalid id", http.StatusBadRequest)
			return
		}
		note, err := service.Get(r.Context(), NoteID(id))
		writeNote(w, http.StatusOK, note, err)
	})
	return mux
}

func writeNote(w http.ResponseWriter, status int, note Note, err error) {
	switch {
	case errors.Is(err, ErrEmptyTitle):
		http.Error(w, err.Error(), http.StatusBadRequest)
	case errors.Is(err, ErrNoteNotFound):
		http.Error(w, err.Error(), http.StatusNotFound)
	case err != nil:
		http.Error(w, "internal error", http.StatusInternalServerError)
	default:
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(status)
		json.NewEncoder(w).Encode(note)
	}
}
