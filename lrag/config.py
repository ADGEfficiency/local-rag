import dataclasses
import typing

ChunkStrategies = typing.Literal["characters", "markdown-objects"]
ChunkExtensions = typing.Literal["file_path", "context"]


@dataclasses.dataclass
class Defaults:
    embedding_model: str = "snowflake-arctic-embed:335m"
    llm_model: str = "llama3.1:8b"
    max_tokens: int = 3000
    temperature: float = 0.0
    chunk_strategy: ChunkStrategies = "characters"
    chunk_extensions: tuple[ChunkExtensions, ...] = dataclasses.field(
        default_factory=tuple
    )


defaults = Defaults()

__all__ = ["defaults", "ChunkStrategies"]
