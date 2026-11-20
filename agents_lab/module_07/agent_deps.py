from dataclasses import dataclass

from .tools.semantic_retriever import SemanticRetriever


@dataclass
class IncidentInvestigatorDeps:
    knowledge_retriever: SemanticRetriever
