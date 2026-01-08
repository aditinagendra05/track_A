kds_hackathon/
│
├── data/
│   ├── novels/
│   │   ├── story_1.txt
│   │   ├── story_2.txt
│   │
│   ├── backstories/
│   │   ├── story_1_backstory.txt
│   │   ├── story_2_backstory.txt
│
├── pipeline/
│   ├── ingest.py          # Pathway ingestion + chunking
│   ├── retrieval.py       # Vector store + retrieval
│   ├── claims.py          # Backstory → claims
│   ├── reasoning.py       # Claim vs evidence reasoning
│   ├── decision.py        # Aggregation logic
│
├── main.py                # Runs everything
├── requirements.txt
└── results.csv
