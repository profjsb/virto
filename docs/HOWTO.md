# Virtual AI Org — HOWTO

This guide walks you through standing up the system end-to-end: API, DB, auth, Linear integration, DAG orchestration, SSE logs, and the React console.

## 1. Prerequisites
- Python 3.10+
- Node 18+ (for the console)
- Postgres 14+
- (Optional) S3 or MinIO
- (Optional) OpenAI / Anthropic API keys
- (Optional) Linear API key

## 2. Setup

### Backend
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/virtual_ai_org
alembic upgrade head

export JWT_SECRET='change-me'
export ALLOW_SIGNUP=true   # only for first registration

# LLM (optional)
# export OPENAI_API_KEY=...  # or ANTHROPIC_API_KEY=...

# Linear (optional but recommended for Sprint view)
export LINEAR_API_KEY=lin_api_...

# S3 (optional)
# export STORE_TO_S3=true S3_BUCKET=your-bucket AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_REGION=us-east-1
# export S3_ENDPOINT_URL=http://localhost:9000  # if using MinIO
uvicorn src.app:app --reload  # http://localhost:8000/docs
```

### Create Admin & Roles
```bash
# Register first user (becomes admin)
curl -X POST localhost:8000/auth/register -H 'content-type: application/json' \
  -d '{"email":"admin@example.com","password":"admin123"}' | jq -r .access_token
# Save the token and use it for subsequent requests
```

Assign roles (optional; admin can assign):
```bash
curl -X POST localhost:8000/auth/assign-role \
 -H 'authorization: Bearer <TOKEN>' -H 'content-type: application/json' \
 -d '{"user_id":1,"role":"approver"}'
