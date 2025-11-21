from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from backend.game_manager import GameManager
from backend.database import load_reference_words
import os

class AppState:
    def __init__(self):
        self.game_manager: GameManager = None
        self.word_list: List[str] = []

app_state = AppState()

def create_app() -> FastAPI:
    app = FastAPI(
        title="Contexto Game API",
        description="A word guessing game based on semantic similarity with unlimited plays.",
        version="1.0.0",
    )

    @app.on_event("startup")
    def startup_event():
        print("Loading words from MongoDB...")
        word_list, word_embeddings = load_reference_words()
        print(f"✅ Loaded {len(word_list)} words")

        app_state.word_list = [str(w) for w in word_list]
        

        app_state.game_manager = GameManager(
            reference_words=app_state.word_list,
            reference_embeddings=word_embeddings
        )
        print("✅ GameManager initialized")

    return app

app = create_app()

# Response Models
class NewGameResponse(BaseModel):
    game_id: str
    message: str
    hint: str
    mode: str

class GuessRequest(BaseModel):
    game_id: str
    word: str

class GuessResponse(BaseModel):
    word: str
    score: float
    rank: int
    total_words: int
    reasoning: Dict[str, float]
    explanations: List[Dict[str, Any]] = []
    message: str
    won: bool
    total_guesses: Optional[int] = None
    in_reference: Optional[bool] = None
    error: Optional[bool] = None

class GameStatsResponse(BaseModel):
    game_id: str
    total_guesses: int
    started_at: str
    completed_at: Optional[str] = None
    won: bool
    guess_history: List[Dict]

# Routes
@app.get("/")
def read_root():
    return {
        "message": "Welcome to Contexto Game API!",
        "total_words": len(app_state.word_list),
        "active_games": len(app_state.game_manager.active_games) if app_state.game_manager else 0,
        "endpoints": {
            "new_game": "POST /game/new",
            "make_guess": "POST /game/guess",
            "game_stats": "GET /game/{game_id}/stats"
        }
    }

@app.post("/game/new", response_model=NewGameResponse)
def new_game(mode: str = 'practice', difficulty: str = 'medium'):
    """
    Start a new game
    - mode: 'daily' or 'practice' (default: practice)
    - difficulty: 'easy', 'medium', 'hard' (only for practice mode)
    """
    if not app_state.game_manager:
        raise HTTPException(status_code=503, detail="Game manager not initialized")
    
    result = app_state.game_manager.start_new_game(mode=mode, difficulty=difficulty)
    return result

@app.post("/game/guess", response_model=GuessResponse)
def make_guess(request: GuessRequest):
    """Make a guess in an existing game"""
    if not app_state.game_manager:
        raise HTTPException(status_code=503, detail="Game manager not initialized")
    
    result = app_state.game_manager.make_guess(request.game_id, request.word)
    
    if result.get('error'):
        return {
            'word': result.get('word', request.word),
            'score': 0.0,
            'rank': -1,
            'total_words': len(app_state.game_manager.reference_words),
            'reasoning': {},
            'explanations': [],
            'message': result.get('message', 'Invalid guess'),
            'won': False
        }

    
    return result

@app.get("/game/{game_id}/stats", response_model=GameStatsResponse)
def get_game_stats(game_id: str):
    """Get statistics for a specific game"""
    if not app_state.game_manager:
        raise HTTPException(status_code=503, detail="Game manager not initialized")
    
    stats = app_state.game_manager.get_game_stats(game_id)
    
    if 'error' in stats:
        raise HTTPException(status_code=404, detail=stats['error'])
    
    return stats

@app.get("/similar/{word}")
def get_similar_words(word: str, top_k: int = 10):
    """Find words similar to the given word (hint feature)"""
    if not app_state.game_manager:
        raise HTTPException(status_code=503, detail="Game manager not initialized")

    if not app_state.game_manager.active_games:
        raise HTTPException(status_code=400, detail="No active games. Start a game first.")
    
    game_id = list(app_state.game_manager.active_games.keys())[0]
    game = app_state.game_manager.active_games[game_id]['game']
    
    similar_words = game.find_similar_words(word, top_k=top_k)
    return {"word": word, "similar_words": similar_words}

@app.delete("/game/{game_id}")
def delete_game(game_id: str):
    """Delete/end a game session"""
    if not app_state.game_manager:
        raise HTTPException(status_code=503, detail="Game manager not initialized")
    
    if game_id in app_state.game_manager.active_games:
        del app_state.game_manager.active_games[game_id]
        return {"message": f"Game {game_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail="Game not found")