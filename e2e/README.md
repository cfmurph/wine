# Browser checks

These drive the running app in Chrome.

```bash
docker compose up -d --build
cd e2e && npm install && npm test        # or: npm test -- land sales
```

- They need Google Chrome. Set `CHROME_PATH` if it isn't in the default location.
- `E2E_WEB_URL` and `E2E_API_URL` point them at another deployment.
- They create users with `e2e-*@example.com` addresses and fictional deals, and remove them afterwards.
- An empty database needs fixture data: `docker compose exec -T backend python3 - < e2e/seed_fixture.py`. CI does this because it has no real BC data. Never run it against a database with real data.
