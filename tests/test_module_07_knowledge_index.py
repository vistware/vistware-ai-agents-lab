import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from typer.testing import CliRunner


@pytest.fixture
def knowledge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test")
    monkeypatch.setenv("AI_MODEL", "openai:gpt-4o-mini")
    monkeypatch.setenv("AI_MODEL_REASONING_EFFORT", "low")

    from agents_lab.module_07.flows import embed_knowledge, parse_knowledge
    from agents_lab.module_07.flows.knowledge_storage import (
        load_embedded_knowledge_index,
        load_parsed_knowledge_files,
    )
    from agents_lab.module_07.main import app
    from agents_lab.module_07.settings import module_settings
    from agents_lab.module_07.tools import semantic_retriever

    source_dir = tmp_path / "knowledge"
    source_dir.mkdir()
    index_path = tmp_path / "embedded.json"
    monkeypatch.setattr(module_settings, "INC_KNOWLEDGE_DIR", source_dir)
    monkeypatch.setattr(
        module_settings, "INC_PARSED_KNOWLEDGE_FILE", tmp_path / "parsed.json"
    )
    monkeypatch.setattr(module_settings, "EMBEDDED_KNOWLEDGE_FILE", index_path)
    monkeypatch.setattr(module_settings, "EMBEDDER_MODEL", "openai:test-model-a")
    client = SimpleNamespace(
        embed_documents=AsyncMock(
            return_value=SimpleNamespace(embeddings=[[1.0, 0.0]])
        ),
        embed_query=AsyncMock(return_value=SimpleNamespace(embeddings=[[1.0, 0.0]])),
    )
    monkeypatch.setattr(embed_knowledge, "embedding_client", client)
    monkeypatch.setattr(semantic_retriever, "embedding_client", client)
    return SimpleNamespace(
        source_dir=source_dir,
        index_path=index_path,
        parse=parse_knowledge.parse_knowledge_flow,
        embed=embed_knowledge.embed_knowledge_flow,
        load_index=load_embedded_knowledge_index,
        load_parsed=load_parsed_knowledge_files,
        search=semantic_retriever.SemanticRetriever().search,
        settings=module_settings,
        client=client,
        app=app,
    )


def test_ingestion_bounds_chunks_and_distinguishes_nested_sources(knowledge) -> None:
    for folder in ("identity", "payments"):
        directory = knowledge.source_dir / folder
        directory.mkdir()
        (directory / "runbook.md").write_text(
            f"# {folder}\n\n## Recovery\n\n"
            + f"{'a' * 700}\n\n{'b' * 700}\n\n{'c' * 2500}",
            encoding="utf-8",
        )

    knowledge.parse()
    files = knowledge.load_parsed()
    assert set(files) == {"identity/runbook.md", "payments/runbook.md"}
    for source_id, file in files.items():
        assert [chunk.content for chunk in file.chunks[:2]] == ["a" * 700, "b" * 700]
        assert "".join(chunk.content for chunk in file.chunks[2:]) == "c" * 2500
        assert all(0 < len(chunk.content) <= 1200 for chunk in file.chunks)
        assert all(chunk.metadata["section"] == "Recovery" for chunk in file.chunks)
        assert [chunk.chunk_id for chunk in file.chunks] == [
            f"{source_id}_{i}" for i in range(len(file.chunks))
        ]
    knowledge.parse()
    assert knowledge.load_parsed() == files


def test_index_sync_removes_stale_chunks_and_reuses_unchanged_vectors(
    knowledge,
) -> None:
    from agents_lab.module_07.exceptions import KnowledgeIndexError

    kept = knowledge.source_dir / "kept.md"
    removed = knowledge.source_dir / "removed.md"
    kept.write_text("# Kept\n\nActive guidance", encoding="utf-8")
    removed.write_text("# Old\n\nOld guidance", encoding="utf-8")
    knowledge.parse()
    asyncio.run(knowledge.embed())
    assert knowledge.client.embed_documents.await_count == 2

    removed.unlink()
    knowledge.parse()
    assert set(knowledge.load_parsed()) == {"kept.md"}
    with pytest.raises(KnowledgeIndexError, match="out of sync"):
        asyncio.run(knowledge.search("guidance"))
    knowledge.client.embed_query.assert_not_awaited()

    asyncio.run(knowledge.embed())
    assert knowledge.client.embed_documents.await_count == 2
    results = asyncio.run(knowledge.search("guidance"))
    assert [result.chunk_id for result in results] == ["kept.md_0"]

    kept.unlink()
    knowledge.parse()
    asyncio.run(knowledge.embed())
    assert knowledge.load_index().chunks == {}
    assert asyncio.run(knowledge.search("guidance")) == []
    assert knowledge.client.embed_query.await_count == 1


