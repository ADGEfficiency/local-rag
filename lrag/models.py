import dataclasses
import pathlib


@dataclasses.dataclass
class File:
    path: pathlib.Path
    file_content: str


@dataclasses.dataclass
class Chunk:
    file: File
    chunk_content: str
