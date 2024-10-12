import dataclasses


@dataclasses.dataclass
class Defaults:
    embedding_model: str = "snowflake-arctic-embed:335m"
    embedding_dim: int = 1024
    llm_model: str = "llama3.1:8b"
    max_tokens: int = 3000
    temperature: float = 0.0


defaults = Defaults()

__all__ = ["defaults"]
