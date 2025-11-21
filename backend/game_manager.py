import random
import uuid
from datetime import datetime, date
from typing import List, Dict, Optional, cast
from backend.script.guess import GuessWord
from backend.script.layer_score import LayeredScoring
from backend.database import (
    save_game_session, 
    update_game_session, 
    add_guess_to_session,
    get_game_session
)

class GameManager:
    def __init__(self, reference_words: List[str]):
        self.reference_words = reference_words
        self.scorer = LayeredScoring()
        
        # Cache for active games 
        self.active_games = {}
        
        # Pre-compute embeddings
        self.reference_embeddings = self.scorer.model.encode(
            reference_words,
            convert_to_numpy=True,
            show_progress_bar=True
        )
   
        self.daily_seed = None
        self.daily_word = None
        
        self.easy_words = reference_words[:1000]
        self.medium_words = reference_words[1000:5000]
        self.hard_words = reference_words[5000:]
    
    def get_daily_word(self) -> str:
        today = date.today()
        seed = int(today.strftime('%Y%m%d'))
        if self.daily_seed is None or seed != self.daily_seed:
            random.seed(seed)
            self.daily_word = random.choice(self.reference_words)
            self.daily_seed = seed
            print(f"📅 Daily word for {today}: {self.daily_word}")
        
        return cast(str, self.daily_word)
    
    async def start_new_game(
        self, 
        mode: str = 'practice', 
        difficulty: str = 'medium'
    ) -> Dict:
        """Start a new game and persist to MongoDB"""
        game_id = str(uuid.uuid4())
        today = date.today().isoformat()
        

        if mode == 'daily':
            secret_word = self.get_daily_word()
            message = "📅 Today's Daily Challenge!"
            game_mode = 'daily'
        else:
            if difficulty == 'easy':
                word_pool = self.easy_words
                message = "🟢 Practice Mode - Easy"
            elif difficulty == 'hard':
                word_pool = self.hard_words
                message = "🔴 Practice Mode - Hard"
            else:
                word_pool = self.medium_words
                message = "🟡 Practice Mode - Medium"
            
            secret_word = random.choice(word_pool)
            game_mode = f'practice_{difficulty}'
        

        game = GuessWord(
            reference_words=self.reference_words,
            secret_word=secret_word,
            reference_embeddings=self.reference_embeddings,
            scorer=self.scorer
        )
        

        self.active_games[game_id] = {
            'game': game,
            'mode': game_mode,
            'secret_word': secret_word,
            'started_at': datetime.now().isoformat(),
            'guesses': [],
            'completed_at': None,
            'won': False
        }
        

        session_data = {
            'game_id': game_id,
            'mode': game_mode,
            'date': today,
            'secret_word': secret_word,
            'secret_word_length': len(secret_word),
            'started_at': datetime.now().isoformat(),
            'guesses': [],
            'completed_at': None,
            'won': False,
            'total_guesses': 0
        }
        
        await save_game_session(session_data)
        
        return {
            'game_id': game_id,
            'mode': game_mode,
            'message': message,
            'hint': f'The word has {len(secret_word)} letters',
            'total_words': len(self.reference_words)
        }
    
    async def make_guess(self, game_id: str, word: str) -> Dict:
        if game_id not in self.active_games:
            session = await get_game_session(game_id)
            if not session:
                return {
                    'error': 'Game not found. Please start a new game!',
                    'game_id': None
                }

            game = GuessWord(
                reference_words=self.reference_words,
                secret_word=session['secret_word'],
                reference_embeddings=self.reference_embeddings,
                scorer=self.scorer
            )
            
            self.active_games[game_id] = {
                'game': game,
                'mode': session['mode'],
                'secret_word': session['secret_word'],
                'started_at': session['started_at'],
                'guesses': session['guesses'],
                'completed_at': session.get('completed_at'),
                'won': session.get('won', False)
            }
        
        game_session = self.active_games[game_id]

        if game_session['won']:
            return {
                'error': 'Game already completed!',
                'secret_word': game_session['secret_word'],
                'total_guesses': len(game_session['guesses'])
            }
        

        word_lower = word.lower().strip()
        word_exists = word_lower in self.reference_words
        
        if not word_exists:
            return {
                'error': 'invalid_word',
                'message': f"'{word}' is not in our word list. Try another word!",
                'word': word,
                'game_id': game_id,
                'valid_word': False
            }
        

        result = game_session['game'].guess(word_lower)
        

        guess_record = {
            'word': word_lower,
            'rank': result['rank'],
            'score': result['score'],
            'reasoning': result['reasoning'],
            'timestamp': datetime.now().isoformat()
        }
        
        game_session['guesses'].append(guess_record)
        
        await add_guess_to_session(game_id, guess_record)
        
        if result.get('won', False):
            game_session['won'] = True
            game_session['completed_at'] = datetime.now().isoformat()
            result['total_guesses'] = len(game_session['guesses'])
            result['game_over'] = True
            
            await update_game_session(game_id, {
                'won': True,
                'completed_at': game_session['completed_at'],
                'total_guesses': len(game_session['guesses'])
            })
        
        result['game_id'] = game_id
        result['guess_count'] = len(game_session['guesses'])
        result['valid_word'] = True
        
        return result
    
    async def get_game_stats(self, game_id: str) -> Optional[Dict]:
        if game_id in self.active_games:
            session = self.active_games[game_id]
            return {
                'game_id': game_id,
                'mode': session['mode'],
                'started_at': session['started_at'],
                'completed_at': session['completed_at'],
                'won': session['won'],
                'total_guesses': len(session['guesses']),
                'guess_history': session['guesses'],
                'secret_word': session['secret_word'] if session['won'] else None
            }
        
        return await get_game_session(game_id)