Multi-Agent Game Strategy ♟️

An AI-powered game-playing agent built using Alpha-Beta pruning and enhanced with an optional RAG (Retrieval-Augmented Generation) layer for explainable strategies.
Includes a self-play simulation module for automated benchmarking and generating detailed move explanations.

📌 Project Overview

This project focuses on designing an intelligent game-playing agent capable of making optimal decisions in a competitive two-player board game.
It integrates traditional search algorithms with explainability features using retrieval + LLM commentary to make strategies transparent and interpretable.

🎯 Why This Project

Classical game-playing agents often lack explainability.

This project bridges the gap by combining:

Alpha-Beta Pruning → Efficient optimal move search.

RAG-based Explanations → Explains why a move was chosen.

Self-Play Simulation → Automates evaluation and builds a searchable memory of strategies.

✅ What Was Done

Game-playing agent (my_player3.py)

Built from scratch with Alpha-Beta pruning and a custom heuristic.

Handles move legality, captures, KO, and suicide checks.

RAG Layer (rag_module.py)

Extracts board embeddings.

Stores and retrieves similar past positions using FAISS (or Python fallback).

Generates human-readable explanations in explanation.txt.

Optional Ollama integration for LLM-powered rationales.

Self-Play Simulation (run_selfplay.py)

Automates agent-vs-agent matches.

Generates multi-move explanations quickly.

Populates RAG index for better retrieval over time.

📈 Impact

Explainable AI Agent → Every move has a documented rationale.

Faster Evaluation → Automated self-play benchmarks strategies rapidly.

Searchable Strategies → Build a memory of past positions to improve analysis.

Human-Readable Insights → Optional GenAI commentary makes results intuitive.

🔄 Project Flow
flowchart TD
    A[input.txt] --> B[my_player3.py]
    B -->|Chosen Move| C[output.txt]
    B --> D[RAG Module]
    D -->|Vectorize Board| E[FAISS Index]
    D -->|Optional Ollama| F[LLM Rationale]
    D --> G[explanation.txt]
    H[run_selfplay.py] --> B


Flow Explanation

Input → Agent reads input.txt (board + player turn).

Decision → Uses Alpha-Beta pruning + heuristics to choose optimal move.

Explanation →

Logs stats (captures, liberties).

Retrieves similar past positions via FAISS/Python fallback.

Optionally appends LLM-generated rationale via Ollama.

Output → Writes chosen move to output.txt.

Self-Play → Automates multi-move matches and explanation logging.

⚡ How to Run the Project
1. Clone the repo
git clone https://github.com/AdityaJaiswal1010/Multi-Agent-Game-Strategy.git
cd Multi-Agent-Game-Strategy

2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

3. Install dependencies
pip install numpy
pip install faiss-cpu   # optional, faster retrieval

4. (Optional) Setup Ollama for LLM explanations

Download Ollama

Pull a small model:

ollama pull llama3

5. Run the agent for a single move
python3 my_player3.py


Reads input.txt

Writes move → output.txt

Appends explanation → explanation.txt

6. Run self-play simulation (agent vs agent)
python3 run_selfplay.py


Automates matches until your agent has played 5 moves.

Appends detailed explanations for every move.

📜 Example Explanation Log
=== 2025-08-26 15:32:10 ===
Move (2,2) | eval=4.50 | captured=0
- new_group_size=1, liberties=4
- Similar past positions: none yet (index will improve over time).
- LLM: This move secures center control and maximizes liberties.

🧠 Key Takeaways

Built a multi-agent competitive game-playing system from scratch.

Designed a RAG-powered explainability layer for better interpretability.

Integrated self-play simulation to test, benchmark, and document strategies.

Optional Ollama integration enables GenAI-based insights for better storytelling.
