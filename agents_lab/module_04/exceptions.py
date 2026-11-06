class Module04Error(Exception):
    """Custom exception for Module 04 errors."""


class IncidentInvalidFormatError(Module04Error):
    def __init__(self) -> None:
        super().__init__("Invalid format for incidents. Please check the input data.")
