class Module02Error(Exception):
    """Custom exception for Module 02 errors."""


class ServiceNotFoundError(Module02Error):
    def __init__(self, service: str) -> None:
        super().__init__(f"Service '{service}' not found.")
