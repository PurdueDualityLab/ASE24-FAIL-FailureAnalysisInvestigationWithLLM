from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class ChainlitThread(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    created_at = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=255, blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chainlit_threads",
        blank=True,
        null=True
    )
    metadata = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name = _("Chat Thread")
        verbose_name_plural = _("Chat Threads")
        ordering = ["-created_at"]

    def __str__(self):
        return self.name or self.id

class ChainlitStep(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    thread = models.ForeignKey(
        ChainlitThread,
        on_delete=models.CASCADE,
        related_name="steps"
    )
    parent_id = models.CharField(max_length=255, blank=True, null=True)
    disable_feedback = models.BooleanField(default=False)
    streaming = models.BooleanField(default=False)
    input = models.TextField(blank=True, null=True)
    output = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    generation = models.JSONField(default=dict, blank=True, null=True)
    show_input = models.BooleanField(default=True)
    language = models.CharField(max_length=255, blank=True, null=True)
    indent = models.IntegerField(default=0)

    class Meta:
        verbose_name = _("Chat Step")
        verbose_name_plural = _("Chat Steps")
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.name} ({self.type})"

class ChainlitElement(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    thread = models.ForeignKey(
        ChainlitThread,
        on_delete=models.CASCADE,
        related_name="elements"
    )
    type = models.CharField(max_length=255)
    url = models.CharField(max_length=2048, blank=True, null=True)
    chainlit_key = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255)
    display = models.CharField(max_length=255)
    size = models.CharField(max_length=255, blank=True, null=True)
    language = models.CharField(max_length=255, blank=True, null=True)
    page = models.IntegerField(blank=True, null=True)
    props = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("Chat Element")
        verbose_name_plural = _("Chat Elements")

    def __str__(self):
        return self.name

class ChainlitFeedback(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    for_id = models.CharField(max_length=255) # ID of the step this feedback is for
    value = models.IntegerField() # 1 for positive, 0 for negative (or -1)
    comment = models.TextField(blank=True, null=True)
    
    # Optional: link to step if you want to enforce referential integrity, 
    # but Chainlit sometimes sends feedback for IDs not yet fully persisted if async is slow.
    # We will just store the ID string for flexibility or link it if possible.
    # To keep it strict, let's link it but allow null if not found.
    step = models.ForeignKey(
        ChainlitStep,
        on_delete=models.CASCADE,
        related_name="feedbacks",
        blank=True, 
        null=True
    )

    class Meta:
        verbose_name = _("Chat Feedback")
        verbose_name_plural = _("Chat Feedbacks")

    def __str__(self):
        return f"Feedback for {self.for_id}: {self.value}"
