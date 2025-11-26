const API_BASE = '/api';

export async function newGame(mode = 'practice', difficulty = 'medium') {
    const res = await fetch(`${API_BASE}/game/new?mode=${mode}&difficulty=${difficulty}`, {
        method: 'POST',
    });
    return await res.json();
}

export async function makeGuess(gameId, word) {
    const res = await fetch(`${API_BASE}/game/guess`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ game_id: gameId, word: word.trim().toLowerCase() })
    });
    return await res.json();
}

export async function getGameStats(gameId) {
    const res = await fetch(`${API_BASE}/game/${gameId}/stats`);
    if (!res.ok) throw new Error('Game not found');
    return await res.json();
}

export async function getSimilarWords(word, topK = 10) {
    const res = await fetch(`${API_BASE}/similar/${word}?top_k=${topK}`);
    return await res.json();
}