from typing import Union

import transformers
from django.db import models
from django.utils.translation import gettext_lazy as _


class Network(models.Model):
    class Meta:
        verbose_name = _("Network")
        verbose_name_plural = _("Networks")


class ZeroShotClassifier:
    def __init__(self):
        self.classifier = transformers.pipeline(
            "zero-shot-classification", model="facebook/bart-large-mnli"
        )

    def classify(
        self, text: str, labels: list[str]
    ) -> dict[str, Union[list[str], list[float], str]]:
        return self.classifier(text, labels)
