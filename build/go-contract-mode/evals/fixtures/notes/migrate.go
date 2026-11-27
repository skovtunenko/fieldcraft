package notes

import (
	"context"
	"database/sql"
	"embed"
	"fmt"
	"io/fs"
)

//go:embed migrations/*.sql
var migrations embed.FS

// Migrate applies every file of migrations/ that the database has not
// recorded yet, in file-name order. Each file runs in its own transaction.
func Migrate(ctx context.Context, db *sql.DB) error {
	if _, err := db.ExecContext(ctx, `CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)`); err != nil {
		return err
	}
	names, err := fs.Glob(migrations, "migrations/*.sql") // Glob returns sorted names
	if err != nil {
		return err
	}
	for _, name := range names {
		var applied int
		if err := db.QueryRowContext(ctx, `SELECT COUNT(*) FROM schema_migrations WHERE name = ?`, name).Scan(&applied); err != nil {
			return err
		}
		if applied > 0 {
			continue
		}
		statements, err := migrations.ReadFile(name)
		if err != nil {
			return err
		}
		tx, err := db.BeginTx(ctx, nil)
		if err != nil {
			return err
		}
		if _, err := tx.ExecContext(ctx, string(statements)); err != nil {
			tx.Rollback()
			return fmt.Errorf("migration %s: %w", name, err)
		}
		if _, err := tx.ExecContext(ctx, `INSERT INTO schema_migrations (name) VALUES (?)`, name); err != nil {
			tx.Rollback()
			return err
		}
		if err := tx.Commit(); err != nil {
			return err
		}
	}
	return nil
}
