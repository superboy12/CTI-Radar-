"""
Custom exception classes for the CTI platform.
"""
from typing import Optional


class CTIException(Exception):
    """Base exception for the CTI platform."""
    def __init__(self, message: str, status_code: int = 500, details: Optional[dict] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(CTIException):
    """Resource not found."""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            status_code=404,
            details={"resource": resource, "identifier": identifier},
        )


class DuplicateError(CTIException):
    """Resource already exists."""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} already exists: {identifier}",
            status_code=409,
            details={"resource": resource, "identifier": identifier},
        )


class AuthenticationError(CTIException):
    """Authentication failed."""
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message=message, status_code=401)


class AuthorizationError(CTIException):
    """Insufficient permissions."""
    def __init__(self, required_role: str = ""):
        message = "Insufficient permissions"
        if required_role:
            message += f". Required role: {required_role}"
        super().__init__(message=message, status_code=403)


class ValidationError(CTIException):
    """Input validation failed."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message=message, status_code=422, details=details)


class RateLimitError(CTIException):
    """Rate limit exceeded."""
    def __init__(self):
        super().__init__(message="Rate limit exceeded. Please try again later.", status_code=429)
