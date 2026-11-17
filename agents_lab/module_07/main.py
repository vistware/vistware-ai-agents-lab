import asyncio

import typer

from agents_lab.module_07.flows.embedding import embed_knowledge_flow
from agents_lab.module_07.flows.prepare_knowledge_data import (
    prepare_knowledge_data_flow,
)
from agents_lab.module_07.tools.semantic_retriever import SemanticRetriever

app = typer.Typer()


@app.callback()
def main() -> None:
    pass


@app.command("prepare-knowledge-data")
def prepare_knowledge_data_command() -> None:
    prepare_knowledge_data_flow()


@app.command("embed-knowledge")
def embed_knowledge_command() -> None:
    asyncio.run(embed_knowledge_flow())


@app.command("retrieve-knowledge")
def retrieve_knowledge_command() -> None:
    retriever = SemanticRetriever()
    query = typer.prompt("Enter your query")
    top_k = typer.prompt("Enter the number of top results", type=int)
    results = asyncio.run(retriever.retrieve(query=query, top_k=top_k))
    for result in results:
        typer.echo(f"File: {result.file_name}, Similarity: {result.similarity}")
        typer.echo(f"Content: {result.content}")
        typer.echo(f"Metadata: {result.metadata}")
        typer.echo("-" * 40)


if __name__ == "__main__":
    app()
