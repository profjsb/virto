# Virtual AI Organization (VO)

A production-ready framework for building and operating virtual organizations staffed by AI agents. This system provides governance frameworks, LLM orchestration, operational workflows, and observability tools for managing autonomous AI teams.

## Overview

**Virtual AI Organization** is a FastAPI-based platform that enables you to:

- 🤖 **Orchestrate AI Agents** — Coordinate multiple AI personas with different roles and responsibilities
- 📋 **Manage Workflows** — Run structured meetings (standups, brainstorms, all-hands) with configurable templates
- 🔐 **Control Access** — JWT authentication with RBAC (admin, approver, engineer, growth, viewer roles)
- 💰 **Track Spend** — Monitor LLM usage and costs across providers (OpenAI, Anthropic)
- ✅ **Approve Decisions** — Policy-based approval workflows with configurable thresholds
- 📊 **Monitor Operations** — Real-time event streaming and artifact management
- 🔗 **Integrate Tools** — Built-in Linear and Notion integrations, S3 storage, and extensible service layer
- 🧠 **Capture Memory** — Store organizational knowledge in Notion for searchable institutional memory

## Architecture

```
├── src/                        # FastAPI application
│   ├── app.py                 # Main API routes and endpoints
│   ├── db/                    # SQLAlchemy models and database
│   ├── orchestration/         # Workflow engines (DAG, LangGraph, CrewAI, AutoGen)
│   ├── services/              # Auth, LLM providers, event streaming, Linear
│   └── utils/                 # S3, storage, I/O utilities
├── console/                    # React/TypeScript ops dashboard
├── governance/                 # Machine-readable policies and constitution
├── meetings/templates/         # Structured meeting formats
├── personas/                   # AI agent persona definitions (JSON)
├── schemas/                    # JSON schemas for validation
├── alembic/                    # Database migrations
└── docs/adr/                  # Architecture Decision Records
```

## Quick Start

### 1. Backend Setup

```bash
# Python 3.10+ required
# Install uv if not already installed: https://docs.astral.sh/uv/
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Configure database
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/virtual_ai_org

# Run migrations
uv run alembic upgrade head

# Configure authentication
export JWT_SECRET='your-secure-secret-key'
export ALLOW_SIGNUP=true

# Start API server
uv run uvicorn src.app:app --reload
```

API documentation available at: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup

```bash
cd console
npm install
export VITE_API_BASE=http://localhost:8000
npm run dev
```

### 3. Create First User

```bash
curl -X POST localhost:8000/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"admin@example.com","password":"admin123"}'
```

The first user is automatically assigned the `admin` role. Save the returned `access_token` for API requests.

## Core Features

### Authentication & Authorization

**JWT-based authentication** with role-based access control:

- **admin** — Full system access
- **approver** — Approve spending and decisions
- **engineer** — Run technical workflows
- **growth** — Business and product operations
- **viewer** — Read-only access

```bash
# Assign roles
curl -X POST localhost:8000/auth/assign-role \
  -H 'authorization: Bearer <TOKEN>' \
  -H 'content-type: application/json' \
  -d '{"user_id":2,"role":"engineer"}'
```

### LLM Provider Integration

Supports multiple LLM providers with unified interface:

```bash
# Configure providers
export OPENAI_API_KEY='sk-...'
export ANTHROPIC_API_KEY='sk-ant-...'

# Optional: Custom pricing for spend tracking
export OPENAI_PRICE_IN=0.000001
export OPENAI_PRICE_OUT=0.000002
export ANTHROPIC_PRICE_IN=0.000003
export ANTHROPIC_PRICE_OUT=0.000015
```

### Orchestration Systems

**Multiple workflow engines supported:**

1. **Custom DAG Engine** (`src/orchestration/dag.py`)
2. **LangGraph Adapter** — Graph-based workflows
3. **CrewAI Adapter** — Multi-agent collaboration
4. **AutoGen Adapter** — Conversational agents

```bash
# Run meeting cycle workflow
curl -X POST localhost:8000/orchestration/dag/meeting_cycle \
  -H 'authorization: Bearer <TOKEN>' \
  -H 'content-type: application/json' \
  -d '{"topic":"MVP kickoff"}'
```

### Approval Workflows

Policy-based approval system with auto-approval thresholds:

```bash
# Submit approval request
curl -X POST localhost:8000/approvals/submit \
  -H 'authorization: Bearer <TOKEN>' \
  -H 'content-type: application/json' \
  -d '{
    "description":"Cloud infrastructure upgrade",
    "amount_usd":250.00,
    "justification":"Scale for production launch"
  }'
```

