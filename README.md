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

Create a virtual environment:

```shell
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or activate it on macOS/Linux:

```shell
source .venv/bin/activate
```

Install the dependencies:

```shell
pip install -r requirements.txt
```

Run the tests:

```shell
pytest -q
```

Start the API:

```shell
uvicorn app.main:app --reload
```

Interactive API documentation is available at http://127.0.0.1:8000/docs.
