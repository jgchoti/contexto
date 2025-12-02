from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import threading
from .game_manager import GameManager
from .script.guess import GuessWord
from .database import load_reference_words
import os
class AppState:
    def __init__(self):
        self.game_manager: Optional[GameManager] = None
        self.word_list: List[str] = []
        self._initialized = False
        self._lock = threading.Lock()

app_state = AppState()

def lazy_init():
    """Load embeddings only once, on first request (solves OOM on Vercel)"""
    if app_state._initialized:
        return

    with app_state._lock:
        if app_state._initialized:
            return

        print("First request! Loading 30k+ word embeddings from MongoDB... (this takes ~10s, one-time only)")
        word_list, word_embeddings = load_reference_words()
        print(f"Successfully loaded {len(word_list)} words")

        app_state.word_list = [str(w) for w in word_list]
        app_state.game_manager = GameManager(
            reference_words=app_state.word_list,
            reference_embeddings=word_embeddings
        )
        app_state._initialized = True
        print("Game engine HOT and ready! All future requests = instant")

app = FastAPI(
    title="Contexto Unlimited API",
    description="Pink & yellow summer edition with unlimited hints & confetti",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      
        "http://localhost:5173",     
        "https://re-contexto.vercel.app"  
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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

@app.get("/")
def root():
    return {
        "message": "Contexto Unlimited API — Pink & Yellow Edition",
        "status": "ready" if app_state._initialized else "warming up...",
        "active_games": len(app_state.game_manager.active_games) if app_state.game_manager else 0
    }

@app.post("/game/new")
def new_game(mode: str = "practice", difficulty: str = "medium"):
    lazy_init()
    if not app_state.game_manager:
        raise HTTPException(status_code=503, detail="Waking up the summer brain... try again in 10s")
    return app_state.game_manager.start_new_game(mode=mode, difficulty=difficulty)

@app.post("/game/guess")
def make_guess(request: GuessRequest):
    lazy_init()
    if not app_state.game_manager:
        raise HTTPException(status_code=503, detail="Still loading embeddings... hold tight!")
    
    result = app_state.game_manager.make_guess(request.game_id, request.word)
    
    if result.get("error"):
        return GuessResponse(
            word=request.word,
            score=0.0,
            rank=-1,
            total_words=len(app_state.word_list),
            reasoning={},
            explanations=[],
            message=result.get("message", "Invalid word"),
            won=False,
        )
    return result

@app.get("/hint")
def get_one_hint(game_id: str):
    lazy_init()
    if not app_state.game_manager:
        raise HTTPException(status_code=503, detail="Loading hints engine...")
    
    if game_id not in app_state.game_manager.active_games:
        raise HTTPException(status_code=404, detail="Game not found")

    game_session = app_state.game_manager.active_games[game_id]
    game: GuessWord = game_session["game"]

    if "hints_given" not in game_session:
        game_session["hints_given"] = []

    secret = game.secret_word.lower()
    candidates = game.find_similar_words(secret, top_k=20)

    available = [
        c for c in candidates
        if c["word"].lower() != secret and c["word"] not in game_session["hints_given"]
    ]

    if not available:
        raise HTTPException(status_code=400, detail="No more hints available")

    best = available[0]
    game_session["hints_given"].append(best["word"])

    return {
        "word": best["word"],
        "similarity": round(best["similarity"], 4),
        "percent": int(best["similarity"] * 100)
    }

@app.get("/reveal")
def reveal_secret(game_id: str):
    lazy_init()
    if not app_state.game_manager:
        raise HTTPException(status_code=503, detail="Loading secret word...")
    
    if game_id not in app_state.game_manager.active_games:
        raise HTTPException(status_code=404, detail="Game not found or already ended")
    
    secret = app_state.game_manager.active_games[game_id]["game"].secret_word
    return {"secret": secret}

if __name__ == "__main__":
    import uvicorn
    import os
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)