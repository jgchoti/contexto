from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from backend.script.guess import GuessWord
from backend.database import load_reference_words
import os
import numpy as np

class AppState:
    def __init__(self):
        self.game: GuessWord = None
        self.word_list: List[str] = []

app_state = AppState()

def create_app() -> FastAPI:
    app = FastAPI(
        title="Contexto Game API",
        description="A word guessing game based on semantic similarity.",
        version="1.0.0",
    )

    @app.on_event("startup")
    def startup_event():
        word_list, word_embeddings = load_reference_words()
        print(f"Loaded {len(word_list)} words")

        if not isinstance(word_list, list):
            try:
                word_list = list(word_list)
            except TypeError:
                word_list = [str(word_list)] 

        app_state.word_list = [str(w) for w in word_list]

        secret_word = os.getenv("SECRET_WORD", "python")

        app_state.game = GuessWord(
            reference_words=app_state.word_list,
            secret_word=secret_word,
            reference_embeddings=word_embeddings,
        )
        print("Startup complete.")

    return app

app = create_app()

class GuessResponse(BaseModel):
    word: str
    score: float
    rank: int
    total_words: int
    reasoning: Dict[str, float]
    explanations: List[Dict[str, Any]] = []
    message: str
    won: bool
    

def get_game() -> GuessWord:
    return app_state.game

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Contexto Game API!",
        "total_words": len(app_state.word_list) if app_state.word_list else 0,
        "secret_word_set": app_state.game is not None,
    }

@app.get("/guess/{word}", response_model=GuessResponse)
def make_guess(word: str, game: GuessWord = Depends(get_game)):
    if not game:
        return {"error": "Game not initialized"}
    result = game.guess(word)
    return result

@app.get("/similar/{word}")
def get_similar_words(word: str, top_k: int = 10, game: GuessWord = Depends(get_game)):
    if not game:
        return {"error": "Game not initialized"}
    similar_words = game.find_similar_words(word, top_k=top_k)
    return {"word": word, "similar_words": similar_words}
