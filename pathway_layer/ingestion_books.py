import pathway as pw

books = pw.io.fs.read(
    "../data/books/",
    format="plaintext_by_file"
)

print("Schema:", books.schema)

books = books.select(
    book_id = pw.this.id,
    text = pw.this.data
)

pw.run()
