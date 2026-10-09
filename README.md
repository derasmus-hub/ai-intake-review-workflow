# AI Intake Review Workflow

A small FastAPI portfolio project showing how deterministic or OpenAI-backed classification can fit into a normal business process without giving the classifier authority over important decisions.

This is an educational demonstration, not production software.

## What it demonstrates

A requester submits a business request. The application asks the selected classifier for a category, priority, summary, and recommended action, then records the request as `awaiting_review`. A human reviewer makes the final approve or reject decision.

The control boundary is intentional:

> AI may recommend. Application code controls state. A human makes the final decision.

## Workflow

```text
POST /intakes
    submitted -> classification -> awaiting_review
                                       |
                     human approves ---+---> approved
                     human rejects  ---+---> rejected
```

Completed records retain the original request, structured classification, workflow status, reviewer, optional review note, creation time, and review time.

## Classification backends

Deterministic classification remains the default. `app/classifier.py` uses understandable keyword rules, making local behavior repeatable and runnable without API keys or network services.

OpenAI classification is optional. It uses the Responses API structured-output parsing support to produce the same validated `AIClassification` contract: `category`, `priority`, `summary`, and `recommended_action`. The OpenAI model receives only the request subject and details. It cannot modify workflow state, approve or reject an intake, access reviewer information, or access persistence.

Classification must succeed before the application changes the intake to `awaiting_review` and saves it. If OpenAI classification fails or returns invalid output, the API returns HTTP 503 and does not save the intake.

## Technology

- Python 3.11
- FastAPI and Pydantic
- OpenAI Python SDK and Responses API structured outputs
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
- Deterministic classification is keyword based; optional OpenAI classification requires API access.
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

The deterministic classifier is used by default, so no API key is required:

```text
CLASSIFIER_BACKEND=deterministic
```

To use OpenAI classification, set `CLASSIFIER_BACKEND=openai` and provide `OPENAI_API_KEY` through the environment. `OPENAI_MODEL` is optional and defaults to `gpt-6-luna`. Never place a real API key in source code or commit it to the repository.

Windows PowerShell example:

```powershell
$env:CLASSIFIER_BACKEND = "openai"
$env:OPENAI_API_KEY = "your-api-key"
$env:OPENAI_MODEL = "gpt-6-luna"
```

macOS/Linux example:

```shell
export CLASSIFIER_BACKEND=openai
export OPENAI_API_KEY=your-api-key
export OPENAI_MODEL=gpt-6-luna
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