```

## 3. Approvals & Policies
- Set thresholds in `governance/policies.yaml`.
- Submit approvals: `POST /approvals/submit` (roles: engineer/growth/approver/admin)
- Approve/reject: `PATCH /approvals/{id}/decision?approved=true|false` (roles: approver/admin)

## 4. Meetings & Orchestration

### Built-in DAG
- Endpoint: `POST /orchestration/dag/meeting_cycle` (engineer/admin)
- The DAG chains: brainstorm → stand-up → all-hands.
- Edit `src/orchestration/flows.py` and `src/orchestration/dag.py` to extend.

### LangGraph (optional)
```bash
pip install langgraph langchain
```
- Endpoint: `POST /orchestration/langgraph/meeting_cycle`
- Code: `src/orchestration/langgraph_adapter.py`

### CrewAI (optional)
```bash
pip install crewai crewai-tools
```
- Endpoint: `POST /orchestration/crewai/brainstorm`
- Code: `src/orchestration/crewai_adapter.py`

## 5. Live Run Logs (SSE)
- Start a demo run: `POST /runs/start_demo` → `{ run_id }`
- Subscribe: `GET /streams/runs/{run_id}` (SSE; emits `log` events and `done`)
- Internals: `src/services/event_stream.py` (simple in-memory hub). For multi-instance deployments, swap for Redis pub/sub.

## 6. Linear Sprint Board
- Set `LINEAR_API_KEY`.
- Endpoints:
  - `GET /linear/teams`
  - `GET /linear/cycles?team_id=...`
  - `GET /linear/issues?team_id=...&cycle_id=...`
  - `POST /linear/issues` `{ team_id, title, description }`
- Client: `console/src/Sprint.tsx`

## 7. React Ops Console
```bash
cd console
npm install
# optional: export VITE_API_BASE=http://localhost:8000
npm run dev
```
- Sign in (after register): the token is stored in `localStorage`.
- Tabs: Approvals, Sprint, Run Logs, Spend.

## 8. Storage & Downloads
- Local artifacts under `data/` are served at `/data/...`.
- If S3 is enabled, artifacts get presigned URLs. Adjust `src/utils/s3.py` to fit your endpoint.

## 9. LLM Cost Logging
- LLM calls log token counts and estimated cost to `usage_events`.
- Set per-token prices to match your provider: `OPENAI_PRICE_IN`, `OPENAI_PRICE_OUT`, `ANTHROPIC_PRICE_IN`, `ANTHROPIC_PRICE_OUT`.

## 10. RBAC Matrix
| Feature | viewer | engineer | growth | approver | admin |
|---|---|---|---|---|---|
| View approvals | ✅ | ✅ | ✅ | ✅ | ✅ |
| Submit approvals | ❌ | ✅ | ✅ | ✅ | ✅ |
| Decide approvals | ❌ | ❌ | ❌ | ✅ | ✅ |
| Run DAG / orchestration | ❌ | ✅ | ❌ | ❌ | ✅ |
| Meetings (stand-up/brainstorm/all-hands) | ✅ | ✅ | ✅ (brainstorm) | ✅ | ✅ |
| View minutes & spend | ✅ | ✅ | ✅ | ✅ | ✅ |
| Manage roles | ❌ | ❌ | ❌ | ❌ | ✅ |

## 11. Production Notes
- Replace JWT secret and disable `ALLOW_SIGNUP`.
- Use a real event bus (Redis/NATS) for streams.
- Run workers for heavy orchestration.
- Add HTTPS, auth for the console, and proper CORS allowlists.
- Pin model versions and prompt templates; store ADRs.

## 12. Troubleshooting
- 401s from console → ensure you logged in and the token is set.
- Linear 401/403 → check `LINEAR_API_KEY`.
- SSE doesn’t stream → proxies may buffer; use `--reload` locally or deploy with uvicorn workers=1 for demo.

Enjoy! 🚀


## 15. One-Command Stack (Docker Compose)

Bring up API + Postgres + Redis + MinIO + Console:
```bash
docker compose up -d --build
# or
make up
```

Open:
- API: http://localhost:8000/docs
- Console: http://localhost:5173
- MinIO Console: http://localhost:9001 (user: `minio`, pass: `minio123`)
- Postgres: localhost:5432 (user: postgres / pass: postgres)

Shut down and remove volumes:
```bash
docker compose down -v
# or
make down
```

Notes:
- The console is built with `VITE_API_BASE=http://localhost:8000`. Change in `docker-compose.yml` if needed.
- The API mounts `./data` into the container so local artifacts are accessible via `/data/...` routes.
- LINEAR_MOCK=true is enabled by default so the Sprint tab works without a Linear key.
- SSE uses Redis pub/sub automatically in this setup.


## 16. CI/CD (GitHub Actions)
Workflows are in `.github/workflows/`:

- `ci.yml`: lint (ruff), tests (pytest), build images
- `docker-publish.yml`: builds & pushes images to GHCR on pushes to `main` and tags `v*`
- `fly-deploy.yml`: (optional) deploys API & Console to Fly.io on `main`

### Setup GHCR
No secrets required; `GITHUB_TOKEN` is used automatically. Images are published as:
- `ghcr.io/<owner>/virtual-ai-org-api`
- `ghcr.io/<owner>/virtual-ai-org-console`

### Fly.io Deploy
1. Install flyctl locally and create two apps (or let `flyctl deploy` do it):
   ```bash
   flyctl apps create vo-api-<you>
   flyctl apps create vo-console-<you>
   ```
2. Update `fly.api.toml` and `fly.console.toml` app names.
3. Add `FLY_API_TOKEN` to GitHub repo secrets.
4. (Optional) Set production secrets:
   ```bash
   flyctl secrets set JWT_SECRET=... --app vo-api-<you>
   flyctl secrets set DATABASE_URL=... REDIS_URL=... --app vo-api-<you>
   ```
5. Push to `main` or run the workflow manually.

### Render One‑Click
- Use **Render Blueprint** with `render.yaml` (repo root). In Render, choose **New → Blueprint** and point to your repo.
- It provisions Postgres and Redis, deploys the API and Console, and wires env vars automatically.
- Set `JWT_SECRET` as a secret in the `vo-api` service settings post‑provision.

