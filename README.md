# AI Intake Review Workflow

A small FastAPI portfolio project showing how AI-ready classification can fit into a normal business process without giving the classifier authority over important decisions.

This is an educational demonstration, not production software.

## What it demonstrates

A requester submits a business request. The application records it, asks an isolated deterministic classifier for a category, priority, summary, and recommended action, then moves it to `awaiting_review`. A human reviewer makes the final approve or reject decision.

The control boundary is intentional:

> AI may recommend. Application code controls state. A human makes the final decision.

## Workflow

```text
POST /intakes
    submitted -> deterministic classification -> awaiting_review
                                                    |
                                  human approves ---+---> approved
                                  human rejects  ---+---> rejected
```

Completed records retain the original request, structured classification, workflow status, reviewer, optional review note, creation time, and review time.

## Why version one is deterministic

`app/classifier.py` uses understandable keyword rules instead of an external AI provider. This makes the behavior repeatable, testable, and runnable without API keys or network services. The classifier returns only structured advice and has no access to the persistence layer or workflow status.

A future LLM-backed implementation can replace `classify_request` while keeping the same `AIClassification` output contract. The routes and review rules can remain responsible for state changes, so an LLM still cannot approve or reject a request.

## Technology

- Python 3.11
- FastAPI and Pydantic
- In-memory persistence
- pytest and FastAPI TestClient
- Uvicorn for local development

## API

- `POST /intakes` creates and classifies a request.
- `GET /intakes/{id}` retrieves a request.
- `POST /intakes/{id}/review` records a human `approve` or `reject` decision.

Interactive API documentation is available at `/docs` while the application is running.

## Current limitations

- Persistence is in memory and resets when the application restarts.
- Classification is deterministic and keyword based.
- Reviewer identity is supplied by the request and is not authenticated in this version.
- This is a portfolio demonstration, not production software.

## Run locally

The development convention in `AGENTS.md` runs Python inside a Docker container named `ai-intake-dev`, with this repository mounted at `/workspace`. From the repository directory:

```sh
docker run -d --name ai-intake-dev -p 8000:8000 -v "${PWD}:/workspace" -w /workspace python:3.11-slim sleep infinity
docker exec ai-intake-dev pip install -r requirements.txt
docker exec ai-intake-dev pytest -q
docker exec ai-intake-dev uvicorn app.main:app --host 0.0.0.0
```

In Windows PowerShell, use the same commands with `${PWD}` expanding to the repository path. If the named container already exists, start and reuse it rather than creating another. API documentation is available at http://127.0.0.1:8000/docs. Stop the container with `docker stop ai-intake-dev` when finished.

## Verification and design boundaries

GitHub Actions runs pytest inside the same named-container convention. Tests cover API validation, classification output, retrieval, approve/reject decisions, terminal-state conflicts, and blank-field rejection. Classification remains a deterministic keyword demonstration: category selection uses the first matching category in the configured order, priority uses high before low, and summaries normalize whitespace before truncation. This is not semantic reasoning or a measured classifier evaluation.

The review endpoint does not authenticate the caller. A supplied reviewer name is metadata, not verified identity. The in-memory store is process-local, has no transactional concurrency protection, and is unsuitable for multi-worker deployment. Reviewer timestamps do not constitute an immutable audit log.

A future external classifier would need schema validation, failure handling, and evaluation before being treated as a working integration. No such integration is claimed here.
