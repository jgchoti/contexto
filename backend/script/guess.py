def guess(word: str):
    score = 500 
    message = f"Your guess '{word}' scored {score} points!"
    return {
        "score": score,
        "message": message
    }