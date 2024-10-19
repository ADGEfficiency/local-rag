import os
import pathlib
import tempfile
import typing

import duckdb
import pytest

from lrag.ingest import app as ingest_cli
from lrag.query import query as query_cli

# from click.testing import CliRunner


TEST_DATA = "adam green, bob blue, charlie red"


@pytest.fixture
def temp_dir() -> typing.Generator[str, None, None]:
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture
def dummy_md_fi(temp_dir: str) -> pathlib.Path:
    file_path = pathlib.Path(temp_dir) / "dummy.md"
    file_path.write_text(TEST_DATA)
    return file_path


def test_ingest_and_query(
    temp_dir: str,
    dummy_md_fi: pathlib.Path,
    chunk_size: int = 10,
) -> None:
    from typer.testing import CliRunner

    runner = CliRunner()
    db_path = os.path.join(temp_dir, "test_db2.duckdb")

    ingest_result = runner.invoke(
        ingest_cli,
        [
            temp_dir,
            "--chunk-size",
            str(chunk_size),
            "--overlap",
            "0.1",
            "--db",
            db_path,
            "--glob",
            "*.md",
            "--embedding-model",
            "all-minilm:22m",
        ],
    )
    print(f"{ingest_result.stdout=}")
    assert ingest_result.exit_code == 0

    with duckdb.connect(db_path) as con:
        result = con.execute(
            "SELECT document_fi, chunk, vector FROM embeddings"
        ).fetchall()

    # check expected number of chunks
    assert len(result) == 4
    # check file name
    assert os.path.samefile(result[0][0], str(dummy_md_fi))
    # check chunk
    assert "chunk: adam green" in result[0][1]
    # check embedding dimension
    assert len(result[0][2]) == 384

    # query_result = runner.invoke(
    #     query_cli,
    #     [
    #         "what is adam's last name?",
    #         "--db",
    #         db_path,
    #         "--embedding-model",
    #         "all-minilm:22m",
    #         "--llm",
    #         "smollm",
    #     ],
    # )
    # print(f"{query_result.output=}")
    # assert query_result.exit_code == 0
    # assert "green" in query_result.output.lower()
