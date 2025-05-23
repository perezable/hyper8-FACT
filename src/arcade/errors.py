"""
Arcade Integration Error Definitions

This module defines custom exceptions for Arcade.dev integration
errors and error handling utilities.
"""

from typing import Optional, Dict, Any
from src.core.errors import FACTError


class ArcadeError(FACTError):
    """Base exception class for all Arcade.dev integration errors."""
    pass


class ArcadeConnectionError(ArcadeError):
    """Raised when connection to Arcade.dev fails."""
    pass


class ArcadeAuthenticationError(ArcadeError):
    """Raised when Arcade.dev authentication fails."""
    pass


class ArcadeExecutionError(ArcadeError):
    """Raised when tool execution on Arcade.dev fails."""
    pass


class ArcadeTimeoutError(ArcadeError):
    """Raised when Arcade.dev operations timeout."""
    pass


class ArcadeRegistrationError(ArcadeError):
    """Raised when tool registration with Arcade.dev fails."""
    pass


class ArcadeSerializationError(ArcadeError):
    """Raised when request/response serialization fails."""
    pass