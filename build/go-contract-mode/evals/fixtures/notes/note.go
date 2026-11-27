package notes

import (
	"context"
	"errors"
	"strings"
)

var (
	ErrNoteNotFound = errors.New("note not found")
	ErrEmptyTitle   = errors.New("note title is empty")
)

// NoteID is assigned by the store.
type NoteID int64

// Note is one stored note.
type Note struct {
	ID    NoteID `json:"id"`
	Title string `json:"title"`
	Body  string `json:"body"`
}

// Store persists notes. SQLStore and MemoryStore implement it.
type Store interface {
	Insert(ctx context.Context, note Note) (NoteID, error)
	Get(ctx context.Context, id NoteID) (Note, error)
}

// Service holds the note rules.
type Service struct {
	store Store
}

func NewService(store Store) *Service {
	return &Service{store: store}
}

// Create stores a note. It returns ErrEmptyTitle for a blank title.
func (s *Service) Create(ctx context.Context, title, body string) (Note, error) {
	title = strings.TrimSpace(title)
	if title == "" {
		return Note{}, ErrEmptyTitle
	}
	note := Note{Title: title, Body: body}
	id, err := s.store.Insert(ctx, note)
	if err != nil {
		return Note{}, err
	}
	note.ID = id
	return note, nil
}

// Get returns a note, or ErrNoteNotFound.
func (s *Service) Get(ctx context.Context, id NoteID) (Note, error) {
	return s.store.Get(ctx, id)
}
