from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Optional
from backend.script.layer_score import LayeredScoring

class GuessWord:
    def __init__(
        self, 
        reference_words: List[str], 
        secret_word: str,
        reference_embeddings: Optional[np.ndarray] = None,
        scorer: Optional[LayeredScoring] = None
    ):

        self.reference_words = reference_words
        self.secret_word = secret_word.lower()
        self.scorer = scorer if scorer else LayeredScoring()
        
        if reference_embeddings is not None:
            print("Using pre-computed embeddings")
            self.reference_embeddings = reference_embeddings
        else:
            print("Computing embeddings...")
            self.reference_embeddings = self.scorer.model.encode(
                reference_words, 
                convert_to_numpy=True,
                show_progress_bar=True
            )
        
        self.secret_emb = self.scorer.model.encode([self.secret_word])[0]

        # Pre-calculate scores for all reference words
        self.reference_scores = []
        for i, word in enumerate(reference_words):
            score_data = self.scorer.calculate_score(
                word, 
                self.secret_word,
                secret_emb=self.secret_emb
            )
            self.reference_scores.append((score_data['score'], word))
        
        self.reference_scores.sort(key=lambda x: x[0], reverse=True)
        print(f"✅ Initialized game with secret word '{self.secret_word}'")
    
    def guess(self, word: str) -> Dict:
        word = word.lower().strip()

        if word == self.secret_word:
            return {
                'word': word,
                'score': 1.0,
                'rank': 0,
                'total_words': len(self.reference_words),
                'reasoning': {
                    'semantic': 1.0,
                    'lexical': 1.0,
                    'category': 1.0
                },
                'message': f"Correct! The word was '{self.secret_word}'",
                'won': True
            }
        
        # Calculate score
        score_data = self.scorer.calculate_score(
            word, 
            self.secret_word,
            secret_emb=self.secret_emb
        )
        guess_score = score_data['score']

        rank = 1
        for ref_score, ref_word in self.reference_scores:
            if guess_score < ref_score:
                rank += 1
            else:
                break
        
        return {
            'word': word,
            'score': guess_score,
            'rank': rank,
            'total_words': len(self.reference_words),
            'reasoning': score_data['reasoning'],
            'message': score_data['message'],
            'won': False
        }