Requests below the policy threshold are auto-approved. Configure in `governance/policies.yaml`.

### Meeting Templates

Structured meeting workflows with markdown output:

- **Standup** — Daily sync (yesterday, today, blockers)
- **Brainstorm** — Idea generation and prioritization
- **All-Hands** — Weekly metrics, updates, risks, lessons

```bash
# Run brainstorm meeting
curl -X POST localhost:8000/meetings/brainstorm \
  -H 'authorization: Bearer <TOKEN>' \
  -H 'content-type: application/json' \
  -d '{
    "topic":"Q4 Product Strategy",
    "owner":"ceo",
    "ideas":["Feature A","Feature B","Feature C"]
  }'
```

### Real-Time Event Streaming

Server-Sent Events (SSE) for live run monitoring:

```bash
# Start a demo run
curl -X POST localhost:8000/runs/start_demo \
  -H 'authorization: Bearer <TOKEN>'

# Stream events (in browser or EventSource client)
# GET /streams/runs/{run_id}
```

### Linear Integration

Project management integration for AI-driven development:

```bash
# Configure Linear
export LINEAR_API_KEY='lin_api_...'

# List teams
curl localhost:8000/linear/teams \
  -H 'authorization: Bearer <TOKEN>'

# Create issue
curl -X POST localhost:8000/linear/issues \
  -H 'authorization: Bearer <TOKEN>' \
  -H 'content-type: application/json' \
  -d '{
    "team_id":"TEAM-123",
    "title":"Implement feature X",
    "description":"Technical details..."
  }'
```

### Notion Integration

**Institutional memory capture** via Notion MCP API for searchable knowledge management:

```bash
# Configure Notion (get OAuth token from Notion MCP connection)
export NOTION_OAUTH_TOKEN='...'
export NOTION_MCP_URL='https://mcp.notion.com/mcp'  # default

# Search workspace
curl -X POST localhost:8000/notion/search \
  -H 'authorization: Bearer <TOKEN>' \
  -H 'content-type: application/json' \
  -d '{"query":"engineering","limit":10}'

# Create page for meeting minutes
curl -X POST localhost:8000/notion/pages \
  -H 'authorization: Bearer <TOKEN>' \
  -H 'content-type: application/json' \
  -d '{
    "title":"Standup 2025-10-06",
    "content":"# Daily Standup\n\n## Yesterday\n- Completed API integration\n\n## Today\n- Testing deployment"
  }'

# Append to existing page
curl -X POST localhost:8000/notion/pages/{page_id}/append \
  -H 'authorization: Bearer <TOKEN>' \
  -H 'content-type: application/json' \
  -d '{"content":"## Follow-up\n- Review PR #123"}'
```

