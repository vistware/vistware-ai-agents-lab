import asyncio
from typing import Annotated

import logfire
import typer
from pydantic_ai.exceptions import UnexpectedModelBehavior

from agents_lab.module_07.agent_deps import IncidentInvestigatorDeps
from agents_lab.module_07.agents import vistware_incident_investigator
from agents_lab.module_07.exceptions import KnowledgeIndexError
from agents_lab.module_07.flows.embed_knowledge import embed_knowledge_flow
from agents_lab.module_07.flows.parse_knowledge import parse_knowledge_flow
from agents_lab.module_07.schemas import IncidentInvestigationAnswer
from agents_lab.module_07.tools.semantic_retriever import (
    DEFAULT_SEARCH_RESULTS,
    SemanticRetriever,
)

app = typer.Typer()


@app.callback()
def main() -> None:
    pass


@app.command("prepare-knowledge-data", hidden=True)
@app.command("parse-knowledge")
def parse_knowledge_command() -> None:
    """Parse Markdown knowledge documents into chunks."""
    parse_knowledge_flow()


@app.command("embed-knowledge")
def embed_knowledge_command(
    rebuild: Annotated[
        bool, typer.Option(help="Regenerate all embedding vectors.")
    ] = False,
) -> None:
    """Synchronize the embedding index with parsed knowledge."""
    try:
        asyncio.run(embed_knowledge_flow(rebuild=rebuild))
    except KnowledgeIndexError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc


@app.command("retrieve-knowledge", hidden=True)
@app.command("search-knowledge")
def search_knowledge_command() -> None:
    """Search the embedded knowledge base for an interactive query."""
    retriever = SemanticRetriever()
    query = typer.prompt("Enter your query")
    top_k = typer.prompt(
        "Enter the number of top results", default=DEFAULT_SEARCH_RESULTS
    )
    try:
        results = asyncio.run(retriever.search(query=query, top_k=top_k))
    except (KnowledgeIndexError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    for result in results:
        typer.echo(f"File: {result.file_name}, Similarity: {result.similarity}")
        typer.echo(f"Content: {result.content}")
        typer.echo(f"Metadata: {result.metadata}")
        typer.echo("-" * 40)


@app.command("analyze-incident", hidden=True)
@app.command("demo-incident-investigator")
def demo_incident_investigator_command() -> None:
    """Run the incident investigator on sample questions."""
    deps = IncidentInvestigatorDeps(knowledge_retriever=SemanticRetriever())
    IncidentInvestigatorDemo(deps).run()


class IncidentInvestigatorDemo:
    def __init__(self, deps: IncidentInvestigatorDeps) -> None:
        self._deps = deps

    def run(self) -> None:
        sample_questions = [
            "Why did authentication fail after the JWT signing key was rotated?",
            "How should operators diagnose delayed payments caused by Kafka consumer lag?",
            "What was the company's revenue in 2025?",
        ]
        for question in sample_questions:
            typer.echo(f"Question: {question}")
            answer = self._investigate_question(question)
            self._print_investigation_answer(answer)
            typer.echo("-" * 40)
            input("Press Enter to continue...")

    def _investigate_question(self, question: str) -> IncidentInvestigationAnswer:
        try:
            result = vistware_incident_investigator.run_sync(
                user_prompt=f"Help user with the following question: {question}",
                deps=self._deps,
            )
        except KnowledgeIndexError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc
        except UnexpectedModelBehavior as exc:
            typer.echo("The agent could not produce a validated answer.", err=True)
            raise typer.Exit(code=1) from exc
        return result.output

    @staticmethod
    def _print_investigation_answer(answer: IncidentInvestigationAnswer) -> None:
        typer.echo(f"Answer: {answer.answer}")
        if answer.knowledge_status == "insufficient":
            typer.echo("Knowledge base: insufficient evidence")
        if answer.chunk_ids:
            typer.echo(f"Sources: {', '.join(answer.chunk_ids)}")


if __name__ == "__main__":
    logfire.configure()
    logfire.instrument_pydantic_ai()
    app()
