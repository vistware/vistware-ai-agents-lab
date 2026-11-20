class Module07Error(Exception):
    """Custom exception for Module 07 errors."""


class KnowledgeIndexError(Module07Error):
    """The embedding index needs to be built or refreshed."""
