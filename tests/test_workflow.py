import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import store


client = TestClient(app)


@pytest.fixture(autouse=True)
def empty_store():
    store.clear()
    yield
    store.clear()


def create_intake(**overrides):
    payload = {
        "requester": "Morgan Lee",
        "subject": "Urgent invoice payment",
        "details": "A supplier invoice is blocked and needs payment immediately.",
    }
    payload.update(overrides)
    return client.post("/intakes", json=payload)


def test_create_intake_returns_structured_classification_and_awaiting_review():
    response = create_intake()

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["requester"] == "Morgan Lee"
    assert body["status"] == "awaiting_review"
    assert body["classification"] == {
        "category": "finance",
        "priority": "high",
        "summary": "A supplier invoice is blocked and needs payment immediately.",
        "recommended_action": "Route to the finance team for review.",
    }
    assert body["reviewer"] is None
    assert body["reviewed_at"] is None
    assert body["created_at"]


def test_get_intake_returns_created_record():
    created = create_intake().json()

    response = client.get(f"/intakes/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_unknown_intake_returns_404():
    response = client.get("/intakes/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json() == {"detail": "Intake not found"}


def test_review_unknown_intake_returns_404():
    response = client.post(
        "/intakes/00000000-0000-0000-0000-000000000000/review",
        json={"decision": "approve", "reviewer": "Taylor Kim", "note": "Budget confirmed."},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Intake not found"}


def test_approve_intake_stores_reviewer_information():
    created = create_intake().json()

    response = client.post(
        f"/intakes/{created['id']}/review",
        json={"decision": "approve", "reviewer": "Taylor Kim", "note": "Budget confirmed."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["reviewer"] == "Taylor Kim"
    assert body["review_note"] == "Budget confirmed."
    assert body["reviewed_at"] is not None


def test_approved_intake_review_state_is_observable_through_get():
    created = create_intake().json()
    intake_url = f"/intakes/{created['id']}"

    review_response = client.post(
        f"{intake_url}/review",
        json={"decision": "approve", "reviewer": "Taylor Kim", "note": "Budget confirmed."},
    )

    assert review_response.status_code == 200

    response = client.get(intake_url)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["reviewer"] == "Taylor Kim"
    assert body["review_note"] == "Budget confirmed."
    assert body["reviewed_at"] is not None


def test_reject_intake():
    created = create_intake(subject="Software request", details="Please install this software.").json()

    response = client.post(
        f"/intakes/{created['id']}/review",
        json={"decision": "reject", "reviewer": "Jordan Patel"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert response.json()["review_note"] is None


def test_completed_intake_cannot_be_reviewed_again():
    created = create_intake().json()
    url = f"/intakes/{created['id']}/review"
    client.post(url, json={"decision": "approve", "reviewer": "Taylor Kim"})

    response = client.post(url, json={"decision": "reject", "reviewer": "Jordan Patel"})

    assert response.status_code == 409
    assert response.json() == {"detail": "Only intakes awaiting review can be reviewed"}


@pytest.mark.parametrize(
    "payload",
    [
        {"subject": "Missing requester", "details": "Some details"},
        {"requester": "Morgan Lee", "subject": "", "details": "Some details"},
        {"requester": "Morgan Lee", "subject": "Subject", "details": ""},
    ],
)
def test_create_intake_rejects_invalid_input(payload):
    response = client.post("/intakes", json=payload)

    assert response.status_code == 422


def test_review_rejects_invalid_decision():
    created = create_intake().json()

    response = client.post(
        f"/intakes/{created['id']}/review",
        json={"decision": "maybe", "reviewer": "Taylor Kim"},
    )

    assert response.status_code == 422


def test_category_and_priority_defaults_are_deterministic():
    response = create_intake(
        subject="General request",
        details="Please arrange a new sign for the meeting room.",
    )

    assert response.status_code == 201
    assert response.json()["classification"]["category"] == "other"
    assert response.json()["classification"]["priority"] == "medium"
