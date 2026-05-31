# Runtime And Ports

- Preferred local backend smoke port is `8014` for D7.6+ and current D8 handoff validation.
- Historical D5/D6 records may mention `8000` or `8010`; do not treat those as the current validation default.
- Set `BACKEND_BASE_URL=http://127.0.0.1:8014` for D7.6+/D8 smoke scripts.
- Set `VITE_API_PROXY_TARGET=http://127.0.0.1:8014` for frontend validation.
- Docker Postgres maps to `127.0.0.1:5435`.
- Start database with `docker compose up -d db`.
- Do not run multiple backend instances with different code versions on the same smoke port.
- Local validation on `8014` does not prove `STAGING_VALIDATED`; strict staging evidence uses the real staging `BACKEND_BASE_URL`.
