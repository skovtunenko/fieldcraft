# Tags in a notes service with schema migrations

Case ID: `notes-tags-resources-01`. It runs the "Composition root and
resources" case of `../cases.md`.

Copy `../fixtures/notes/` into a new run directory before each session, as
`cancel-order.md` describes. Keep this scenario outside the executor's context.

## First user turn

Run the case once in each language: English, Russian, and Ukrainian, as
`cancel-order.md` describes. The English request:

```text
go contract mode. Notes need tags. A tag is stored in the database. A note can
get tags, and an HTTP endpoint must return the notes that have a given tag.
Every existing note must get the tag "untagged". Let's agree on the contract
and put it into the project.
```

The same request in Russian:

```text
go contract mode. Нужно добавить теги к заметкам. Тег хранится в базе данных.
Заметке можно назначить теги, и нужен HTTP-эндпоинт, который возвращает
заметки по тегу. Все существующие заметки должны получить тег «untagged».
Давай согласуем контракт и внесём его в проект.
```

The same request in Ukrainian:

```text
go contract mode. Потрібно додати теги до нотаток. Тег зберігається в базі
даних. Нотатці можна призначити теги, і потрібен HTTP-ендпоінт, який повертає
нотатки за тегом. Усі наявні нотатки мають отримати тег «untagged». Давай
узгодимо контракт і внесемо його в проєкт.
```

## User decisions for later rounds

Accept each recommendation with "yes" (Russian "да", Ukrainian "так"). Stop after the facade contract map; the
internals phase is not part of this case.

## Expected observations

1. The first reply writes no file and asks the storage form, with the new
   migration file, as a facade decision.
2. The new migration file holds the schema statements in full. The backfill of
   the tag `untagged` is an intent comment; the file changes no data.
3. `NewHandler` registers the new routes. Each new handler body writes status
   501. The server builds and starts.
4. The file tree of the contract map shows the migration file.
5. An existing body whose behavior changes becomes a stub only after the user
   agreed to the tests that become pending.

In this fixture `NewHandler` registers the routes, so `cmd/server/main.go`
does not change. The case does not check a change to `main`.
