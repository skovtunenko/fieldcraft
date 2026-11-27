package notes

import (
	"context"
	"database/sql"
	"errors"
)

// SQLStore keeps notes in the notes table of migrations/.
type SQLStore struct {
	db *sql.DB
}

var _ Store = (*SQLStore)(nil)

func NewSQLStore(db *sql.DB) *SQLStore {
	return &SQLStore{db: db}
}

func (s *SQLStore) Insert(ctx context.Context, note Note) (NoteID, error) {
	result, err := s.db.ExecContext(ctx, `INSERT INTO notes (title, body) VALUES (?, ?)`, note.Title, note.Body)
	if err != nil {
		return 0, err
	}
	id, err := result.LastInsertId()
	return NoteID(id), err
}

func (s *SQLStore) Get(ctx context.Context, id NoteID) (Note, error) {
	note := Note{ID: id}
	err := s.db.QueryRowContext(ctx, `SELECT title, body FROM notes WHERE id = ?`, id).Scan(&note.Title, &note.Body)
	if errors.Is(err, sql.ErrNoRows) {
		return Note{}, ErrNoteNotFound
	}
	return note, err
}
