package notes

import (
	"context"
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestService_Create(t *testing.T) {
	tests := []struct {
		name      string
		title     string
		wantTitle string
		wantErr   error
	}{
		{name: "trims the title", title: "  plan  ", wantTitle: "plan"},
		{name: "blank title", title: "   ", wantErr: ErrEmptyTitle},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			service := NewService(NewMemoryStore())
			got, err := service.Create(context.Background(), tt.title, "body")
			if !errors.Is(err, tt.wantErr) {
				t.Fatalf("Create() error = %v, want %v", err, tt.wantErr)
			}
			if got.Title != tt.wantTitle {
				t.Errorf("Create() title = %q, want %q", got.Title, tt.wantTitle)
			}
		})
	}
}

func TestService_Get_NotFound(t *testing.T) {
	service := NewService(NewMemoryStore())
	if _, err := service.Get(context.Background(), 7); !errors.Is(err, ErrNoteNotFound) {
		t.Fatalf("Get() error = %v, want %v", err, ErrNoteNotFound)
	}
}

func TestHandler_CreateThenGet(t *testing.T) {
	handler := NewHandler(NewService(NewMemoryStore()))

	create := httptest.NewRecorder()
	handler.ServeHTTP(create, httptest.NewRequest(http.MethodPost, "/notes", strings.NewReader(`{"title":"plan","body":"b"}`)))
	if create.Code != http.StatusCreated {
		t.Fatalf("POST /notes status = %d, want %d", create.Code, http.StatusCreated)
	}

	get := httptest.NewRecorder()
	handler.ServeHTTP(get, httptest.NewRequest(http.MethodGet, "/notes/1", nil))
	if get.Code != http.StatusOK || !strings.Contains(get.Body.String(), `"title":"plan"`) {
		t.Fatalf("GET /notes/1 = %d %s", get.Code, get.Body.String())
	}

	missing := httptest.NewRecorder()
	handler.ServeHTTP(missing, httptest.NewRequest(http.MethodGet, "/notes/9", nil))
	if missing.Code != http.StatusNotFound {
		t.Fatalf("GET /notes/9 status = %d, want %d", missing.Code, http.StatusNotFound)
	}
}
