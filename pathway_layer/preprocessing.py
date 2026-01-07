import pathway as pw
import re

# ---------- Load full books ----------
books = pw.io.fs.read(
    "../data/books/",
    format="plaintext_by_file"
)

books = books.select(
    book_id = pw.this.id,
    text = pw.this.data
)

# ---------- Basic cleaning ----------
def clean_text(t: str) -> str:
    t = re.sub(r"\s+", " ", t)
    return t.strip()

books = books.select(
    book_id = pw.this.book_id,
    clean_text = pw.apply(clean_text, pw.this.text)
)

# ---------- Chunking ----------
def chunk_text(text, chunk_size=1200, overlap=200):
    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks

chunks = books.select(
    book_id = pw.this.book_id,
    chunk = pw.apply(chunk_text, pw.this.clean_text)
).flatten(pw.this.chunk)

# ---------- Assign chunk ids ----------
chunks = chunks.with_columns(
    chunk_id = pw.this.id
)

# ---------- Output to memory / console ----------
pw.debug.compute_and_print(chunks, include_id=False)

pw.run()
