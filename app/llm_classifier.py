from typing import Any

from pydantic import ValidationError

from app.classifier import ClassificationError
from app.models import AIClassification


SYSTEM_INSTRUCTION = """Classify the supplied business request and recommend the next business action.
Return only the requested classification fields. Do not approve or reject the request, and do not
make or recommend any workflow state change. A human reviewer makes the final decision."""


def _create_openai_client(api_key: str) -> Any:
    from openai import OpenAI

    return OpenAI(api_key=api_key)


class OpenAIClassifier:
    """Return structured classification advice from the OpenAI Responses API."""

    def __init__(self, api_key: str, model: str = "gpt-6-luna", client: Any = None) -> None:
        self.model = model
        self._client = client if client is not None else _create_openai_client(api_key)

    def __call__(self, subject: str, details: str) -> AIClassification:
        try:
            response = self._client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {
                        "role": "user",
                        "content": f"Subject:\n{subject}\n\nDetails:\n{details}",
                    },
                ],
                text_format=AIClassification,
            )
            parsed = response.output_parsed
            if parsed is None:
                raise ClassificationError("OpenAI returned no parsed classification")
            return AIClassification.model_validate(parsed)
        except ClassificationError:
            raise
        except ValidationError as exc:
            raise ClassificationError("OpenAI returned invalid classification") from exc
        except Exception as exc:
            raise ClassificationError("OpenAI classification failed") from exc
