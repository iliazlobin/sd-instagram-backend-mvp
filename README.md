# Instagram MVP

[![Lint](https://github.com/iliazlobin/sd-instagram-backend-mvp/actions/workflows/lint.yml/badge.svg)](https://github.com/iliazlobin/sd-instagram-backend-mvp/actions/workflows/lint.yml)
[![CI](https://github.com/iliazlobin/sd-instagram-backend-mvp/actions/workflows/ci.yml/badge.svg)](https://github.com/iliazlobin/sd-instagram-backend-mvp/actions/workflows/ci.yml)
[![Functional](https://github.com/iliazlobin/sd-instagram-backend-mvp/actions/workflows/functional.yml/badge.svg)](https://github.com/iliazlobin/sd-instagram-backend-mvp/actions/workflows/functional.yml)

A minimal Instagram-style REST API backend for photo sharing, built with FastAPI and PostgreSQL.

Users create profiles, upload photos with hashtags, follow each other, browse a chronological feed, like posts, and search by hashtag. The MVP pushes every new post to all followers' feeds at write time (fan-out-on-write) and uses PostgreSQL's native GIN index for hashtag search.

## Quickstart

```bash
git clone <repo-url> instagram-mvp
cd instagram-mvp
cp .env.example .env
docker compose up -d
curl http://localhost:8010/healthz
# → {"status":"ok","db":"connected"}
```

Migrations run automatically on container start. The app listens on host port `8010` (override with `APP_PORT` in `.env`).

### Without Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL="postgresql+asyncpg://instagram:instagram@localhost:5432/instagram"
alembic upgrade head
uvicorn instagram.main:app --host 0.0.0.0 --port 8000
```

## API Reference

Base URL: `http://localhost:8000` (or `http://localhost:8010` with Docker Compose).

All timestamps are ISO 8601. User identity is passed via the `X-User-Id` header on endpoints that require it.

### Users

#### `POST /users` — Create user

```json
// Request
{"username": "alice", "display_name": "Alice"}

// Response 201
{
  "user_id": "a1b2c3d4-...",
  "username": "alice",
  "display_name": "Alice",
  "follower_count": 0,
  "following_count": 0,
  "created_at": "2025-06-25T12:00:00.123456Z"
}
```

Status codes: `201` created, `409` username taken, `422` validation error.

#### `GET /users/{user_id}` — Get user profile

```json
// Response 200
{
  "user_id": "a1b2c3d4-...",
  "username": "alice",
  "display_name": "Alice",
  "follower_count": 5,
  "following_count": 12,
  "created_at": "2025-06-25T12:00:00.123456Z"
}
```

Status codes: `200` found, `404` not found.

#### `GET /users/{user_id}/posts` — List user posts

```
GET /users/a1b2c3d4-.../posts?limit=20&offset=0
```

```json
// Response 200
[
  {
    "post_id": "e5f6g7h8-...",
    "user_id": "a1b2c3d4-...",
    "caption": "Sunset at the beach #sunset",
    "media_url": "/media/abcd1234.jpg",
    "media_type": "photo",
    "hashtags": ["sunset"],
    "like_count": 3,
    "created_at": "2025-06-25T12:00:00.123456Z"
  }
]
```

Query params: `limit` (default 20, max 100), `offset` (default 0). Returns newest first. Empty results return `200 []`.

### Posts

#### `POST /posts` — Create a post

```
POST /posts
Content-Type: multipart/form-data
X-User-Id: a1b2c3d4-...

image: <file>      (required, max 10 MB)
caption: <text>    (required)
```

```json
// Response 201
{
  "post_id": "e5f6g7h8-...",
  "user_id": "a1b2c3d4-...",
  "caption": "Sunset at the beach #sunset #beach",
  "media_url": "/media/abcd1234.jpg",
  "media_type": "photo",
  "hashtags": ["sunset", "beach"],
  "like_count": 0,
  "created_at": "2025-06-25T12:00:00.123456Z"
}
```

Hashtags are extracted from the caption (words starting with `#`, lowercased, deduplicated). On upload, the post is fanned out to all followers' feeds synchronously.

Status codes: `201` created, `404` user not found, `413` image too large, `422` missing image, caption, or `X-User-Id`.

#### `GET /posts/{post_id}` — Get post detail

```json
// Response 200
{
  "post_id": "e5f6g7h8-...",
  "user_id": "a1b2c3d4-...",
  "caption": "Sunset at the beach #sunset",
  "media_url": "/media/abcd1234.jpg",
  "media_type": "photo",
  "hashtags": ["sunset"],
  "like_count": 3,
  "created_at": "2025-06-25T12:00:00.123456Z"
}
```

Status codes: `200` found, `404` not found.

#### `GET /posts/media/{filename}` — Serve uploaded media

Returns the raw image file with the correct `Content-Type` (`image/jpeg`, `image/png`, `image/gif`, `image/webp`).

### Follows

#### `POST /users/{followed_id}/follow` — Follow a user

```
POST /users/b2c3d4e5-.../follow
X-User-Id: a1b2c3d4-...
```

```json
// Response 201 (first follow)
// Response 200 (already following — idempotent)
{
  "follower_id": "a1b2c3d4-...",
  "followed_id": "b2c3d4e5-...",
  "created_at": "2025-06-25T12:00:00.123456Z"
}
```

On first follow, the most recent 20 posts from the followed user are backfilled into the follower's feed. Follower/following counts are updated atomically.

Status codes: `201` new follow, `200` already following, `404` user not found, `422` self-follow or missing `X-User-Id`.

#### `DELETE /users/{followed_id}/follow` — Unfollow

```
DELETE /users/b2c3d4e5-.../follow
X-User-Id: a1b2c3d4-...
```

Removes the follow relationship, decrements counters, and deletes the unfollowed user's posts from the feed.

Status codes: `204` unfollowed, `404` not following.

### Feed

#### `GET /feed` — Get chronological feed

```
GET /feed?limit=20&before=2025-06-25T12:00:00.000000Z
X-User-Id: a1b2c3d4-...
```

```json
// Response 200
[
  {
    "post_id": "e5f6g7h8-...",
    "user_id": "b2c3d4e5-...",
    "caption": "Coffee time #coffee",
    "media_url": "/media/defg5678.jpg",
    "media_type": "photo",
    "hashtags": ["coffee"],
    "like_count": 2,
    "created_at": "2025-06-25T12:00:00.123456Z",
    "author": {
      "user_id": "b2c3d4e5-...",
      "username": "bob",
      "display_name": "Bob"
    }
  }
]
```

Returns posts from followed users, newest first. Cursor-based pagination via `before` (ISO 8601 timestamp). Each entry includes the author's profile info for rendering.

Query params: `limit` (default 20, max 100), `before` (optional cursor). Empty feed returns `200 []`.

### Search

#### `GET /search` — Search posts by hashtag

```
GET /search?q=sunset&type=hashtag&limit=20&offset=0
```

```json
// Response 200
[
  {
    "post_id": "e5f6g7h8-...",
    "user_id": "a1b2c3d4-...",
    "caption": "Sunset at the beach #sunset",
    "media_url": "/media/abcd1234.jpg",
    "media_type": "photo",
    "hashtags": ["sunset", "beach"],
    "like_count": 3,
    "created_at": "2025-06-25T12:00:00.123456Z"
  }
]
```

Uses PostgreSQL GIN index on the `hashtags` array column. Case-insensitive — searching `Sunset` matches posts tagged `#sunset`. Only `type=hashtag` is supported.

Query params: `q` (required, hashtag without `#`), `type` (required, must be `hashtag`), `limit` (default 20, max 100), `offset` (default 0).

### Likes

#### `POST /posts/{post_id}/like` — Like a post

```
POST /posts/e5f6g7h8-.../like
X-User-Id: a1b2c3d4-...
```

```json
// Response 201 (first like)
// Response 200 (already liked — idempotent)
{
  "post_id": "e5f6g7h8-...",
  "user_id": "a1b2c3d4-...",
  "created_at": "2025-06-25T12:00:00.123456Z"
}
```

Atomically increments the post's `like_count`.

Status codes: `201` new like, `200` already liked, `404` post not found.

#### `DELETE /posts/{post_id}/like` — Unlike a post

```
DELETE /posts/e5f6g7h8-.../like
X-User-Id: a1b2c3d4-...
```

Atomically decrements the post's `like_count`.

Status codes: `204` unliked, `404` not liked or post not found.

### Health

#### `GET /healthz` — Health check

```json
// Response 200
{"status": "ok", "db": "connected"}

// Response 503
{"status": "unhealthy", "db": "disconnected"}
```

Pings the database with `SELECT 1`. Used by Docker Compose healthchecks and monitoring.

## Configuration

All settings are read from environment variables via `pydantic-settings` (see `src/instagram/config.py`). Copy `.env.example` to `.env` and adjust:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://instagram:instagram@db:5432/instagram` | Database connection |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server listen port |
| `APP_PORT` | `8010` | Docker host port mapping |
| `MEDIA_DIR` | `media` | Upload storage directory |
| `MAX_UPLOAD_BYTES` | `10485760` | Max upload size (10 MB) |
| `FEED_DEFAULT_LIMIT` | `20` | Default feed page size |
| `FEED_MAX_LIMIT` | `100` | Max feed page size |
| `FEED_BACKFILL_COUNT` | `20` | Posts to backfill on follow |
| `SEARCH_DEFAULT_LIMIT` | `20` | Default search page size |
| `SEARCH_MAX_LIMIT` | `100` | Max search page size |

## Testing

### Unit tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

White-box tests that import the app directly and exercise services and endpoints.

### Acceptance tests

Black-box tests that verify the running system over HTTP — one file per functional requirement:

```bash
API_BASE_URL=http://localhost:8000 pytest verify/acceptance/ -v
```

| Test file | Functional requirement |
|---|---|
| `test_fr1_create_post.py` | FR-1 — Post creation with image and hashtags |
| `test_fr2_get_post.py` | FR-2 — Post detail retrieval |
| `test_fr3_user_posts.py` | FR-3 — Paginated user post listing |
| `test_fr4_follow.py` | FR-4 — Follow/unfollow with idempotency |
| `test_fr5_feed.py` | FR-5 — Chronological feed from followed users |
| `test_fr6_search.py` | FR-6 — Hashtag search via GIN index |
| `test_fr7_like.py` | FR-7 — Like/unlike with idempotency |
| `test_fr8_health.py` | FR-8 — Health check with DB probe |

## Limitations

- **Chronological feed only** — no ML ranking or algorithmic curation.
- **No authentication** — user identity is passed via an `X-User-Id` header. There is no password, session, or token mechanism.
- **Local filesystem media** — uploaded images are stored in the `media/` directory on the app server. For production, replace with S3 and a CDN.
- **Photos only** — video uploads are not supported. The `media_type` field is constrained to `photo`.
- **Push to all followers** — fan-out writes a feed entry for every follower on every post. This works for small follower counts but would need a hybrid push/pull strategy for celebrity accounts with millions of followers.
- **No comments, stories, DMs** — these features are out of MVP scope.
- **No WebSocket/real-time** — all interactions are request/response over REST.

## Project Layout

```
├── src/instagram/        # Application code
│   ├── main.py           # FastAPI app factory, lifespan, /healthz
│   ├── config.py         # pydantic-settings configuration
│   ├── database.py       # Async SQLAlchemy engine and session
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic request/response DTOs
│   ├── routers/          # FastAPI route handlers (thin — no business logic)
│   └── services/         # Business logic and data access
├── alembic/              # Database migrations
├── tests/                # White-box unit/integration tests
├── verify/acceptance/    # Black-box acceptance tests
├── Dockerfile            # Multi-stage Python 3.12 image
├── docker-compose.yml    # PostgreSQL 16 + app services
├── DEPLOY.md             # Deployment guide
├── DESIGN.md             # Architecture and design decisions
└── pyproject.toml        # Project metadata and dependencies
```
