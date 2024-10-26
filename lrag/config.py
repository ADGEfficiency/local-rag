import dataclasses
from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ChunkStrategies(str, Enum):
    characters = "characters"
    markdown_objects = "markdown-objects"


class ChunkExtensions(str, Enum):
    file_path = "file_path"
    markdown = "markdown"
    context = "context"


@dataclasses.dataclass
class Defaults:
    embedding_model: str = "snowflake-arctic-embed:335m"
    llm_model: str = "llama3.1:8b"
    max_tokens: int = 3000
    temperature: float = 0.0
    chunk_strategy: ChunkStrategies = ChunkStrategies.characters
    chunk_extensions: tuple[ChunkExtensions, ...] = dataclasses.field(
        default_factory=tuple
    )
    db_fi: str = "db.duckdb"
    n_chunks: int = 10
    generate_response_with_raw_query: bool = False


defaults = Defaults()

__all__ = [
    "ChunkExtensions",
    "ChunkStrategies",
    "LogLevel",
    "defaults",
]
