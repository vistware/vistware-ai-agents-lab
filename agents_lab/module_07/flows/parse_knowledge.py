import hashlib
from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from agents_lab.utils.time_ import get_current_utc_time

from ..settings import module_settings
from .knowledge_storage import load_parsed_knowledge_files, write_json
from .schemas import (
    KnowledgeSourceFile,
    ParsedKnowledgeChunk,
    ParsedKnowledgeFile,
)

MAX_CHUNK_LENGTH = 1200
CHUNKING_VERSION = 1


@dataclass
class KnowledgeFileScanner:
    knowledge_dir: Path = field(
        default_factory=lambda: module_settings.INC_KNOWLEDGE_DIR
    )

    def scan(self) -> Generator[KnowledgeSourceFile]:
        for file_path in sorted(self.knowledge_dir.rglob("*.md")):
            if not file_path.is_file():
                continue
            contents = file_path.read_bytes()
            yield KnowledgeSourceFile(
                source_id=file_path.relative_to(self.knowledge_dir).as_posix(),
                path=file_path,
                content_hash=hashlib.sha256(contents).hexdigest(),
                markdown=contents.decode("utf-8"),
            )


class MarkdownKnowledgeSplitter:
    def __init__(self) -> None:
        self._header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "title"),
                ("##", "section"),
                ("###", "subsection"),
            ]
        )
        self._length_splitter = RecursiveCharacterTextSplitter(
            chunk_size=MAX_CHUNK_LENGTH,
            chunk_overlap=0,
            # The header splitter joins paragraphs with a Markdown hard break.
            separators=["  \n", "\n\n", "\n", " ", ""],
        )

    def split(self, source: KnowledgeSourceFile) -> list[ParsedKnowledgeChunk]:
        sections = self._header_splitter.split_text(source.markdown)
        return [
            ParsedKnowledgeChunk(
                chunk_id=f"{source.source_id}_{index}",
                content=chunk.page_content,
                metadata=chunk.metadata,
            )
            for index, chunk in enumerate(
                self._length_splitter.split_documents(sections)
            )
        ]


@dataclass
class ParsedKnowledgeWriter:
    scanner: KnowledgeFileScanner
    splitter: MarkdownKnowledgeSplitter

    def update(self) -> None:
        existing_files = load_parsed_knowledge_files()
        parsed_files = {
            source.source_id: self._parse_source(
                source, existing_files.get(source.source_id)
            )
            for source in self.scanner.scan()
        }
        write_json(
            module_settings.INC_PARSED_KNOWLEDGE_FILE,
            {
                source_id: file.model_dump(mode="json")
                for source_id, file in parsed_files.items()
            },
        )

    def _parse_source(
        self, source: KnowledgeSourceFile, existing: ParsedKnowledgeFile | None
    ) -> ParsedKnowledgeFile:
        path = str(source.path)
        if (
            existing
            and existing.content_hash == source.content_hash
            and existing.chunking_version == CHUNKING_VERSION
            and existing.path == path
        ):
            return existing

        return ParsedKnowledgeFile(
            name=source.path.name,
            path=path,
            content_hash=source.content_hash,
            chunks=self.splitter.split(source),
            created_at=get_current_utc_time(),
            chunking_version=CHUNKING_VERSION,
        )


def parse_knowledge_flow() -> None:
    writer = ParsedKnowledgeWriter(
        scanner=KnowledgeFileScanner(), splitter=MarkdownKnowledgeSplitter()
    )
    writer.update()
