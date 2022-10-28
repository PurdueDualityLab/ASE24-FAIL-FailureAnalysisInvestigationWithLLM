from typing import Any, Protocol, TypeVar, Union

import transformers

T = TypeVar("T")
E = TypeVar("E")


class Network(Protocol[T, E]):
    def preprocess(self, input_data: T) -> Any:
        ...

    def predict(self, preprocessed_data: Any) -> Any:
        ...

    def postprocess(self, prediction: Any) -> E:
        ...

    def run(self, input_data: T) -> E:
        preprocessed_data = self.preprocess(input_data)
        prediction = self.predict(preprocessed_data)
        return self.postprocess(prediction)


class ZeroShotClassifier(Network[str, tuple[str, float]]):
    def __init__(self, labels: list[str], model_name: str = "facebook/bart-large-mnli"):
        self.classifier = transformers.pipeline(
            "zero-shot-classification", model=model_name
        )
        self.max_input_length = self.classifier.model.config.max_position_embeddings
        self.labels = labels

    def preprocess(self, input_data: str) -> str:
        return input_data[: self.max_input_length]

    def predict(
        self, preprocessed_data: str
    ) -> dict[str, Union[list[str], list[float], str]]:
        return self.classifier(preprocessed_data, self.labels)

    def postprocess(
        self, prediction: dict[str, Union[list[str], list[float], str]]
    ) -> tuple[str, float]:
        scores: list[float] = prediction["scores"]
        max_score: float = max(scores)
        return prediction["labels"][scores.index(max_score)], max_score


class Summarizer(Network[str, str]):
    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        self.summarizer = transformers.pipeline("summarization", model=model_name)
        self.max_input_length = self.summarizer.model.config.max_position_embeddings

    def preprocess(self, input_data: str) -> str:
        return input_data[: self.max_input_length]

    def predict(self, preprocessed_data: str) -> list[dict[str, str]]:
        return self.summarizer(preprocessed_data)

    def postprocess(self, prediction: list[dict[str, str]]) -> str:
        return prediction[0]["summary_text"]
