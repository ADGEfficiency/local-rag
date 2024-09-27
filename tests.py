import os
import pathlib
import tempfile

import duckdb
import pytest
from click.testing import CliRunner

from ingest import main as ingest_cli
from query import main as query_cli


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


DATA = "adam green, bob blue, charlie red"


@pytest.fixture
def dummy_data(temp_dir):
    file_path = pathlib.Path(temp_dir) / "dummy.md"
    file_path.write_text(DATA)
    return file_path


def test_ingest_and_query(
    temp_dir: str,
    dummy_data: pathlib.Path,
    chunk_size: int = 10,
) -> None:
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
            "--embedding-dim",
            384,
        ],
    )
    print(f"{ingest_result.stdout=}")
    assert ingest_result.exit_code == 0

    con = duckdb.connect(db_path)
    result = con.execute("SELECT * FROM embeddings").fetchall()
    con.close()

    assert len(result) > 0
    assert result[0][0] == str(dummy_data)
    assert "content: adam green" in result[0][1]
    assert len(result[0][2]) == 384

    query_result = runner.invoke(
        query_cli,
        [
            "what is adam's last name?",
            "--db",
            db_path,
            "--embedding-model",
            "all-minilm:22m",
            "--embedding-dim",
            "384",
            "--llm",
            "smollm",
        ],
    )
    print(f"{query_result.output=}")
    assert query_result.exit_code == 0
    assert "green" in query_result.output.lower()
