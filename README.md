# Anime Corner

A small, anime-themed web app running on Docker. nginx serves a static page and acts as a reverse proxy to a tiny Python API that returns random anime quotes. Quotes live in an editable JSON file mounted into the API container, so content can change without rebuilding. Portainer provides a visual dashboard to manage the containers. Built step by step, adding tools slowly.

## Stack

| Service     | Tech | Purpose |
|-------------|------|---------|
| `web`       | nginx (alpine) | Serves the static page and proxies `/api/` to the API |
| `api`       | Python 3.12 (stdlib only) | Returns random anime quotes as JSON |
| `portainer` | Portainer CE | Web GUI to view and manage the containers |

Everything is open-source and orchestrated with Docker Compose.

## Project Structure

```
anime-app/
├── Dockerfile            # builds the web (nginx) image
├── docker-compose.yml    # defines web + api + portainer services
├── nginx.conf            # nginx: serves page + reverse proxy to api
├── index.html            # the anime-themed page
└── api/
    ├── Dockerfile        # builds the API image
    ├── app.py            # quote API (Python stdlib HTTP server)
    └── quotes.json       # editable quote data (mounted into the container)
```

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
| Quote API (via proxy) | http://localhost:8080/api/quote |
| Portainer dashboard | http://localhost:9000 |

Open the web page and click **New Quote** to fetch a fresh quote. The API is **not** exposed directly to the host — it is only reachable internally through the nginx proxy.

### Portainer first-time setup

1. Open http://localhost:9000
2. Create an admin username and password (do this promptly; if setup locks, run `docker compose restart portainer` and retry)
3. Choose the local Docker environment

## How the Reverse Proxy Works

The browser only ever talks to nginx on port 8080. nginx serves the static page at `/` and forwards any `/api/` request to the API container internally:

```nginx
location /api/ {
    proxy_pass http://api:5000/;
}
```

Inside Docker Compose, containers reach each other by service name, so `api` resolves to the API container. The trailing `/` strips the `/api/` prefix, so `/api/quote` reaches the API's `/quote`. This removes the need for CORS and keeps a single public entry point.

## Editing Quotes (no rebuild)

Quotes are stored in `api/quotes.json` and mounted into the container as read-only at `/data/quotes.json`:

```yaml
volumes:
  - ./api/quotes.json:/data/quotes.json:ro
```

The API reads the file on every request, so adding or changing a quote takes effect immediately — no rebuild and no restart. Just edit the file:

```bash
nano api/quotes.json
```

```json
[
  { "text": "A lesson without pain is meaningless.", "char": "Edward Elric" },
  { "text": "If you don't take risks, you can't create a future.", "char": "Monkey D. Luffy" }
]
```

Save, then `curl http://localhost:8080/api/quote` a few times to see the new entry in rotation.

## API

### `GET /api/quote`

Returns a random anime quote (through the nginx proxy).

**Example**

```bash
curl http://localhost:8080/api/quote
```

**Response**

```json
{
  "text": "A lesson without pain is meaningless.",
  "char": "Edward Elric"
}
```

If the data file is missing or invalid, the API returns HTTP 500 with `{"error": "could not load quotes"}`.

## Verifying nginx (GUI)

- **Browser DevTools:** open http://localhost:8080, press F12, go to the **Network** tab, click **New Quote**, and inspect the `quote` request. The Request URL should be `http://localhost:8080/api/quote` with status `200`, and the response headers should include `Server: nginx`.
- **Portainer:** open http://localhost:9000 → **Containers** → `anime-app` → **Logs** to watch nginx handle requests live.

## Common Commands

```bash
docker compose up -d --build   # start (rebuild after changes)
docker compose down            # stop and remove containers
docker compose ps              # list running services
docker compose logs -f         # follow logs
docker compose restart         # restart all services
docker compose restart web     # restart a single service
```

Editing `api/quotes.json` needs no rebuild. Editing `index.html`, `nginx.conf`, or `api/app.py` requires `docker compose up -d --build`.

## Notes

- The API uses only the Python standard library — no external dependencies.
- The API is exposed to other containers (`expose`) but not published to the host, so it is only reachable through the nginx proxy.
- The quotes file is mounted read-only (`:ro`); the API can read it but not modify it.
- The API reads the data file on each request, so content edits apply live.
- Portainer settings persist in the named volume `portainer_data`.
- Portainer needs access to the Docker socket (`/var/run/docker.sock`) to manage containers.
