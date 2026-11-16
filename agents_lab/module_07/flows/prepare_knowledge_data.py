import hashlib
import json
from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path

from langchain_text_splitters import MarkdownHeaderTextSplitter

from agents_lab.utils.time_ import get_current_utc_time

from ..settings import module_settings
from .schemas import (
    ChunkedKnowledgeFile,
    KnowledgeSourceFile,
    ParsedKnowledgeChunk,
    ParsedKnowledgeFile,
)
from .utils import load_parsed_knowledge_files


def compute_file_hash(file_path: Path) -> str:
    """Return the SHA-256 hex digest of a file's contents."""
    digest = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            digest.update(chunk)

    return digest.hexdigest()


@dataclass
class KnowledgeFileScanner:
    knowledge_dir: Path = field(
        default_factory=lambda: module_settings.INC_KNOWLEDGE_DIR
    )

    def scan(self) -> Generator[KnowledgeSourceFile]:
        for file_path in self.knowledge_dir.glob("**/*.md"):
            yield KnowledgeSourceFile(path=file_path, hash=compute_file_hash(file_path))


@dataclass
class MarkdownKnowledgeSplitter:
    file_scanner: KnowledgeFileScanner

    def __post_init__(self) -> None:
        self._splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "title"),
                ("##", "section"),
                ("###", "subsection"),
            ]
        )

    def split_files(self) -> Generator[ChunkedKnowledgeFile]:
        for source_file in self.file_scanner.scan():
            markdown = source_file.path.read_text()
            yield ChunkedKnowledgeFile(
                chunks=self._splitter.split_text(text=markdown),
                source_file=source_file,
            )


@dataclass
class ParsedKnowledgeWriter:
    splitter: MarkdownKnowledgeSplitter

    def __post_init__(self) -> None:
        self._stored_files: dict[str, ParsedKnowledgeFile] = {}

    def _clear_cached_files(self) -> None:
        self._stored_files = {}

    def _load_existing_files(self) -> None:
        self._stored_files = load_parsed_knowledge_files()

    def _save_files(self) -> None:
        module_settings.INC_PARSED_KNOWLEDGE_FILE.parent.mkdir(
            parents=True, exist_ok=True
        )
        serialized_files = {
            key: value.model_dump(mode="json")
            for key, value in self._stored_files.items()
        }
        with module_settings.INC_PARSED_KNOWLEDGE_FILE.open("w") as file:
            json.dump(serialized_files, file, indent=4)

    def update(self) -> None:
        self._load_existing_files()
        for chunked_file in self.splitter.split_files():
            file_path = str(chunked_file.source_file.path)
            file_name = chunked_file.source_file.path.name
            file_hash = chunked_file.source_file.hash
            existing_file = self._stored_files.get(file_name)
            if existing_file and existing_file.hash == file_hash:
                continue
            self._stored_files[file_name] = ParsedKnowledgeFile(
                name=file_name,
                path=file_path,
                hash=file_hash,
                content=[
                    ParsedKnowledgeChunk(
                        content=chunk.page_content,
                        metadata=chunk.metadata,
                        chunk_id=f"{file_name}_{chunk_index}",
                    )
                    for chunk_index, chunk in enumerate(chunked_file.chunks)
                ],
                created_at=get_current_utc_time(),
                is_updated_or_new=True,
            )
        self._save_files()
        self._clear_cached_files()


def prepare_knowledge_data_flow() -> None:
    file_scanner = KnowledgeFileScanner()
    splitter = MarkdownKnowledgeSplitter(file_scanner=file_scanner)
    writer = ParsedKnowledgeWriter(splitter=splitter)
    writer.update()
