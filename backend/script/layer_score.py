from sentence_transformers import SentenceTransformer
from Levenshtein import distance as levenshtein_distance
from nltk.corpus import wordnet as wn
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class LayeredScoring:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def semantic_similarity(self, word1, word2, emb1=None, emb2=None):
        if emb1 is None:
            emb1 = self.model.encode([word1])[0]
        if emb2 is None:
            emb2 = self.model.encode([word2])[0]
        
        similarity = cosine_similarity(
            emb1.reshape(1, -1),
            emb2.reshape(1, -1)
        )[0][0]
        
        return float(similarity)
    
    def lexical_similarity(self, word1, word2):
        max_len = max(len(word1), len(word2))
        if max_len == 0:
            return 1.0
        
        edit_dist = levenshtein_distance(word1.lower(), word2.lower())
        normalized = 1 - (edit_dist / max_len)
        
        return max(0.0, normalized)
    
    def category_match(self, word1, word2):
        """Layer 3: WordNet category consistency (10%)"""
        try:
            synsets1 = wn.synsets(word1)
            synsets2 = wn.synsets(word2)
            
            if not synsets1 or not synsets2:
                return 0.5  
            
            pos1 = set([s.pos() for s in synsets1])
            pos2 = set([s.pos() for s in synsets2])
            
            if pos1 & pos2:
                return 1.0
            else:
                return 0.0
                
        except Exception:
            return 0.5  
    
    def calculate_score(self, guess_word, secret_word, secret_emb=None):
        """
        Weights:
        - Semantic: 70%
        - Lexical: 20%
        - Category: 10%
        """
        
        semantic = self.semantic_similarity(guess_word, secret_word, emb2=secret_emb)
        lexical = self.lexical_similarity(guess_word, secret_word)
        category = self.category_match(guess_word, secret_word)
        
        # Weighted combination
        final_score = (
            semantic * 0.7 +
            lexical * 0.2 +
            category * 0.1
        )
        

        message = self.generate_message(semantic, lexical, category)
        
        return {
            'score': round(final_score, 4),
            'reasoning': {
                'semantic': round(semantic, 2),
                'lexical': round(lexical, 2),
                'category': round(category, 2)
            },
            'message': message
        }
    
    def generate_message(self, semantic, lexical, category):
        if semantic > 0.8:
            if category == 1.0:
                return "Very close in meaning and same word type! 🔥"
            return "Semantically very close!"
        
        if semantic > 0.5 and lexical > 0.8:
            return "Similar spelling, somewhat related meaning"
        
        if lexical > 0.8 and semantic < 0.5:
            return "Similar spelling but different meaning"
        
        if category == 1.0 and semantic < 0.5:
            return "Same type of word, but different topic"
        
        if semantic < 0.3:
            return "Pretty far off in meaning"
        
        return "Getting warmer..."