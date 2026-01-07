# track_A
narrative-consistency/
│
├── data/                               # All external data (Pathway reads from here)
│   │
│   ├── books/                          # FULL novels (long context memory)
│   │   ├── the_count_of_monte_cristo.txt
│   │   └── in_search_of_the_castaways.txt
│   │
│   └── splits/                         # Task data (cases to verify)
│       ├── train.csv
│       └── test.csv
│
├── pathway_layer/                      # Pathway is your system backbone
│   ├── ingestion_books.py              # stream novels from data/books/
│   ├── ingestion_cases.py              # stream train.csv & test.csv
│   ├── preprocessing.py                # cleaning + chunking
│   ├── indexing.py                     # embeddings + vector store
│   └── narrative_memory.py             # timeline & character tables
│
├── reasoning/                          # Your intelligence layer
│   ├── claim_extractor.py
│   ├── retriever.py
│   ├── validators.py
│   ├── causal_checker.py
│   └── scorer.py
│
├── rationale/                          # Evidence & dossier builder
│   └── builder.py
│
├── pipelines/
│   └── run_pipeline.py                 # end-to-end system
│
├── outputs/                            # What your system produces
│   ├── predictions.json
│   └── dossiers/
│       └── example.json
│
├── notebooks/                          # optional experiments
│
├── requirements.txt
└── README.md


