# Morning deployment

Morning deploys as one logical product with three containers:

- `web`: the Morning browser/PWA surface and same-origin reverse proxy;
- `api`: the standalone Starlette Morning application;
- `db`: Morning-owned PostgreSQL 17.

Atlas is not part of this topology.

## First start

1. Copy `.env.example` to `.env`.
2. Replace both password/secret placeholders with strong random values.
3. For local HTTP use, keep `MORNING_ENV=development`.
4. Run `docker compose up -d --build`.
5. Bootstrap the first Morning administrator with the `morning` CLI inside the API container.
6. Open `http://<host>:8080` (or the configured `MORNING_PORT`).

The API container runs `alembic upgrade head` before starting the application, so a fresh database is created from the Morning migration history.

## Production

Set `MORNING_ENV=production`. Production sessions use Secure cookies, so the web service must be published through HTTPS. TLS termination may be provided by the host's existing reverse proxy; Morning does not require Atlas or an Atlas proxy.

Do not expose PostgreSQL directly to the public network.
