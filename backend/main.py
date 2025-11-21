# backend/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from backend.script.guess import GuessWord

app = FastAPI()

WORD_LIST = [
    "python", "programming", "code", "computer", "algorithm", 
    "data", "machine", "learning", "artificial", "intelligence",
    "software", "developer", "function", "variable", "loop",
    "array", "string", "database", "server", "client",
    "network", "security", "cloud", "api", "framework",
    "library", "module", "package", "deployment", "testing"
]

SECRET_WORD = "python"


game = GuessWord(reference_words=WORD_LIST, secret_word=SECRET_WORD)

class GuessResponse(BaseModel):
    word: str
    score: float
    rank: int
    total_words: int
    reasoning: dict
    message: str

@app.get("/")
def read_root():
    return {
        "message": "Contexto Game API", 
        "total_words": len(WORD_LIST)
    }

@app.get("/guess/{word}", response_model=GuessResponse)
def make_guess(word: str):
    result = game.guess(word)
    return result
