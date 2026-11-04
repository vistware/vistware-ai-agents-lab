class Module03Error(Exception):
    """Custom exception for Module 03 errors."""


class ServicePermissionDeniedError(Module03Error):
    def __init__(self, service: str) -> None:
        super().__init__(f"Permission denied for service '{service}'.")
