import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class PathConfig(BaseModel):
    """Path configuration"""
    root: Path = Path(__file__).parent
    data: Path = root / "data"
    books: Path = data / "books"
    splits: Path = data / "splits"
    outputs: Path = root / "outputs"
    dossiers: Path = outputs / "dossiers"
    vector_store: Path = root / "vector_store"
    pathway_cache: Path = root / "pathway_cache"

class ModelConfig(BaseModel):
    """Model configuration"""
    llm_model: str = os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

class ProcessingConfig(BaseModel):
    """Processing configuration"""
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "500"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    top_k_retrieval: int = int(os.getenv("TOP_K_RETRIEVAL", "10"))
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))

class Config(BaseModel):
    """Global configuration"""
    paths: PathConfig = PathConfig()
    models: ModelConfig = ModelConfig()
    processing: ProcessingConfig = ProcessingConfig()

# Global config instance
config = Config()

# Create necessary directories
config.paths.outputs.mkdir(exist_ok=True)
config.paths.dossiers.mkdir(exist_ok=True)
config.paths.vector_store.mkdir(exist_ok=True)
config.paths.pathway_cache.mkdir(exist_ok=True)