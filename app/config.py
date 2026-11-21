"""Backward-compatible settings import.

The canonical application settings live in app.core.config.
"""
from app.core.config import Settings, settings

__all__ = ["Settings", "settings"]
