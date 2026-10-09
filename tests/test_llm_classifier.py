from types import SimpleNamespace

import pytest

from app.classifier import ClassificationError
from app.llm_classifier import OpenAIClassifier
from app.models import AIClassification, Category, Priority


class FakeResponses:
    def __init__(self, output_parsed=None, error=None):
        self.output_parsed = output_parsed
        self.error = error
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(output_parsed=self.output_parsed)


class FakeOpenAIClient:
    def __init__(self, output_parsed=None, error=None):
        self.responses = FakeResponses(output_parsed=output_parsed, error=error)


def valid_classification():
    return {
        "category": "finance",
        "priority": "high",
        "summary": "Payment is blocked.",
        "recommended_action": "Route to the finance team for review.",
    }


def test_valid_structured_output_becomes_ai_classification():
    client = FakeOpenAIClient(output_parsed=valid_classification())
    classifier = OpenAIClassifier(api_key="test-key", client=client)

    result = classifier("Urgent invoice", "Payment is blocked.")

    assert result == AIClassification(
        category=Category.FINANCE,
        priority=Priority.HIGH,
        summary="Payment is blocked.",
        recommended_action="Route to the finance team for review.",
    )


def test_responses_parse_receives_only_subject_and_details_as_business_input():
    client = FakeOpenAIClient(output_parsed=valid_classification())
    classifier = OpenAIClassifier(api_key="test-key", client=client)

    classifier("Urgent invoice", "Payment is blocked.")

    call = client.responses.calls[0]
    assert call["model"] == "gpt-6-luna"
    assert call["text_format"] is AIClassification
    assert call["input"][1] == {
        "role": "user",
        "content": "Subject:\nUrgent invoice\n\nDetails:\nPayment is blocked.",
    }
    assert "approve" not in call["input"][1]["content"].lower()
    assert "reviewer" not in call["input"][1]["content"].lower()
    assert "status" not in call["input"][1]["content"].lower()


def test_custom_model_is_passed_to_responses_parse():
    client = FakeOpenAIClient(output_parsed=valid_classification())
    classifier = OpenAIClassifier(
        api_key="test-key",
        model="custom-test-model",
        client=client,
    )

    classifier("Subject", "Details")

    assert client.responses.calls[0]["model"] == "custom-test-model"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("category", "legal"),
        ("priority", "critical"),
    ],
)
def test_invalid_enum_output_raises_classification_error(field, value):
    output = valid_classification()
    output[field] = value
    classifier = OpenAIClassifier(
        api_key="test-key",
        client=FakeOpenAIClient(output_parsed=output),
    )

    with pytest.raises(ClassificationError):
        classifier("Subject", "Details")


def test_missing_required_field_raises_classification_error():
    output = valid_classification()
    del output["summary"]
    classifier = OpenAIClassifier(
        api_key="test-key",
        client=FakeOpenAIClient(output_parsed=output),
    )

    with pytest.raises(ClassificationError):
        classifier("Subject", "Details")


@pytest.mark.parametrize("field", ["summary", "recommended_action"])
def test_empty_required_text_field_raises_classification_error(field):
    output = valid_classification()
    output[field] = ""
    classifier = OpenAIClassifier(
        api_key="test-key",
        client=FakeOpenAIClient(output_parsed=output),
    )

    with pytest.raises(ClassificationError):
        classifier("Subject", "Details")


@pytest.mark.parametrize(
    "unexpected_field",
    ["status", "decision", "reviewer", "reviewed_at", "approved", "rejected"],
)
def test_unexpected_field_raises_classification_error(unexpected_field):
    output = valid_classification()
    output[unexpected_field] = "not-allowed"
    classifier = OpenAIClassifier(
        api_key="test-key",
        client=FakeOpenAIClient(output_parsed=output),
    )

    with pytest.raises(ClassificationError):
        classifier("Subject", "Details")


def test_provider_failure_becomes_classification_error():
    classifier = OpenAIClassifier(
        api_key="test-key",
        client=FakeOpenAIClient(error=RuntimeError("provider detail")),
    )

    with pytest.raises(ClassificationError, match="OpenAI classification failed"):
        classifier("Subject", "Details")


def test_refusal_or_missing_parsed_output_becomes_classification_error():
    classifier = OpenAIClassifier(
        api_key="test-key",
        client=FakeOpenAIClient(output_parsed=None),
    )

    with pytest.raises(ClassificationError, match="no parsed classification"):
        classifier("Subject", "Details")
