import { useState, useEffect, useRef } from "react";
import { newGame, makeGuess } from "./api";
import confetti from "canvas-confetti";
import "./App.css";

function App() {
  const [game, setGame] = useState(null);
  const [guesses, setGuesses] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [hints, setHints] = useState([]);
  const [hintLoading, setHintLoading] = useState(false);
  const [similarWords, setSimilarWords] = useState([]);
  const inputRef = useRef();

  useEffect(() => {
    startNewGame();
    inputRef.current?.focus();
  }, []);

  const triggerConfetti = () => {
    // Pink & Yellow summer explosion
    const count = 300;
    const defaults = {
      origin: { y: 0.7 },
      colors: [
        "#ff6b9d",
        "#ff9ec1",
        "#ffd43b",
        "#ffb84d",
        "#fff0f6",
        "#ffe8a3",
      ],
      ticks: 200,
      gravity: 0.8,
      scalar: 1.2,
    };

    // Left side burst
    confetti({
      ...defaults,
      particleCount: count / 2,
      angle: 60,
      spread: 55,
      startVelocity: 60,
      origin: { x: 0, y: 0.6 },
    });

    // Right side burst
    confetti({
      ...defaults,
      particleCount: count / 2,
      angle: 120,
      spread: 55,
      startVelocity: 60,
      origin: { x: 1, y: 0.6 },
    });

    // Final big center explosion
    setTimeout(() => {
      confetti({
        ...defaults,
        particleCount: count,
        spread: 80,
        startVelocity: 80,
        scalar: 1.5,
        shapes: ["star", "circle"],
      });
    }, 300);
  };

  async function startNewGame() {
    setLoading(true);
    setMessage("Starting new game...");
    try {
      const data = await newGame("practice", "medium");
      setGame(data);
      setGuesses([]);
      setHints([]); // Reset hints for new game
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
          triggerConfetti();
          setMessage(`You won in ${result.total_guesses} guesses!`);
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
    if (loading || !game) return;
    setLoading(true);
    try {
      const res = await fetch(
        `http://localhost:8000/hint?game_id=${game.game_id}`
      );
      if (!res.ok) throw new Error();
      const data = await res.json();
      setHints((prev) => {
        const exists = prev.some((h) => h.word === data.word);
        if (exists) return prev;
        return [...prev, data];
      });

      setMessage(`💡 Hint: "${data.word}" is ${data.percent}% similar`);
    } catch (err) {
      setMessage("Failed to get hint");
    }
    setLoading(false);
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
        <div className="action-buttons-section">
          <div className="action-buttons-wrapper">
            {/* HINT BUTTON */}
            <button
              onClick={async () => {
                if (hintLoading || loading || !game) return;
                setHintLoading(true);
                try {
                  const res = await fetch(`/api/hint?game_id=${game.game_id}`);
                  if (!res.ok) throw new Error();
                  const data = await res.json();

                  setHints((prev) => {
                    if (prev.some((h) => h.word === data.word)) {
                      setMessage("Already showed that hint!");
                      return prev;
                    }
                    setMessage(`New hint revealed!`);
                    return [...prev, data];
                  });
                } catch (err) {
                  setMessage("No more strong hints available");
                }
                setHintLoading(false);
              }}
              disabled={hintLoading || loading}
              className="hint-btn"
            >
              {hintLoading ? "Finding..." : `Give me a hint (${hints.length})`}
            </button>

            <button
              onClick={async () => {
                if (!game || loading) return;
                if (
                  !window.confirm(
                    "Really give up? The secret word will be revealed!"
                  )
                )
                  return;

                setLoading(true);
                try {
                  const res = await fetch(
                    `/api/reveal?game_id=${game.game_id}`
                  );
                  const data = await res.json();
                  setMessage(
                    `The secret word was: ${data.secret.toUpperCase()} `
                  );
                  setGuesses((prev) =>
                    prev.map((g) => ({ ...g, gameOver: true }))
                  );
                } catch (err) {
                  setMessage("Could not reveal word");
                }
                setLoading(false);
              }}
              disabled={loading || guesses.some((g) => g.won)}
              className="give-up-btn"
            >
              I give up
            </button>
          </div>

          {hints.length > 0 && (
            <div className="unlimited-hints">
              <p>Your hints so far:</p>
              <div className="hints-grid">
                {hints.map((hint, i) => (
                  <div
                    key={i}
                    className="hint-card"
                    onClick={() => {
                      setInput(hint.word);
                      inputRef.current?.focus();
                    }}
                  >
                    <div className="hint-word">{hint.word.toUpperCase()}</div>
                    <div className="hint-percent">{hint.percent}%</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="guesses">
          {sortedGuesses.length === 0 ? (
            <p>No guesses yet. Start guessing!</p>
          ) : (
            <div className="guesses-list">
              {sortedGuesses.map((g, i) => (
                <div
                  key={i}
                  className={`guess-card ${
                    g.won
                      ? "won"
                      : g.rank <= 10
                      ? "hot"
                      : g.rank <= 50
                      ? "warm"
                      : "cold"
                  }`}
                >
                  <div className="guess-header">
                    <span className="position">{i + 1}</span>
                    <span className="word">{g.word.toUpperCase()}</span>
                    <span className="rank">#{g.rank}</span>
                    <span className="score">{(g.score * 100).toFixed(1)}%</span>

                    {!g.won && (g.explanations || g.reasoning) && (
                      <button
                        className="expand-btn"
                        onClick={() =>
                          setGuesses((prev) =>
                            prev.map((gg) =>
                              gg.word === g.word
                                ? { ...gg, expanded: !gg.expanded }
                                : gg
                            )
                          )
                        }
                      >
                        {g.expanded ? "Hide" : "Show"} Why
                      </button>
                    )}
                  </div>

                  {g.expanded && (
                    <div className="reasoning-panel">
                      <div className="layers">
                        {g.explanations?.map((exp, j) => (
                          <div key={j} className="layer-row">
                            <div className="layer-icon">{exp.icon}</div>
                            <div className="layer-info">
                              <div className="layer-name">{exp.layer}</div>
                              <div className="layer-explanation">
                                {exp.explanation}
                              </div>
                            </div>
                            <div className="layer-bar-container">
                              <div
                                className="layer-bar"
                                style={{
                                  width: `${exp.score * 100}%`,
                                  background:
                                    exp.score > 0.7
                                      ? "linear-gradient(90deg, #ffd43b, #fab005)" // hot yellow
                                      : exp.score > 0.4
                                      ? "linear-gradient(90deg, #ffd4a3, #ffb84d)" // warm orange
                                      : "linear-gradient(90deg, #fecaca, #fca5a5)", // cold pink
                                }}
                              />
                              <span className="layer-percent">
                                {(exp.score * 100).toFixed(0)}%
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export default App;
