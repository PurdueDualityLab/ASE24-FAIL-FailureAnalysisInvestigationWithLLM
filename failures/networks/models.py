from typing import Any, Protocol, TypeVar, Union

import sentence_transformers
import transformers
import openai
import os
import logging
import re


from failures.parameters.models import Parameter

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
    def __init__(self, model_name: str = "facebook/bart-large-mnli"):
        self.classifier = transformers.pipeline(
            "zero-shot-classification", model=model_name
        )
        self.max_input_length = self.classifier.model.config.max_position_embeddings

    def preprocess(self, input_data: dict) -> str:
        self.labels = input_data["labels"]
        return input_data["text"][: self.max_input_length]

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



# TODO: expose parameters for summary length
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


class QuestionAnswerer(Network[tuple[str, str], str]):
    def __init__(self, model_name: str = "deepset/tinyroberta-squad2"):
        self.answerer = transformers.pipeline(
            "question-answering", model=model_name, tokenizer=model_name
        )
        self.max_input_length = self.answerer.model.config.max_position_embeddings

    def preprocess(self, input_data: tuple[str, str]) -> dict[str, str]:
        question, context = input_data
        return {
            "question": question[: self.max_input_length],
            "context": context[: self.max_input_length],
        }

    def predict(self, preprocessed_data: dict[str, str]) -> dict[str, str]:
        return self.answerer(preprocessed_data)

    def postprocess(self, prediction: dict[str, str]) -> str:
        return prediction["answer"]


class Embedder(Network[str, list[float]]):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        # TODO: constrain input size
        self.embedder = sentence_transformers.SentenceTransformer(model_name)

    def preprocess(self, input_data: str) -> list[str]:
        return [input_data]

    def predict(self, preprocessed_data: list[str]) -> list[list[float]]:
        return self.embedder.encode(preprocessed_data)

    def postprocess(self, prediction: list[list[float]]) -> list[float]:
        return prediction[0]

class ClassifierChatGPT(Network[list, bool]):
    def __init__(self):

        self.chatGPT = ChatGPT()

    def preprocess(self, input_data: list) -> list:
        return input_data
    
    def predict(self, preprocessed_data: list) -> str:
        messages = preprocessed_data

        response = self.chatGPT.run(messages)

        return response
    
    def postprocess(self, prediction: str) -> bool:
        if "true" in prediction.lower():
            return True
        else:
            return False
    


class SummarizerGPT(Network[str, str]):
    def __init__(self):
        self.openai = openai
        self.openai.api_key = os.getenv('OPENAI_API_KEY')

        self.context = "Provide a summary of this text: \n\n"

    def preprocess(self, input_data: str) -> str:
        prompt = self.context + input_data[:1500] + "\n\n"
        
    def predict(self, preprocessed_data: str) -> str:
        prompt = preprocessed_data

        try:
            response = None
            response = self.openai.Completion.create(
                model="text-babbage-001",
                prompt=prompt,
                max_tokens=300,
            )
        
        except openai.error.Timeout as e:
            #Handle timeout error, e.g. retry or log
            logging.info(f"OpenAI API request timed out: {e}")
        except openai.error.APIError as e:
            #Handle API error, e.g. retry or log
            logging.info(f"OpenAI API returned an API Error: {e}")
        except openai.error.APIConnectionError as e:
            #Handle connection error, e.g. check network or log
            logging.info(f"OpenAI API request failed to connect: {e}")
        except openai.error.InvalidRequestError as e:
            #Handle invalid request error, e.g. validate parameters or log
            logging.info(f"OpenAI API request was invalid: {e}")
        except openai.error.AuthenticationError as e:
            #Handle authentication error, e.g. check credentials or log
            logging.info(f"OpenAI API request was not authorized: {e}")
        except openai.error.PermissionError as e:
            #Handle permission error, e.g. check scope or log
            logging.info(f"OpenAI API request was not permitted: {e}")
        except openai.error.RateLimitError as e:
            #Handle rate limit error, e.g. wait or log
            logging.info(f"OpenAI API request exceeded rate limit: {e}")

        if response is not None:
            summary = response.choices[0]["text"].strip()
            return summary
        else:
            return None

    def postprocess(self, prediction: str) -> str:
        return prediction





class ChatGPT(Network[list, str]):
    def __init__(self):
        self.openai = openai
        self.openai.api_key = os.getenv('OPENAI_API_KEY')

    def preprocess(self, input_data: list) -> list:
        return input_data

    def predict(self, preprocessed_data: list) -> str:
        messages = preprocessed_data
        
        try:
            chat_completion = None
            chat_completion = self.openai.ChatCompletion.create(
                            model="gpt-3.5-turbo", messages=messages, temperature=1 #top_p=1 
                            ) 
        
        except openai.error.Timeout as e:
            #Handle timeout error, e.g. retry or log
            logging.info(f"OpenAI API request timed out: {e}")
        except openai.error.APIError as e:
            #Handle API error, e.g. retry or log
            logging.info(f"OpenAI API returned an API Error: {e}")
        except openai.error.APIConnectionError as e:
            #Handle connection error, e.g. check network or log
            logging.info(f"OpenAI API request failed to connect: {e}")
        except openai.error.InvalidRequestError as e:
            #Handle invalid request error, e.g. validate parameters or log
            logging.info(f"OpenAI API request was invalid: {e}")
        except openai.error.AuthenticationError as e:
            #Handle authentication error, e.g. check credentials or log
            logging.info(f"OpenAI API request was not authorized: {e}")
        except openai.error.PermissionError as e:
            #Handle permission error, e.g. check scope or log
            logging.info(f"OpenAI API request was not permitted: {e}")
        except openai.error.RateLimitError as e:
            #Handle rate limit error, e.g. wait or log
            logging.info(f"OpenAI API request exceeded rate limit: {e}")
        
        if chat_completion is not None:
            reply = chat_completion.choices[0].message.content
            return reply
        else:
            return None
            

    def postprocess(self, prediction: str) -> str:
        return prediction