**Setup**: Follow [Notion MCP setup guide](https://developers.notion.com/docs/get-started-with-mcp) to connect your workspace and obtain OAuth token. Enable mock mode for testing: `export NOTION_MOCK=true`

## Storage Options

### PostgreSQL (Required)

Primary data store for users, approvals, artifacts, usage events:

```bash
export DATABASE_URL=postgresql+psycopg://user:pass@host:5432/dbname
alembic upgrade head
```

### S3 (Optional)

Artifact storage for meeting minutes and outputs:

```bash
export STORE_TO_S3=true
export S3_BUCKET=your-bucket
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=us-east-1

# For MinIO or custom S3-compatible storage
export S3_ENDPOINT_URL=http://localhost:9000
```

### Redis (Optional)

Event pub/sub for distributed deployments:

```bash
export REDIS_URL=redis://localhost:6379
```

## Deployment

### Docker Compose

```bash
docker-compose up -d
```

Includes PostgreSQL, Redis, API, and console services.

### Fly.io

```bash
fly deploy --config fly.api.toml
fly deploy --config fly.console.toml
```

### Render

Uses `render.yaml` for infrastructure-as-code deployment.

## Configuration Reference

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `JWT_SECRET` | Yes | Secret key for JWT signing |
| `ALLOW_SIGNUP` | No | Enable open registration (default: false) |
| `ADMIN_SIGNUP_SECRET` | No | Secret for admin registration |
| `OPENAI_API_KEY` | No | OpenAI API key |
| `ANTHROPIC_API_KEY` | No | Anthropic API key |
| `STORE_TO_S3` | No | Enable S3 storage (default: false) |
| `S3_BUCKET` | No | S3 bucket name |
| `LINEAR_API_KEY` | No | Linear API key |
| `REDIS_URL` | No | Redis connection string |

### Governance Files

- `governance/constitution.md` — Organizational charter
- `governance/policies.yaml` — Machine-readable policies (spending thresholds, etc.)
- `personas/*.json` — AI agent persona definitions
- `schemas/*.schema.json` — Validation schemas for personas and hiring plans

## Development

### Project Structure

```
src/
├── app.py                  # API routes and dependency injection
├── db/
│   ├── __init__.py        # Database session factory
│   └── models.py          # SQLAlchemy models
├── orchestration/
│   ├── dag.py             # Custom DAG engine
│   ├── flows.py           # Meeting workflow implementations
│   ├── langgraph_adapter.py
│   ├── crewai_adapter.py
│   └── autogen_loop.py
├── services/
│   ├── auth.py            # JWT and password hashing
│   ├── auth_rbac.py       # Role-based access control
│   ├── llm_provider.py    # Unified LLM interface
│   ├── usage_logger.py    # Token and cost tracking
│   ├── event_stream.py    # SSE pub/sub hub
│   ├── linear_client.py   # Linear GraphQL client
│   └── policy.py          # Policy loading and evaluation
└── utils/
    ├── s3.py              # S3 operations
    ├── store.py           # Namespace-based storage
    └── io.py              # File I/O utilities
```

### Running Tests

The project includes comprehensive testing for both backend and frontend:

```bash
# Quick test run (recommended before PRs)
./scripts/run_tests.sh --quick

# Full test suite with integration tests
./scripts/run_tests.sh --full

# Backend tests only
make test-backend
# or
uv run pytest -v

# Frontend tests only
make test-frontend
# or
cd console && npm run test

# Run all tests
make test-all

# Generate coverage reports
make test-backend-cov  # Backend coverage -> htmlcov/index.html
make test-frontend-cov # Frontend coverage -> console/coverage/

# Run linters and formatters
make lint        # Check code style
make lint-fix    # Auto-fix linting issues
make format      # Format code

# Run specific test types
uv run pytest -m unit         # Unit tests only
uv run pytest -m integration  # Integration tests only
```

For detailed testing documentation, see [TESTING.md](TESTING.md)

### Database Migrations

```bash
# Create new migration
uv run alembic revision -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

## Use Cases

### 1. AI Team Hiring

Generate structured hiring plans for AI-powered teams:

```bash
curl -X POST localhost:8000/hiring/plan \
  -H 'authorization: Bearer <TOKEN>' \
  -H 'content-type: application/json' \
  -d '{
    "idea":"Build marketplace for local services",
    "budget_usd":50000,
    "deadline_days":90,
    "goal":"Launch MVP with 100 users"
  }'
```

Returns role definitions, workstreams, and metrics.

### 2. Automated Standups

Daily team synchronization without human coordination:

```bash
curl -X POST localhost:8000/meetings/standup \
  -H 'authorization: Bearer <TOKEN>' \
  -H 'content-type: application/json' \
  -d '{
    "date":"2025-10-02",
    "attendees":["cto","ceo","cxo"],
    "yesterday":["Shipped auth system"],
    "today":["Implement payment flow"],
    "blockers":["Waiting on Stripe credentials"]
  }'
```

### 3. Spend Monitoring

Track LLM costs across the organization:

```bash
# View in console at /spend
# Or query database directly
SELECT provider, model, SUM(cost_usd)
FROM usage_events
GROUP BY provider, model;
```

## API Reference

Full interactive API documentation available at `/docs` when running the server.

**Key Endpoints:**

- `POST /auth/register` — User registration
- `POST /auth/login` — Authentication
- `POST /hiring/plan` — Generate AI hiring plan
- `POST /approvals/submit` — Submit approval request
- `PATCH /approvals/{id}/decision` — Approve/reject
- `POST /meetings/{standup,brainstorm,allhands}` — Run meetings
- `POST /orchestration/dag/meeting_cycle` — Execute workflow
- `GET /streams/runs/{run_id}` — Stream run events (SSE)
- `GET /ops/{approvals,minutes}` — List operational artifacts
- `GET /linear/{teams,cycles,issues}` — Linear integration

## Roadmap

- [ ] Vector database integration for semantic search
- [ ] OpenTelemetry observability
- [ ] Multi-tenant support
- [ ] Webhook system for external integrations
- [ ] Advanced workflow editor UI
- [ ] Persona marketplace
- [ ] Budget forecasting and alerts

## Contributing

See [docs/HOWTO.md](docs/HOWTO.md) for development guidelines.

Architecture decisions are documented in [docs/adr/](docs/adr/).

## License

See [LICENSE](LICENSE) file for details.
