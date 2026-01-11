from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
import logging

from src.config import settings

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for text content"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.embedding_model
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model"""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model {self.model_name}: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * settings.embedding_dimension
        
        try:
            # Generate embedding
            embedding = self.model.encode(text.strip(), convert_to_numpy=True)
            
            # Ensure correct dimension
            if len(embedding) != settings.embedding_dimension:
                logger.warning(f"Embedding dimension mismatch: expected {settings.embedding_dimension}, got {len(embedding)}")
                # Pad or truncate as needed
                if len(embedding) < settings.embedding_dimension:
                    embedding = np.pad(embedding, (0, settings.embedding_dimension - len(embedding)))
                else:
                    embedding = embedding[:settings.embedding_dimension]
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return zero vector on error
            return [0.0] * settings.embedding_dimension
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        
        if not texts:
            return []
        
        try:
            # Filter out empty texts and keep track of indices
            valid_texts = []
            valid_indices = []
            
            for i, text in enumerate(texts):
                if text and text.strip():
                    valid_texts.append(text.strip())
                    valid_indices.append(i)
            
            if not valid_texts:
                # All texts are empty
                return [[0.0] * settings.embedding_dimension] * len(texts)
            
            # Generate embeddings for valid texts
            embeddings = self.model.encode(valid_texts, convert_to_numpy=True)
            
            # Create result array with zero vectors for empty texts
            result = []
            valid_idx = 0
            
            for i in range(len(texts)):
                if i in valid_indices:
                    embedding = embeddings[valid_idx]
                    
                    # Ensure correct dimension
                    if len(embedding) != settings.embedding_dimension:
                        if len(embedding) < settings.embedding_dimension:
                            embedding = np.pad(embedding, (0, settings.embedding_dimension - len(embedding)))
                        else:
                            embedding = embedding[:settings.embedding_dimension]
                    
                    result.append(embedding.tolist())
                    valid_idx += 1
                else:
                    # Empty text, use zero vector
                    result.append([0.0] * settings.embedding_dimension)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            # Return zero vectors on error
            return [[0.0] * settings.embedding_dimension] * len(texts)
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings"""
        
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Compute cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to compute similarity: {e}")
            return 0.0
    
    def find_most_similar(self, 
                         query_embedding: List[float], 
                         candidate_embeddings: List[List[float]], 
                         top_k: int = 5) -> List[tuple]:
        """Find most similar embeddings to query"""
        
        similarities = []
        
        for i, candidate in enumerate(candidate_embeddings):
            similarity = self.compute_similarity(query_embedding, candidate)
            similarities.append((i, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]