package notes

import (
	"context"
	"sync"
)

// MemoryStore keeps notes in memory. Tests and the local server use it.
type MemoryStore struct {
	mu    sync.Mutex
	next  NoteID
	notes map[NoteID]Note
}

var _ Store = (*MemoryStore)(nil)

func NewMemoryStore() *MemoryStore {
	return &MemoryStore{notes: make(map[NoteID]Note)}
}

func (m *MemoryStore) Insert(ctx context.Context, note Note) (NoteID, error) {
	if err := ctx.Err(); err != nil {
		return 0, err
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	m.next++
	note.ID = m.next
	m.notes[note.ID] = note
	return note.ID, nil
}

func (m *MemoryStore) Get(ctx context.Context, id NoteID) (Note, error) {
	if err := ctx.Err(); err != nil {
		return Note{}, err
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	note, ok := m.notes[id]
	if !ok {
		return Note{}, ErrNoteNotFound
	}
	return note, nil
}
