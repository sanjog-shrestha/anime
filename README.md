# Anime Corner

A small, anime-themed web app running on Docker. It serves a static page (nginx) backed by a tiny Python API that returns random anime quotes. Built step by step, adding tools slowly.

## Stack

| Service | Tech | Purpose |
|---------|------|---------|
| `web`   | nginx (alpine) | Serves the static page |
| `api`   | Python 3.12 (stdlib only) | Returns random anime quotes as JSON |

Everything is open-source and orchestrated with Docker Compose.

## Project Structure

```
anime-app/
├── Dockerfile            # builds the web (nginx) image
├── docker-compose.yml    # defines web + api services
├── index.html            # the anime-themed page
└── api/
    ├── Dockerfile        # builds the API image
    └── app.py            # quote API (Python stdlib HTTP server)
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
| Quote API | http://localhost:5000/quote |

Open the web page and click **New Quote** to fetch a fresh quote.

## API

### `GET /quote`

Returns a random anime quote.

**Example**

```bash
curl http://localhost:5000/quote
```

**Response**

```json
{
  "text": "A lesson without pain is meaningless.",
  "char": "Edward Elric"
}
```

## Common Commands

```bash
docker compose up -d --build   # start (rebuild after changes)
docker compose down            # stop and remove containers
docker compose ps              # list running services
docker compose logs -f         # follow logs
docker compose restart         # restart all services
docker compose restart web     # restart a single service
```

After editing `index.html` or `api/app.py`, re-run `docker compose up -d --build` to apply changes.

## Notes

- The API uses only the Python standard library — no external dependencies.
- CORS is currently handled with an `Access-Control-Allow-Origin: *` header on the API. This will be replaced by an nginx reverse proxy in a later step.
