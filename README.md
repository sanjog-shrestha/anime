# Anime Corner

A small, anime-themed web app running on Docker. nginx serves the static front end and acts as a reverse proxy to a tiny Python API. Quotes are stored in a SQLite database that persists in a Docker volume; on first run the database seeds itself from `quotes.json`. Through the browser you can view a random quote, browse the full list, search/filter it, add new quotes, and delete existing ones. Portainer provides a visual dashboard to manage the containers. Built step by step, adding tools slowly.

## Stack

| Service     | Tech | Purpose |
|-------------|------|---------|
| `web`       | nginx (alpine) | Serves the static front end and proxies `/api/` to the API |
| `api`       | Python 3.12 (stdlib only, incl. sqlite3) | CRUD API for anime quotes backed by SQLite |
| `portainer` | Portainer CE | Web GUI to view and manage the containers |

Everything is open-source and orchestrated with Docker Compose.

## Project Structure

```
anime-app/
├── Dockerfile            # builds the web (nginx) image
├── docker-compose.yml    # defines web + api + portainer services
├── nginx.conf            # nginx: serves front end + reverse proxy to api
├── index.html            # page structure (random quote + add form + search + list)
├── style.css             # page styling
└── api/
    ├── Dockerfile        # builds the API image
    ├── app.py            # quote API (Python stdlib + SQLite)
    └── quotes.json       # seed data, loaded once into the database
```

The front end separates concerns: `index.html` holds structure, `style.css` holds styling.

## Requirements

- Docker
- Docker Compose (v2, `docker compose`)

## Getting Started

From the project root:

```bash
docker compose up -d --build
```

- `up` — create and start the containers
- `-d` — run in the background
- `--build` — rebuild images from the Dockerfiles

## Access

| Service | URL |
|---------|-----|
| Web page | http://localhost:8080 |
| Random quote (via proxy) | http://localhost:8080/api/quote |
| All quotes (via proxy) | http://localhost:8080/api/quotes |
| Portainer dashboard | http://localhost:9000 |

The web page lets you:
- See a random quote and fetch a new one with **New Quote**
- Add a quote with the **Add a Quote** form
- Search/filter the list by quote text or character name
- Delete a quote with the **×** button on each list item

The API is **not** exposed directly to the host — it is only reachable internally through the nginx proxy.

### Portainer first-time setup

1. Open http://localhost:9000
2. Create an admin username and password (do this promptly; if setup locks, run `docker compose restart portainer` and retry)
3. Choose the local Docker environment

## How the Reverse Proxy Works

The browser only ever talks to nginx on port 8080. nginx serves the static files at `/` and forwards any `/api/` request to the API container internally:

```nginx
location /api/ {
    proxy_pass http://api:5000/;
}
```

Inside Docker Compose, containers reach each other by service name, so `api` resolves to the API container. The trailing `/` strips the `/api/` prefix, so `/api/quote` reaches the API's `/quote`. This removes the need for CORS and keeps a single public entry point.

## Search / Filter

Search is handled entirely on the front end. The full list is fetched once into a JavaScript array (`allQuotes`); typing in the search box filters that array by quote text or character name (case-insensitive) and re-renders the list. Because nothing is re-fetched, filtering is instant and requires no API or database change. Deleting works on filtered results too, since each item carries its database `id`.

## Database & Persistence

Quotes are stored in a SQLite database at `/data/quotes.db` inside the API container. That path is backed by the named Docker volume `quotes_data`, so the data survives container restarts, recreation, and rebuilds:

```yaml
volumes:
  - quotes_data:/data
```

On startup the API runs `init_db()`, which creates the `quotes` table if needed and, only when the table is empty, seeds it from `quotes.json` (baked into the image). After the first seed, the database is the source of truth and `quotes.json` is no longer read.

Check that seeding ran:

```bash
docker compose logs api      # look for: Seeded N quotes from quotes.json
```

Inspect the database directly:

```bash
docker compose exec api sh
python -c "import sqlite3; print(sqlite3.connect('/data/quotes.db').execute('SELECT * FROM quotes').fetchall())"
exit
```

To start completely fresh (wipe all quotes and re-seed):

```bash
docker compose down
docker volume rm anime-app_quotes_data   # volume name = <project>_quotes_data
docker compose up -d --build
```

## API

The API is a small CRUD interface. Each quote has an `id`, `text`, and `char`.

### `GET /api/quote`

Returns a single random quote.

```json
{ "text": "A lesson without pain is meaningless.", "char": "Edward Elric" }
```

### `GET /api/quotes`

Returns the full list of quotes, each including its `id`.

```json
[
  { "id": 1, "text": "A lesson without pain is meaningless.", "char": "Edward Elric" },
  { "id": 2, "text": "If you don't take risks, you can't create a future.", "char": "Monkey D. Luffy" }
]
```

### `POST /api/quotes`

Adds a new quote. Body must be JSON with non-empty `text` and `char`.

```json
{ "text": "New quote here", "char": "Character Name" }
```

Returns `201` with the created quote. Returns `400` if either field is missing or empty.

### `DELETE /api/quotes/{id}`

Deletes the quote with the given id. Returns `200` with `{"deleted": <id>}`.

On errors the API returns HTTP 500 with a JSON `{"error": ...}` message.

## Verifying in the Browser (GUI)

No curl needed — everything is checkable on the page at http://localhost:8080:

1. **Read:** the random quote card and the **All Quotes** list both populate on load.
2. **New random:** click **New Quote** — the top card changes.
3. **Create:** fill the **Add a Quote** form and click **Add** — "Added!" appears and the quote shows up in the list immediately.
4. **Search:** type in the search box — the list narrows to matching quotes/characters as you type; clearing it restores the full list; a no-match term shows "No matches found."
5. **Persistence:** press **F5** to refresh — added quotes are still there, proving they were saved to the database.
6. **Delete:** click the **×** on any quote — it disappears, and stays gone after a refresh.

You can also watch requests live in **Portainer** → **Containers** → `anime-api` → **Logs** while you use the page. Use **DevTools (F12) → Network** to inspect status codes (`200`, `201`) and confirm `Server: nginx` on responses.

## Common Commands

```bash
docker compose up -d --build   # start (rebuild after changes)
docker compose down            # stop and remove containers
docker compose ps              # list running services
docker compose logs -f         # follow logs
docker compose restart         # restart all services
docker compose restart web     # restart a single service
```

Editing `index.html`, `style.css`, `nginx.conf`, or `api/app.py` requires `docker compose up -d --build`. Editing `api/quotes.json` only affects a fresh (empty) database, since it is seed data.

## Notes

- The API uses only the Python standard library, including the built-in `sqlite3` module — no external dependencies.
- The front end is split into `index.html` (structure) and `style.css` (styling); both are copied into the nginx image.
- Search/filter runs entirely in the browser against the already-loaded list — no API call per keystroke.
- The API is exposed to other containers (`expose`) but not published to the host, so it is only reachable through the nginx proxy.
- `quotes.json` is seed data baked into the API image; it loads into the database only on first run when the table is empty.
- The database lives in the named volume `quotes_data` and persists independently of the container.
- Portainer settings persist in the named volume `portainer_data`.
- Portainer needs access to the Docker socket (`/var/run/docker.sock`) to manage containers.
