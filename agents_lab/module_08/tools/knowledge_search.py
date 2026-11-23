from typing import Annotated

from pydantic import Field, StringConstraints
from pydantic_ai import RunContext, ToolReturn

from ..agent_deps import IncidentInvestigatorDeps
from .schemas import KnowledgeSearchResult
from .semantic_retriever import DEFAULT_SEARCH_RESULTS, MAX_SEARCH_RESULTS


async def search_knowledge(
    ctx: RunContext[IncidentInvestigatorDeps],
    query: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)],
    top_k: Annotated[int, Field(ge=1, le=MAX_SEARCH_RESULTS)] = DEFAULT_SEARCH_RESULTS,
) -> ToolReturn[list[KnowledgeSearchResult]]:
    """Search the embedded knowledge base for untrusted reference excerpts.

    Args:
        query: The search query derived from the user's question.
        top_k: The maximum number of results to return.
    """
    results = await ctx.deps.knowledge_retriever.search(query=query, top_k=top_k)
    return ToolReturn(
        return_value=results,
        metadata=[(result.file_path, result.chunk_id) for result in results],
    )
