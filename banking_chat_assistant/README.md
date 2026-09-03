# Banking AI Chat Assistant

Agentic AI customer-support platform for banking, built with FastAPI, a LangGraph
multi-agent orchestrator, RAG over ChromaDB, RabbitMQ event-driven architecture,
PostgreSQL, and OpenTelemetry.

## Architecture

```
Client → API (FastAPI) → Orchestrator (LangGraph) → Agent → RAG → Event Bus
```

The orchestrator graph:

```
guardrail_input → classify_intent → ┬→ account_agent ─┐
                                    ├→ card_agent     │
                                    ├→ loan_agent     ├→ END
                                    └→ rag_agent    ──┘
```

## Quick start

### Docker (full stack: API + PostgreSQL + RabbitMQ)

```bash
cp .env.example .env
docker compose up --build
```

### Local

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

API docs: http://localhost:8000/docs

> The default `LLM_PROVIDER=mock` and `EMBEDDING_MODEL=local-hash` let the app run
> fully offline with no API keys. Set `LLM_PROVIDER=openai` plus `LLM_API_KEY` for
> a real model. If RabbitMQ is unreachable the app starts in degraded mode: events
> are logged and skipped rather than failing requests.

## Authentication

All endpoints require `Authorization: Bearer <session-token>`. Tokens are HMAC-signed
and the customer identity is derived from the token — client-supplied identifiers are
never trusted. Generate a demo token:

```bash
python -c "
from app.core.config import get_settings
from app.core.security import issue_session_token
print(issue_session_token('cust_demo_001', get_settings()))"
```

## Endpoints

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/api/v1/chat` | Multi-agent conversational entrypoint |
| POST | `/api/v1/chat/stream` | SSE token streaming (`text/event-stream`) |
| POST | `/api/v1/account/balance` | Balance inquiry |
| POST | `/api/v1/account/transactions` | Transaction history |
| POST | `/api/v1/cards/block` | Requires `Idempotency-Key` header |
| POST | `/api/v1/cards/unblock` | Requires `Idempotency-Key` header |
| POST | `/api/v1/loans/details` | Loan status, outstanding, EMI |
| POST | `/api/v1/complaints` | Requires `Idempotency-Key` header |
| GET | `/api/v1/complaints/{id}` | Complaint status |
| GET | `/api/v1/health/live`, `/ready` | Health probes |

Example:

```bash
curl -X POST localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"session_id":"s1","message":"What is the minimum balance policy for savings accounts?"}'
```

## Error format

All errors return the standard envelope:

```json
{ "error_code": "AGENT_TIMEOUT", "message": "Agent execution timeout.", "details": {} }
```

Provider-specific errors are never leaked; they are mapped to `LLM_PROVIDER_ERROR`,
`BROKER_UNAVAILABLE`, `TOOL_EXECUTION_ERROR`, etc.

## Events

See [docs/events.md](docs/events.md) for the full event catalogue and schema.

## Testing

```bash
pytest --cov=app --cov-report=term-missing
```

45 tests, ~83% coverage. The suite runs fully offline (SQLite, mock LLM, local-hash
embeddings, degraded broker) with `app.dependency_overrides` used for auth injection.

## Project layout

Domain-based, not layer-based:

```
app/
  api/v1/       routers (one per domain)
  agents/       intent_classifier, account, card, loan, complaint, rag, guardrail, tools
  orchestrator/ workflow.py, router.py, state.py
  rag/          ingestion, retrieval, embeddings, reranking, vectordb
  clients/      llm, vector, broker, banking_api
  services/     chat, complaint, rag, audit
  schemas/      chat, events, agents, errors, customer
  core/         config, exceptions, middleware, logging, dependencies, security, idempotency
  events/       producer, consumer
  db/           models, session, seed
tests/
main.py
```

## Security notes

- PII (account/card numbers) is masked in logs; raw prompts are never persisted.
- User messages, retrieved documents, and tool outputs are all treated as untrusted
  and screened by the guardrail agent for prompt injection.
- Sensitive actions (card block/unblock, complaint creation) are idempotency-key protected.
