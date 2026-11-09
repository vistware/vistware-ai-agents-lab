class Module05Error(Exception):
    """Custom exception for Module 05 errors."""


class InvalidFileFormatError(Module05Error):
    """Exception raised for invalid file format errors."""

    def __init__(self) -> None:
        super().__init__(
            "Invalid file format, permission denied or unreadable. Please contact support."
        )
