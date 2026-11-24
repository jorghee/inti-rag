"""Domain exceptions for data access repositories."""


class RepositoryError(Exception):
    """Base error raised by repository implementations."""


class StorageUnavailableError(RepositoryError):
    """Raised when Supabase or an external persistence backend cannot be reached."""


class ResourceNotFoundError(RepositoryError):
    """Raised when a requested record does not exist."""


class ForbiddenAccessError(RepositoryError):
    """Raised when a user attempts to access a record owned by another user."""
