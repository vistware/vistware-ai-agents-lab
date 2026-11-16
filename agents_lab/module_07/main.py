import asyncio

import typer

from agents_lab.module_07.flows.embedding import embed_knowledge_flow
from agents_lab.module_07.flows.prepare_knowledge_data import (
    prepare_knowledge_data_flow,
)

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


if __name__ == "__main__":
    app()
