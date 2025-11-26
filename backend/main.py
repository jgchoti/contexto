from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
from backend.game_manager import GameManager
from backend.script.guess import GuessWord
from backend.database import load_reference_words
class AppState:
    def __init__(self):
        self.game_manager: GameManager = None
        self.word_list: List[str] = []

app_state = AppState()

def create_app() -> FastAPI:
    app = FastAPI(
        title="Contexto Game API",
        description="Unlimited Contexto with pink & yellow summer vibes",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], 
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup_event():
        print("Loading reference words and embeddings from MongoDB...")
        word_list, word_embeddings = load_reference_words()
        print(f"Loaded {len(word_list)} words")

        app_state.word_list = [str(w) for w in word_list]
        app_state.game_manager = GameManager(
            reference_words=app_state.word_list,
            reference_embeddings=word_embeddings
        )
        print("GameManager ready!")
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

    @app.get("/")
    def root():
        return {
            "message": "Contexto Unlimited API – Pink & Yellow Edition",
            "active_games": len(app_state.game_manager.active_games) if app_state.game_manager else 0,
        }

    @app.post("/game/new"))
    def new_game(mode: str = "practice", difficulty: str = "medium"):
        if not app_state.game_manager:
            raise HTTPException(503, "Game engine not ready yet")
        return app_state.game_manager.start_new_game(mode=mode, difficulty=difficulty)

    @app.post("/game/guess")
    def make_guess(request: GuessRequest):
        if not app_state.game_manager:
            raise HTTPException(503, "Game engine not ready yet")
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
        if game_id not in app_state.game_manager.active_games:
            raise HTTPException(404, "Game not found")

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
            raise HTTPException(400, "No more hints available")

        best = available[0]
        game_session["hints_given"].append(best["word"])

        return {
            "word": best["word"],
            "similarity": round(best["similarity"], 4),
            "percent": int(best["similarity"] * 100)
        }

    @app.get("/reveal")
    def reveal_secret(game_id: str):
        if game_id not in app_state.game_manager.active_games:
            raise HTTPException(404, "Game not found or already ended")
        secret = app_state.game_manager.active_games[game_id]["game"].secret_word
        return {"secret": secret}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)