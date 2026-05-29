# Runtime And Ports

- Backend default development examples may use `8010`, but D7.6+ smoke validation uses `8014`.
- Set `BACKEND_BASE_URL=http://127.0.0.1:8014` for D7 smoke scripts.
- Set `VITE_API_PROXY_TARGET=http://127.0.0.1:8014` for frontend validation.
- Docker Postgres maps to `127.0.0.1:5435`.
- Start database with `docker compose up -d db`.
- Do not run multiple backend instances with different code versions on the same smoke port.
