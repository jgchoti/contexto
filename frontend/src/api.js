const API_BASE = import.meta.env.DEV
    ? '/api'
    : 'https://contexto-l76j.onrender.com';

export async function newGame(mode = 'practice', difficulty = 'medium') {
    const res = await fetch(`${API_BASE}/game/new`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode, difficulty })
    });

    if (!res.ok) {
        const err = await res.text();
        throw new Error(`Failed to start game: ${res.status} ${err}`);
    }
    return await res.json();
}

export async function makeGuess(gameId, word) {
    const res = await fetch(`${API_BASE}/game/guess`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            game_id: gameId,
            word: word.trim().toLowerCase()
        })
    });
    return await res.json();
}

export async function getHint(gameId) {
    const res = await fetch(`${API_BASE}/hint?game_id=${gameId}`);
    return await res.json();
}

export async function revealSecret(gameId) {
    const res = await fetch(`${API_BASE}/reveal?game_id=${gameId}`);
    return await res.json();
}