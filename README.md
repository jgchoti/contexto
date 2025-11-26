# 🎮 Contexto Unlimited

> **"I saw the game. Recognized the tech. Rebuilt it."**

A reverse-engineered version of Contexto that showcases semantic search, vector embeddings, and full-stack data engineering.

[![Live Demo](https://img.shields.io/badge/Demo-Live-success)](your-demo-link)
[![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20React%20%7C%20MongoDB-blue)](/)

---

## 🎯 The Challenge

Can you guess the secret word? Each guess gets ranked by semantic similarity—powered by ML, not just string matching.

**What makes this interesting:**

- Not just "hot or cold"—you get a **3-layer reasoning breakdown**
- **~9,000-word vocabulary** with real-time ranking
- **FAISS-powered hints** for when you're stuck

---

## 🧠 The Tech Behind It

### **The ML Stack**

```
User Guess → Sentence Transformer → 384D Vector → 3-Layer Scoring
                                                          ↓
                                    Semantic (70%) + Lexical (20%) + Linguistic (10%)
                                                          ↓
                                              Ranked against 9K words
```

**🎯 What Makes This Different**

**The Original Contexto**

Your guess → Some ML model → Hot or Cold

**This Version**

Your guess → 3-Layer AI Analysis → Detailed reasoning WHY

You get:

🧠 **Semantic score** - Does it mean the same thing?

📝 **Lexical score** - Does it look similar? (catches plurals, tenses)

📚 **Linguistic score** - Is it the same type of word?

Click "Show Why" on any guess to see the breakdown. It's like X-ray vision for word relationships.

---

### **Architecture**

```
Frontend (React + Vite)
    ↓
FastAPI Backend
    ↓
┌─────────────────────────────────────┐
│  Game Manager                       │
│  • Multiple concurrent games        │
│  • Daily + Practice modes           │
│  • Pre-computed embeddings          │
└─────────────────────────────────────┘
    ↓                    ↓
MongoDB Atlas      PostgreSQL (Supabase)
• Game sessions    • Analytics
• 10K embeddings   • Word difficulty
• Player state     • dbt transforms
```

---

## 🚀 Getting Started

### **Prerequisites**

```bash
Python 3.12+
Node.js 18+
MongoDB Atlas account (free tier)
```

### **Backend Setup**

```bash
cd backend

# Create virtual environment
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"

# Set up environment variables
cp .env.example .env
# Edit .env with your MongoDB connection string

# Load words into MongoDB (takes ~5 minutes)
python scripts/setup_words.py

# Start the server
uvicorn main:app --reload
```

Backend runs on `http://localhost:8000`

### **Frontend Setup**

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend runs on `http://localhost:5173`

---

## 🎮 How to Play

1. **Start a game**
2. **Make a guess**: Type any word
3. **Get ranked**: See where your guess ranks (1 = closest, 10000 = furthest)
4. **Analyze**: Click "Show Why" to see the 3-layer reasoning breakdown
5. **Use hints**: Stuck? Get a word that's semantically close
6. **Win**: Find the secret word!

---

## 🏗️ Technical Deep Dive

### **Embedding Pipeline**

```python
# 1. Setup: Pre-compute 10K embeddings (one-time)
words = load_word_list()  # ~9~,000 most common English words
embeddings = model.encode(words)  # 384D vectors
store_in_mongodb(words, embeddings)  # 15MB storage

# 2. Game Start: Calculate similarities
secret_word = "python"
secret_emb = model.encode([secret_word])
similarities = cosine_similarity(all_embeddings, secret_emb)
sorted_ranks = argsort(similarities)  # Pre-sorted for fast lookup

# 3. User Guess: On-the-fly embedding + ranking
guess_emb = model.encode([user_guess])
score = calculate_layered_score(guess_emb, secret_emb)
rank = binary_search(sorted_ranks, score)  # <100ms response
```

### **Performance Optimizations**

- **Pre-computation**: Calculate all 10K similarities on game start (~3s)
- **Shared resources**: One model instance, one embedding set, many games
- **FAISS indexing**: Hint feature uses approximate nearest neighbor search
- **MongoDB caching**: Store embeddings to avoid regeneration (5min → 1s startup)

**Result**: <100ms response time per guess, 50+ concurrent games on 512MB RAM

---

## 📊 Tech Stack

| Layer             | Technology                   | Why                                 |
| ----------------- | ---------------------------- | ----------------------------------- |
| **Frontend**      | React + Vite                 | Fast dev experience, modern tooling |
| **Backend**       | FastAPI                      | Async, type hints, automatic docs   |
| **ML**            | Sentence Transformers        | SOTA embeddings, 80MB model size    |
| **Vector Search** | FAISS                        | 60x faster similarity search        |
| **Databases**     | MongoDB + PostgreSQL         | NoSQL for state, SQL for analytics  |
| **NLP**           | NLTK (WordNet + Levenshtein) | Linguistic features                 |
| **Hosting**       | Vercel + Atlas               | All on free tiers                   |

---

## 🎯 Key Engineering Decisions

### **Why Sentence Transformers over Word2Vec?**

| Model                 | Size  | OOV Handling | Hostable? |
| --------------------- | ----- | ------------ | --------- |
| Word2Vec              | 3.6GB | ❌ No        | ❌ No     |
| Sentence Transformers | 80MB  | ✅ Yes       | ✅ Yes    |

**Trade-off**: Slightly slower inference but flexible and deployable on free tier.

### **Why 3-Layer Scoring?**

Pure semantic similarity gives weird results:

- "program" vs "programmer" → Low score (should be high)
- "read" (verb) vs "read" (past tense) → Medium score (should be perfect)

Layered approach catches these edge cases.

### **Why MongoDB + PostgreSQL?**

- **MongoDB**: Fast writes for game sessions, flexible schema, embedded arrays

---

## 📈 Project Roadmap

**Phase 1: Core Game** ✅

- [x] 3-layer scoring system
- [x] Game manager with multiple modes
- [x] FAISS hint system
- [x] React frontend

**Phase 2: Analytics** 🚧

- [ ] dbt models for word difficulty
- [ ] Player behavior analysis
- [ ] Leaderboard system

**Phase 3: Advanced Features** 📋

- [ ] Multiplayer mode (Redis pub/sub)
- [ ] Custom word lists
- [ ] Fine-tuned embeddings on game data

---

## 📝 What I Learned

**Data Engineering:**

- Pre-computation strategies for sub-100ms latency
- Memory optimization under free-tier constraints (512MB)

**Machine Learning:**

- Ensemble methods beat single-model approaches
- Feature engineering matters more than model complexity
- Production ML requires infrastructure, not just models

**System Design:**

- Horizontal scalability through stateless game sessions
- Strategic trade-offs: accuracy vs latency vs cost
- Free-tier optimization techniques

---

## 🙏 Acknowledgments

- Original Contexto game for inspiration
- Sentence Transformers library by UKPLab

---
