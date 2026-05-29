# Security And Git Safety

- Never commit `.env`, real tokens, `local_data/`, `backend/storage/`, uploads, or generated logs.
- Use `.env.example` files for templates only.
- Do not expose internal costs, margins, supplier private notes, pricing internals, storage keys, backend paths, passwords, secrets, or tokens.
- Run `git status --short` and `git diff --check` before staging.
- Prefer explicit `git add` paths over broad staging when local generated files may exist.
- Push to `origin master` only after requested validation passes.
