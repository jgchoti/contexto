import random
import uuid
from datetime import datetime, date
from typing import List, Dict
import numpy as np
from script.guess import GuessWord
from script.layer_score import LayeredScoring

class GameManager:
    def __init__(self, reference_words: List[str], reference_embeddings: np.ndarray):
        self.reference_words = reference_words
        self.reference_embeddings = reference_embeddings
        self.active_games = {}
        self.scorer = LayeredScoring()
        self.easy_words = reference_words[:1000]
        self.medium_words = reference_words[1000:3000]
        self.hard_words = reference_words[3000:]
        self.daily_seed = None
        self.daily_word = None
        
        print(f"✅ GameManager ready with {len(reference_words)} words")
    
    def get_daily_word(self) -> str:
        """Get consistent daily word for all players"""
        today = date.today()
        seed = int(today.strftime('%Y%m%d'))
        
        if seed != self.daily_seed:
            random.seed(seed)
            self.daily_word = random.choice(self.medium_words)  # Daily = medium difficulty
            self.daily_seed = seed
            print(f"📅 Daily word updated: {len(self.daily_word)} letters")
        
        return self.daily_word
    
    def start_new_game(self, mode: str = 'practice', difficulty: str = 'medium') -> Dict:
        """
        mode: 'daily' or 'practice'
        difficulty: 'easy', 'medium', 'hard' (only for practice)
        """
        game_id = str(uuid.uuid4())

        if mode == 'daily':
            secret_word = self.get_daily_word()
            message = "Today's daily challenge!"
        else:

            if difficulty == 'easy':
                word_pool = self.easy_words
            elif difficulty == 'hard':
                word_pool = self.hard_words
            else:
                word_pool = self.medium_words
            
            secret_word = random.choice(word_pool)
            message = f"Practice mode - {difficulty} difficulty"
        
      
        game = GuessWord(
            reference_words=self.reference_words,
            secret_word=secret_word,
            reference_embeddings=self.reference_embeddings,
            scorer=self.scorer 
        )
        
        # Store game session
        self.active_games[game_id] = {
            'game': game,
            'mode': mode,
            'difficulty': difficulty,
            'started_at': datetime.now(),
            'completed_at': None,
            'guesses': [],
            'won': False
        }
        
        return {
            'game_id': game_id,
            'message': message,
            'hint': f'The word has {len(secret_word)} letters',
            'mode': mode
        }
    
    def make_guess(self, game_id: str, word: str) -> Dict:
        """Make a guess in an existing game"""
        if game_id not in self.active_games:
            return {'error': 'Game not found. Start a new game!'}
        
        game_session = self.active_games[game_id]
        
        if game_session['won']:
            return {
                'error': 'Game already completed!',
                'total_guesses': len(game_session['guesses'])
            }
        
        # Make the guess
        result = game_session['game'].guess(word)
        
        # Track guess
        game_session['guesses'].append({
            'word': word,
            'rank': result['rank'],
            'score': result['score'],
            'timestamp': datetime.now().isoformat()
        })
        
        # Check if won
        if result['rank'] == 0:
            game_session['won'] = True
            game_session['completed_at'] = datetime.now()
            result['total_guesses'] = len(game_session['guesses'])
        
        return result
    
    def get_game_stats(self, game_id: str) -> Dict:
        """Get statistics for a game"""
        if game_id not in self.active_games:
            return {'error': 'Game not found'}
        
        session = self.active_games[game_id]
        
        return {
            'game_id': game_id,
            'mode': session['mode'],
            'difficulty': session.get('difficulty', 'N/A'),
            'total_guesses': len(session['guesses']),
            'started_at': session['started_at'].isoformat(),
            'completed_at': session['completed_at'].isoformat() if session['completed_at'] else None,
            'won': session['won'],
            'guess_history': session['guesses']
        }