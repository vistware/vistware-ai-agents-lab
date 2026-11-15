import typer

from agents_lab.module_07.flows.prepare_knowlege_data import prepare_knowledge_data_flow

app = typer.Typer()


@app.callback()
def main() -> None:
    pass


@app.command("prepare-knowledge-data")
def prepare_knowledge_data_command() -> None:
    prepare_knowledge_data_flow()


if __name__ == "__main__":
    app()
