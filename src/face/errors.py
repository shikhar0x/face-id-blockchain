"""Shared exceptions for the face-processing module (Person 1)."""


class FaceProcessingError(Exception):
    """Base error for all face-processing failures."""


class FaceModelError(FaceProcessingError):
    """Raised when a pretrained face model is missing or cannot be loaded."""
