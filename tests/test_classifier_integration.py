from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.classifier import (
    ClassificationError,
    ClassifierConfigurationError,
    classify_request,
    get_classifier,
)
from app.llm_classifier import OpenAIClassifier
from app.models import AIClassification, Category, Priority
from app.store import store


client = TestClient(main_module.app)


def test_application_metadata_reports_stage_2_version():
    assert main_module.app.version == "0.3.0"


@pytest.fixture(autouse=True)
def empty_store():
    store.clear()
    yield
    store.clear()


def test_deterministic_is_the_default_backend(monkeypatch):
    monkeypatch.delenv("CLASSIFIER_BACKEND", raising=False)

    assert get_classifier() is classify_request


def test_explicit_openai_backend_selects_openai_classifier(monkeypatch):
    monkeypatch.setenv("CLASSIFIER_BACKEND", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.llm_classifier._create_openai_client", lambda api_key: object())

    assert isinstance(get_classifier(), OpenAIClassifier)


def test_unknown_backend_is_rejected(monkeypatch):
    monkeypatch.setenv("CLASSIFIER_BACKEND", "unknown")

    with pytest.raises(ClassifierConfigurationError, match="deterministic.*openai"):
        get_classifier()


def test_openai_backend_requires_api_key(monkeypatch):
    monkeypatch.setenv("CLASSIFIER_BACKEND", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ClassifierConfigurationError, match="OPENAI_API_KEY"):
        get_classifier()


def test_openai_backend_rejects_whitespace_only_api_key(monkeypatch):
    monkeypatch.setenv("CLASSIFIER_BACKEND", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "   \t  ")

    with pytest.raises(ClassifierConfigurationError, match="OPENAI_API_KEY"):
        get_classifier()


def test_openai_model_defaults_to_gpt_6_luna(monkeypatch):
    monkeypatch.setenv("CLASSIFIER_BACKEND", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.setattr("app.llm_classifier._create_openai_client", lambda api_key: object())

    classifier = get_classifier()

    assert classifier.model == "gpt-6-luna"


@pytest.mark.parametrize("configured_model", ["", "   \t  "])
def test_blank_openai_model_defaults_to_gpt_6_luna(monkeypatch, configured_model):
    monkeypatch.setenv("CLASSIFIER_BACKEND", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", configured_model)
    monkeypatch.setattr("app.llm_classifier._create_openai_client", lambda api_key: object())

    classifier = get_classifier()

    assert classifier.model == "gpt-6-luna"


def test_configured_openai_model_overrides_default(monkeypatch):
    monkeypatch.setenv("CLASSIFIER_BACKEND", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "  configured-model  ")
    monkeypatch.setattr("app.llm_classifier._create_openai_client", lambda api_key: object())

    classifier = get_classifier()

    assert classifier.model == "configured-model"


def test_classification_failure_returns_503_and_does_not_save(monkeypatch):
    def failing_classifier(subject, details):
        raise ClassificationError("provider detail")

    save_calls = []
    monkeypatch.setattr(main_module, "classifier", failing_classifier)
    monkeypatch.setattr(store, "save", lambda record: save_calls.append(record))

    response = client.post(
        "/intakes",
        json={
            "requester": "Morgan Lee",
            "subject": "Urgent invoice payment",
            "details": "A supplier invoice is blocked.",
        },
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Classification service unavailable"}
    assert save_calls == []


def test_successful_openai_classification_results_only_in_awaiting_review(monkeypatch):
    classification = AIClassification(
        category=Category.FINANCE,
        priority=Priority.HIGH,
        summary="A supplier invoice is blocked.",
        recommended_action="Route to the finance team for review.",
    )
    fake_responses = SimpleNamespace(
        parse=lambda **kwargs: SimpleNamespace(output_parsed=classification)
    )
    openai_classifier = OpenAIClassifier(
        api_key="test-key",
        client=SimpleNamespace(responses=fake_responses),
    )
    monkeypatch.setattr(main_module, "classifier", openai_classifier)

    response = client.post(
        "/intakes",
        json={
            "requester": "Morgan Lee",
            "subject": "Urgent invoice payment",
            "details": "A supplier invoice is blocked.",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["classification"] == classification.model_dump(mode="json")
    assert body["status"] == "awaiting_review"
    assert body["reviewer"] is None
    assert body["review_note"] is None
    assert body["reviewed_at"] is None
