from fastapi import FastAPI
from backend.script.guess import guess
from pydantic import BaseModel

app = FastAPI()

class GuessResponse(BaseModel):
    word: str
    score: float
    message: str

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/guess")
def guess_root():
    return {"message": "Please provide a word, e.g., /guess/hello"}


@app.get("/guess/{word}", response_model=GuessResponse)
def make_guess(word: str):
    result = guess(word)
    return {
        "word": word,
        "score": result.get("score", 0),
        "message": result.get("message", "")
    }