def test_index_rebuilds_for_legacy_data_and_same_dimension_model_changes(
    knowledge, monkeypatch: pytest.MonkeyPatch
) -> None:
    from agents_lab.module_07.exceptions import KnowledgeIndexError

    (knowledge.source_dir / "runbook.md").write_text("# Runbook\n\nRecovery steps")
    knowledge.parse()
    knowledge.index_path.write_text(json.dumps({"runbook.md_0": {"embedding": [1, 0]}}))
    with pytest.raises(KnowledgeIndexError, match="predates model metadata"):
        asyncio.run(knowledge.search("recovery"))
    asyncio.run(knowledge.embed())
    assert knowledge.load_index().model == "openai:test-model-a"
    assert knowledge.load_index().dimensions == 2

    monkeypatch.setattr(knowledge.settings, "EMBEDDER_MODEL", "openai:test-model-b")
    with pytest.raises(KnowledgeIndexError, match="different model"):
        asyncio.run(knowledge.search("recovery"))
    knowledge.client.embed_query.assert_not_awaited()
    asyncio.run(knowledge.embed())
    assert knowledge.client.embed_documents.await_count == 2
    assert knowledge.load_index().model == "openai:test-model-b"
    assert asyncio.run(knowledge.search("recovery"))[0].chunk_id == "runbook.md_0"


def test_dimension_mismatch_preserves_index_until_successful_rebuild(knowledge) -> None:
    from agents_lab.module_07.exceptions import KnowledgeIndexError

    runbook = knowledge.source_dir / "runbook.md"
    runbook.write_text("# Runbook\n\nFirst version")
    knowledge.parse()
    asyncio.run(knowledge.embed())
    previous_index = knowledge.index_path.read_bytes()

    new_embedding = SimpleNamespace(embeddings=[[1.0, 0.0, 0.0]])
    knowledge.client.embed_query.return_value = new_embedding
    with pytest.raises(KnowledgeIndexError, match="query embedding dimensions"):
        asyncio.run(knowledge.search("recovery"))

    runbook.write_text("# Runbook\n\nSecond version")
    knowledge.parse()
    knowledge.client.embed_documents.return_value = new_embedding
    with pytest.raises(KnowledgeIndexError, match="unexpected dimensions"):
        asyncio.run(knowledge.embed())
    assert knowledge.index_path.read_bytes() == previous_index

    rebuild = CliRunner().invoke(knowledge.app, ["embed-knowledge", "--rebuild"])
    assert rebuild.exit_code == 0, rebuild.output
    assert knowledge.load_index().dimensions == 3
    assert asyncio.run(knowledge.search("recovery"))[0].content == "Second version"

    corrupted_index = json.loads(knowledge.index_path.read_bytes())
    corrupted_index["chunks"]["runbook.md_0"]["embedding"] = [1.0]
    knowledge.index_path.write_text(json.dumps(corrupted_index))
    with pytest.raises(KnowledgeIndexError, match="index is invalid"):
        asyncio.run(knowledge.search("recovery"))


@pytest.mark.parametrize(
    ("query", "top_k", "message"),
    [
        ("  ", 1, "must not be blank"),
        ("recovery", -1, "between 1 and 5"),
        ("recovery", 6, "between 1 and 5"),
    ],
)
def test_retriever_validates_direct_calls(knowledge, query, top_k, message) -> None:
    with pytest.raises(ValueError, match=message):
        asyncio.run(knowledge.search(query, top_k))
    knowledge.client.embed_query.assert_not_awaited()
