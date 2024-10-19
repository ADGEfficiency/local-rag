import dataclasses
import pathlib



@dataclasses.dataclass
class File:
    folder: pathlib.Path
    path: pathlib.Path
    file_content: str = dataclasses.field(repr=False)


@dataclasses.dataclass
class Chunk:
    file: File
    raw_chunk_content: str = dataclasses.field(repr=False)
    chunk_content: str
