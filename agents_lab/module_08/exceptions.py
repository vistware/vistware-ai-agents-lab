class Module08Error(Exception):
    """Base exception for Module 08 errors."""


class KnowledgeIndexError(Module08Error):
    """The knowledge artifacts or query embedding cannot be used for search."""
