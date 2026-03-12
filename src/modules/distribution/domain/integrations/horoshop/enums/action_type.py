"""Action type enum for Horoshop."""
from django.db import models


class ActionType(models.TextChoices):
    """Allowed Playwright actions for Horoshop."""
    GOTO = "goto", "Go To URL"
    CLICK = "click", "Click Element"
    HOVER = "hover", "Hover Element"
    FILL = "fill", "Fill Input"
    FILL_IFRAME = "fill_iframe", "Fill IFrame"
    SELECT = "select", "Select Option"
    CHECK = "check", "Check or Uncheck"
    UPLOAD = "upload", "Upload File"
    WAIT_NETWORKIDLE = "wait_networkidle", "Wait for Network Idle"
    WAIT_TIMEOUT = "wait_timeout", "Wait ms"
    FILL_YOUTUBE_IFRAME = "fill_youtube_iframe"
