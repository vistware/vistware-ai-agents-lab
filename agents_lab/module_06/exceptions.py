class Module06Error(Exception):
    """Custom exception for Module 06 errors."""


class InvalidFileFormatError(Module06Error):
    """Exception raised for invalid file format errors."""

    def __init__(self) -> None:
        super().__init__(
            "Invalid file format, permission denied or unreadable. Please contact support."
        )
