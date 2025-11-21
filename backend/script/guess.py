from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Optional
from backend.script.layer_score import LayeredScoring
import faiss

class GuessWord:
    def __init__(
        self,
        reference_words: List[str],
        secret_word: str,
        reference_embeddings: Optional[np.ndarray] = None,
        scorer: Optional[LayeredScoring] = None,
        use_cosine: bool = True
    ):
        self.reference_words = reference_words
        self.secret_word = secret_word.lower()
        self.scorer = scorer if scorer else LayeredScoring()
        self.use_cosine = use_cosine

        if reference_embeddings is not None:
            print("Using pre-computed embeddings")
            self.reference_embeddings = reference_embeddings.astype('float32')
        else:
            print("Computing embeddings...")
            self.reference_embeddings = self.scorer.model.encode(
                reference_words,
                convert_to_numpy=True,
                show_progress_bar=True
            ).astype('float32')

        if self.use_cosine:
            faiss.normalize_L2(self.reference_embeddings)

        # Secret word embedding
        self.secret_emb = self.scorer.model.encode([self.secret_word])[0].astype('float32')
        if self.use_cosine:
            self.secret_emb /= np.linalg.norm(self.secret_emb)

        # Pre-calculate reference scores for ranking
        print("Pre-calculating scores for ranking... (this may take a moment)")
        self.reference_scores = np.array([
            self.scorer.calculate_score(
                word,
                self.secret_word,
                guess_emb=ref_emb,
                secret_emb=self.secret_emb
            )['score']
            for word, ref_emb in zip(self.reference_words, self.reference_embeddings)
        ])
        print("Score pre-calculation complete.")
        self.sorted_indices = np.argsort(-self.reference_scores)
        self.sorted_scores = self.reference_scores[self.sorted_indices]
        
        print(f"✅ Initialized game with secret word '{self.secret_word}'")

        dimension = self.reference_embeddings.shape[1]
        if self.use_cosine:
            self.index = faiss.IndexFlatIP(dimension)
        else:
            self.index = faiss.IndexFlatL2(dimension)
        self.index.add(self.reference_embeddings)
        print(f"✅ FAISS index built with {len(reference_words)} vectors")

    def guess(self, word: str) -> Dict:
        word = word.lower().strip()

        if word == self.secret_word:
            return {
                'word': word,
                'score': 1.0,
                'rank': 0,
                'total_words': len(self.reference_words),
                'reasoning': {'semantic': 1.0, 'lexical': 1.0, 'category': 1.0},
                'message': f"Correct! The word was '{self.secret_word}'",
                'won': True
            }

        score_data = self.scorer.calculate_score(word, self.secret_word, secret_emb=self.secret_emb)
        guess_score = score_data['score']

        rank = int(np.searchsorted(-self.sorted_scores, -guess_score)) + 1

        return {
            'word': word,
            'score': guess_score,
            'rank': rank,
            'total_words': len(self.reference_words),
            'reasoning': score_data['reasoning'],
            'explanations': score_data['explanations'],
            'message': score_data['message'],
            'won': False
        }

    def find_similar_words(self, word: str, top_k: int = 10) -> List[Dict]:
        word_emb = self.scorer.model.encode([word])[0].astype('float32')
        if self.use_cosine:
            word_emb /= np.linalg.norm(word_emb)
        word_emb = np.expand_dims(word_emb, axis=0)

        distances, indices = self.index.search(word_emb, top_k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if self.use_cosine:
                results.append({
                    "word": self.reference_words[idx],
                    "similarity": float(dist)
                })
            else:
                results.append({
                    "word": self.reference_words[idx],
                    "distance": float(dist)
                })
        return results
