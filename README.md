# Anime Corner

A small, anime-themed web app running on Docker. nginx serves the static front end and acts as a reverse proxy to a tiny Python API. Two linked content types — **quotes** and **characters** — are stored in a SQLite database that persists in a Docker volume; on first run each table seeds itself from a JSON file. When adding a quote you pick its character from a dropdown, so quotes reference real characters. Portainer provides a visual dashboard to manage the containers. Built step by step, adding tools slowly.

## Stack

| Service     | Tech | Purpose |
|-------------|------|---------|
| `web`       | nginx (alpine) | Serves the static front end and proxies `/api/` to the API |
| `api`       | Python 3.12 (stdlib only, incl. sqlite3) | CRUD API for quotes and characters backed by SQLite |
| `portainer` | Portainer CE | Web GUI to view and manage the containers |

Everything is open-source and orchestrated with Docker Compose.

## Project Structure

```
anime-app/
├── Dockerfile            # builds the web (nginx) image
├── docker-compose.yml    # defines web + api + portainer services
├── nginx.conf            # nginx: serves front end + reverse proxy to api
├── index.html            # page structure (quotes + characters sections)
├── style.css             # page styling
└── api/
    ├── Dockerfile        # builds the API image
    ├── app.py            # API (Python stdlib + SQLite)
    ├── quotes.json       # quote seed data, loaded once into the database
    └── characters.json   # character seed data, loaded once into the database
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
| All characters (via proxy) | http://localhost:8080/api/characters |
| Portainer dashboard | http://localhost:9000 |

The web page lets you:
- See a random quote and fetch a new one with **New Quote**
- Add a quote (selecting its character from a dropdown), search/filter quotes, and delete a quote with the **×** button
- Add and delete characters (name + anime) in the **Characters** section

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

## Content Types & Relationship

The app manages two data types, each with its own table, routes, and UI section, following the same pattern.

- **Characters** — fields: `id`, `name`, `anime`. Seeded from `characters.json`.
- **Quotes** — fields: `id`, `text`, `char`, `character_id`. Seeded from `quotes.json`.

The two are linked: a quote stores a `character_id` pointing to a character. In the UI, the **Add a Quote** form uses a dropdown populated from the characters table, so quotes can only be attached to characters that actually exist. The `char` text field is kept alongside `character_id` for simple display.

## Search / Filter (quotes)

Search is handled entirely on the front end. The full quote list is fetched once into a JavaScript array; typing in the search box filters that array by quote text or character name (case-insensitive) and re-renders the list. No API call per keystroke; deleting works on filtered results too, since each item carries its database `id`.

## Database & Persistence

Data is stored in a SQLite database at `/data/quotes.db` inside the API container, backed by the named Docker volume `quotes_data`, so it survives container restarts, recreation, and rebuilds:

```yaml
volumes:
  - quotes_data:/data
```

On startup the API runs `init_db()`, which creates the `quotes` and `characters` tables if needed and, for each one only when empty, seeds it from the matching JSON file (baked into the image). After the first seed, the database is the source of truth and the JSON files are no longer read.

> **Note on schema changes:** `CREATE TABLE IF NOT EXISTS` does not modify an existing table. When a column is added (such as `character_id` on quotes), an existing database must be wiped and re-seeded for the new column to take effect.

Check that seeding ran:

```bash
docker compose logs api
# look for: Seeded N quotes from quotes.json
#           Seeded N characters from characters.json
```

Inspect the database directly:

```bash
docker compose exec api sh
python -c "import sqlite3; c=sqlite3.connect('/data/quotes.db'); print(c.execute('SELECT * FROM quotes').fetchall()); print(c.execute('SELECT * FROM characters').fetchall())"
exit
```

To start completely fresh (wipe everything and re-seed) — also required after a schema change:

```bash
docker compose down
docker volume rm anime-app_quotes_data   # volume name = <project>_quotes_data
docker compose up -d --build
```

## API

Each resource is a small CRUD interface.

### Quotes

- `GET /api/quote` — one random quote: `{ "text": ..., "char": ... }`
- `GET /api/quotes` — full list, each item includes `id`, `text`, `char`, `character_id`
- `POST /api/quotes` — add a quote; JSON body `{ "text": ..., "char": ..., "character_id": ... }`; `text` and `char` required, `character_id` optional; returns `201` (or `400` if missing)
- `DELETE /api/quotes/{id}` — delete a quote; returns `{"deleted": <id>}`

### Characters

- `GET /api/characters` — full list, each item includes `id`, `name`, `anime`
- `POST /api/characters` — add a character; JSON body `{ "name": ..., "anime": ... }`; both required; returns `201` (or `400` if missing)
- `DELETE /api/characters/{id}` — delete a character; returns `{"deleted": <id>}`

On errors the API returns HTTP 500 with a JSON `{"error": ...}` message.

## Verifying in the Browser (GUI)

No curl needed — everything is checkable on the page at http://localhost:8080:

1. **Read:** the random quote card, the quote list, and the characters list all populate on load.
2. **New random:** click **New Quote** — the top card changes.
3. **Dropdown link:** in the **Add a Quote** form, the character field is a dropdown populated from the characters table; adding a character makes it appear there automatically.
4. **Create quote:** select a character, type a quote, click **Add** — "Added!" appears and it shows in the list, stored with its `character_id`.
5. **Search:** type in the search box — the quote list narrows as you type; clearing restores it; a no-match term shows "No matches found."
6. **Create character:** in the **Characters** section, add a name + anime and click **Add Character** — it appears immediately and in the quote dropdown.
7. **Persistence:** press **F5** — added quotes and characters are still there.
8. **Delete:** click the **×** on any quote or character — it disappears, and stays gone after a refresh.

Confirm the link is stored via **DevTools (F12) → Network**: a `quotes` response now includes a `character_id` field. You can also watch requests live in **Portainer** → **Containers** → `anime-api` → **Logs**.

## Common Commands

```bash
docker compose up -d --build   # start (rebuild after changes)
docker compose down            # stop and remove containers
docker compose ps              # list running services
docker compose logs -f         # follow logs
docker compose restart         # restart all services
docker compose restart web     # restart a single service
```

Editing `index.html`, `style.css`, `nginx.conf`, or `api/app.py` requires `docker compose up -d --build`. Editing the seed JSON files only affects fresh (empty) tables. A schema change requires wiping the `quotes_data` volume.

## Notes

- The API uses only the Python standard library, including the built-in `sqlite3` module — no external dependencies.
- The front end is split into `index.html` (structure) and `style.css` (styling); both are copied into the nginx image.
- Quotes reference characters via `character_id`; the Add-a-Quote dropdown enforces selecting an existing character.
- Search/filter runs entirely in the browser against the already-loaded quote list.
- The API is exposed to other containers (`expose`) but not published to the host, so it is only reachable through the nginx proxy.
- Seed JSON files are baked into the API image and load into the database only on first run when the relevant table is empty.
- The database lives in the named volume `quotes_data` and persists independently of the container.
- Portainer settings persist in the named volume `portainer_data`.
- Portainer needs access to the Docker socket (`/var/run/docker.sock`) to manage containers.
