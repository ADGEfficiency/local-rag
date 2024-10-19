import duckdb

db_fi = "bm25.duckdb"
con = duckdb.connect(db_fi)
con.execute("install fts; load fts;")
con.execute(
    """
    DROP TABLE IF EXISTS docs;
    DROP SEQUENCE IF EXISTS seq_document_id;
    CREATE SEQUENCE IF NOT EXISTS seq_document_id START 1;
    CREATE TABLE docs (
        document_id INTEGER PRIMARY KEY DEFAULT nextval('seq_document_id'),
        text_content VARCHAR
    );
    """
)

docs = [
    "The mallard is a dabbling duck that breeds throughout the temperate.",
    "The cat is a domestic species of small carnivorous mammal.",
]
for doc in docs:
    con.execute("INSERT INTO docs VALUES (DEFAULT, ?)", [doc])

con.execute("""
    PRAGMA create_fts_index('docs', 'document_id', 'text_content', overwrite=true);
""")

print(con.execute("SELECT * FROM docs").fetchall())
print(
    con.execute(
        """
    SELECT *, fts_main_docs.match_bm25(document_id, 'mallard duck') AS score
    FROM docs
    """
    ).fetchall()
)
