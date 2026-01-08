import pathway as pw
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
from loguru import logger
from config import config
import numpy as np

class VectorIndexer:
    """Create and manage vector embeddings for semantic search"""
    
    def __init__(self):
        self.embedding_model_name = config.models.embedding_model
        self.vector_store_path = config.paths.vector_store
        self.top_k = config.processing.top_k_retrieval
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        
        # Initialize vector store
        self.client = chromadb.PersistentClient(
            path=str(self.vector_store_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.client.get_or_create_collection(
            name="narrative_chunks",
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.success("Vector indexer initialized")
    
    def index_chunks(self, chunks_table: pw.Table) -> None:
        """
        Create embeddings and index chunks
        
        Args:
            chunks_table: Table with book_id, chunk_id, chunk_text
        """
        logger.info("Creating embeddings and indexing chunks")
        
        # Convert Pathway table to list for processing
        chunks_data = []
        
        # Process in batches for efficiency
        batch_size = 32
        batch_texts = []
        batch_ids = []
        batch_metadatas = []
        
        for row in chunks_table:
            chunk_id = row['chunk_id']
            chunk_text = row['chunk_text']
            book_id = row['book_id']
            title = row.get('title', '')
            
            batch_texts.append(chunk_text)
            batch_ids.append(chunk_id)
            batch_metadatas.append({
                'book_id': book_id,
                'title': title,
                'text': chunk_text
            })
            
            # Process batch when full
            if len(batch_texts) >= batch_size:
                self._index_batch(batch_texts, batch_ids, batch_metadatas)
                batch_texts = []
                batch_ids = []
                batch_metadatas = []
        
        # Process remaining items
        if batch_texts:
            self._index_batch(batch_texts, batch_ids, batch_metadatas)
        
        logger.success(f"Indexed chunks in vector store")
    
    def _index_batch(self, texts: List[str], ids: List[str], metadatas: List[Dict]) -> None:
        """Index a batch of chunks"""
        try:
            # Generate embeddings
            embeddings = self.embedding_model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=texts,
                ids=ids,
                metadatas=metadatas
            )
            
            logger.debug(f"Indexed batch of {len(texts)} chunks")
            
        except Exception as e:
            logger.error(f"Error indexing batch: {e}")
    
    def search(self, query: str, book_id: str = None, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks
        
        Args:
            query: Search query
            book_id: Optional filter by book
            top_k: Number of results to return
            
        Returns:
            List of dicts with chunk_id, text, book_id, relevance_score
        """
        if top_k is None:
            top_k = self.top_k
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(
            [query],
            convert_to_numpy=True
        )[0]
        
        # Build where filter
        where_filter = {}
        if book_id:
            where_filter = {"book_id": book_id}
        
        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=where_filter if where_filter else None
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'chunk_id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'book_id': results['metadatas'][0][i].get('book_id', ''),
                    'title': results['metadatas'][0][i].get('title', ''),
                    'relevance_score': 1 - results['distances'][0][i]  # Convert distance to similarity
                })
        
        logger.debug(f"Found {len(formatted_results)} results for query")
        return formatted_results
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the indexed collection"""
        count = self.collection.count()
        return {
            'total_chunks': count,
            'embedding_dim': self.embedding_model.get_sentence_embedding_dimension()
        }