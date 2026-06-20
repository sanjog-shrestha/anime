# Anime Corner

A small, anime-themed web app running on Docker. nginx serves the static front end and acts as a reverse proxy to a tiny Python API. Quotes are stored in a SQLite database that persists in a Docker volume; on first run the database seeds itself from `quotes.json`. The page shows a random quote, the full list, and a form to add new quotes. Portainer provides a visual dashboard to manage and inspect the containers. Built step by step, adding tools slowly.

## Stack

| Service     | Tech | Purpose |
|-------------|------|---------|
| `web`       | nginx (alpine) | Serves the static front end and proxies `/api/` to the API |
| `api`       | Python 3.12 (stdlib only, incl. sqlite3) | Reads and writes anime quotes in a SQLite database |
| `portainer` | Portainer CE | Web GUI to view, inspect, and manage the containers |

Everything is open-source and orchestrated with Docker Compose.

## Project Structure

```
anime-app/
├── Dockerfile            # builds the web (nginx) image
├── docker-compose.yml    # defines web + api + portainer services
├── nginx.conf            # nginx: serves front end + reverse proxy to api
├── index.html            # page structure (random quote + add form + full list)
├── style.css             # page styling
└── api/
    ├── Dockerfile        # builds the API image
    ├── app.py            # quote API (Python stdlib + SQLite, GET + POST)
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

Open the web page to see a random quote card, an **Add a Quote** form, and the full list of quotes. The API is **not** exposed directly to the host — it is only reachable internally through the nginx proxy.

### Portainer first-time setup

1. Open http://localhost:9000
2. Create an admin username and password (do this promptly; if setup locks, run `docker compose restart portainer` and retry)
3. Choose the local Docker environment

## How the Reverse Proxy Works

The browser only ever talks to nginx on port 8080. nginx serves the static files at `/` and forwards any `/api/` request to the API container internally (all HTTP methods, including POST):

```nginx
location /api/ {
    proxy_pass http://api:5000/;
}
```

Inside Docker Compose, containers reach each other by service name, so `api` resolves to the API container. The trailing `/` strips the `/api/` prefix, so `/api/quotes` reaches the API's `/quotes`. This removes the need for CORS and keeps a single public entry point.

## Database & Persistence

Quotes are stored in a SQLite database at `/data/quotes.db` inside the API container, backed by the named volume `quotes_data`, so data survives restarts, recreation, and rebuilds:

```yaml
volumes:
  - quotes_data:/data
```

On startup the API runs `init_db()`, which creates the `quotes` table if needed and, only when the table is empty, seeds it from `quotes.json` (baked into the image). After the first seed, the database is the source of truth.

To start completely fresh (wipe all quotes and re-seed):

```bash
docker compose down
docker volume rm anime-app_quotes_data   # volume name = <project>_quotes_data
docker compose up -d --build
```

## API

### `GET /api/quote`

Returns a single random anime quote.

```json
{ "text": "A lesson without pain is meaningless.", "char": "Edward Elric" }
```

### `GET /api/quotes`

Returns the full list of quotes.

```json
[
  { "text": "A lesson without pain is meaningless.", "char": "Edward Elric" },
  { "text": "If you don't take risks, you can't create a future.", "char": "Monkey D. Luffy" }
]
```

### `POST /api/quotes`

Adds a new quote. Body must be JSON with non-empty `text` and `char`.

Request body:

```json
{ "text": "Whatever you lose, you'll find it again.", "char": "Kenshin Himura" }
```

Responses:

- `201 Created` — returns the saved quote
- `400 Bad Request` — `{"error": "text and char are required"}` if a field is empty
- `500` — `{"error": "could not add quote"}` on failure

## Verifying in the GUI

All verification can be done in the browser and Portainer — no command line needed.

### Add a quote through the page

1. Open http://localhost:8080
2. In the **Add a Quote** card, enter a quote and character name
3. Click **Add** — you should see "Quote added!" and the new entry appears at the bottom of the **All Quotes** list

### Confirm the request via DevTools

1. Press **F12** → **Network** tab
2. Click **Add** with a new quote
3. Select the `quotes` request and check:
   - Request Method: `POST`
   - Request URL: `http://localhost:8080/api/quotes`
   - Status: `201 Created`
   - Payload / Response tabs show the sent and saved data
   - Response headers include `Server: nginx` (confirming the proxy)

### Confirm it saved to the database (Portainer)

1. Open http://localhost:9000 → **Containers** → **anime-api** → **Console**
2. Command `/bin/sh` → **Connect**
3. Run:
   ```
   python -c "import sqlite3; [print(r) for r in sqlite3.connect('/data/quotes.db').execute('SELECT * FROM quotes')]"
   ```
4. The list includes your newly added quotes — straight from SQLite

### Prove persistence (Portainer)

1. In Portainer → **Containers**, select **anime-api** → **Recreate**
2. Reload http://localhost:8080 — your added quotes are still there, because they live in the `quotes_data` volume

## Common Commands

```bash
docker compose up -d --build   # start (rebuild after changes)
docker compose down            # stop and remove containers
docker compose ps              # list running services
docker compose logs -f         # follow logs
docker compose restart         # restart all services
docker compose restart web     # restart a single service
```

Editing `index.html`, `style.css`, `nginx.conf`, or `api/app.py` requires `docker compose up -d --build`.

## Notes

- The API uses only the Python standard library, including the built-in `sqlite3` module — no external dependencies.
- The app supports Create and Read; Update and Delete are natural follow-on routes.
- The front end is split into `index.html` (structure) and `style.css` (styling); both are copied into the nginx image.
- The API is exposed to other containers (`expose`) but not published to the host, so it is only reachable through the nginx proxy.
- `quotes.json` is seed data baked into the API image; it loads into the database only on first run when the table is empty.
- The database lives in the named volume `quotes_data` and persists independently of the container.
- Portainer settings persist in the named volume `portainer_data`.
- Portainer needs access to the Docker socket (`/var/run/docker.sock`) to manage containers.
