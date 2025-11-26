import { useState, useEffect, useRef } from "react";
import { newGame, makeGuess, getGameStats, getSimilarWords } from "./api";
import "./App.css";

function App() {
  const [game, setGame] = useState(null);
  const [guesses, setGuesses] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [hintWord, setHintWord] = useState("");
  const [similarWords, setSimilarWords] = useState([]);
  const inputRef = useRef();

  useEffect(() => {
    startNewGame();
    inputRef.current?.focus();
  }, []);

  async function startNewGame() {
    setLoading(true);
    setMessage("Starting new game...");
    try {
      const data = await newGame("practice", "medium");
      setGame(data);
      setGuesses([]);
      setMessage(data.message + " | Hint: " + data.hint);
    } catch (err) {
      setMessage("Failed to start game");
    }
    setLoading(false);
  }

  async function submitGuess(e) {
    e.preventDefault();
    if (!input.trim() || loading || !game) return;

    const word = input.trim().toLowerCase();
    setInput("");
    setLoading(true);
    setMessage("Thinking...");

    try {
      const result = await makeGuess(game.game_id, word);

      if (result.error || result.rank === -1) {
        setMessage(result.message || "Invalid word");
      } else {
        setGuesses((prev) => [...prev, result]);
        if (result.won) {
          setMessage(`🎉 You won in ${result.total_guesses} guesses!`);
        } else {
          setMessage(`#${result.rank} out of ${result.total_words}`);
        }
      }
    } catch (err) {
      setMessage("Error submitting guess");
    }
    setLoading(false);
    inputRef.current?.focus();
  }

  async function fetchHint() {
    if (!hintWord.trim()) return;
    try {
      const data = await getSimilarWords(hintWord, 10);
      setSimilarWords(data.similar_words || []);
    } catch (err) {
      setSimilarWords([]);
    }
  }

  const sortedGuesses = [...guesses].sort((a, b) => a.rank - b.rank);

  return (
    <>
      <div className="app">
        <header>
          <h1>Contexto Unlimited</h1>
          <button onClick={startNewGame} className="new-game-btn">
            New Game
          </button>
        </header>

        <div className="game-info">
          {game && (
            <p>
              <strong>Game ID:</strong> {game.game_id.slice(0, 8)}... |{" "}
              <strong>Mode:</strong> {game.mode}
            </p>
          )}
          <p className="message">{message}</p>
        </div>

        <form onSubmit={submitGuess} className="guess-form">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your guess..."
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            Guess
          </button>
        </form>

        <div className="hint-section">
          <input
            type="text"
            value={hintWord}
            onChange={(e) => setHintWord(e.target.value)}
            placeholder="Get hints for a word..."
            onKeyPress={(e) => e.key === "Enter" && fetchHint()}
          />
          <button onClick={fetchHint}>Get Hints</button>
          {similarWords.length > 0 && (
            <div className="hints">
              {similarWords.map((w, i) => (
                <span
                  key={i}
                  className="hint-tag"
                  onClick={() => setInput(w.word)}
                >
                  {w.word} ({(w.score * 100).toFixed(1)}%)
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="guesses">
          {sortedGuesses.length === 0 ? (
            <p>No guesses yet. Start guessing!</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Word</th>
                  <th>Rank</th>
                  <th>Similarity</th>
                </tr>
              </thead>
              <tbody>
                {sortedGuesses.map((g, i) => (
                  <tr
                    key={i}
                    className={
                      g.won
                        ? "won"
                        : g.rank <= 10
                        ? "hot"
                        : g.rank <= 50
                        ? "warm"
                        : "cold"
                    }
                  >
                    <td>{i + 1}</td>
                    <td>{g.word}</td>
                    <td>#{g.rank}</td>
                    <td>{(g.score * 100).toFixed(2)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </>
  );
}

export default App;
