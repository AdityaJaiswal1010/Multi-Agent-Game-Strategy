Multi-Agent Game Strategy 🧠♟️

Alpha-Beta agent + RAG explanations + optional Ollama commentary for a 5×5 Go-like board game.
Runs standalone (single move from input.txt) or as self-play (agent vs. agent) to generate multi-move logs and explanations.

Why this exists (and why it’s useful)

Production-style agent loop: Reads standardized input.txt, writes output.txt → drop-in for course autograders or external match runners.

Explainability built-in: Every move appends a human-readable rationale to explanation.txt.

RAG memory: Retrieval-Augmented Generation indexes game states to surface “similar past positions”.

Optional LLM commentary (Ollama): Local, lightweight natural-language reasons for each move.

Self-play driver: Automates multi-move matches so you can see behavior evolve without a separate opponent.

What’s inside

my_player3.py – Your core agent (alpha-beta pruning + heuristic). Unchanged gameplay logic.

rag_module.py – RAG layer: lightweight vectorizer, FAISS (or Python fallback) index, explanation builder, Ollama hook.

run_selfplay.py – Hybrid self-play (agent plays both sides) with time/ply limits and per-move timeout.

input.txt / output.txt – File interface (agent contract).

explanation.txt – Appended move rationales: captures, liberties, similar cases, optional LLM text.

High-level architecture
+-------------------+        +--------------------+
| input.txt         |  --->  | my_player3.py      |  ---> writes chosen move ---> output.txt
| (prev/curr board) |        |  • alpha-beta      |
| + myChip (1/2)    |        |  • heuristic       |  ---> calls RAG (non-blocking)
+-------------------+        +--------------------+         |
                                                           v
                                               +----------------------+
                                               | rag_module.py        |
                                               |  • vectorize board   |
                                               |  • FAISS/fallback    |
                                               |  • similar cases     |
                                               |  • Ollama commentary |
                                               +----------+-----------+
                                                          |
                                                          v
                                                   explanation.txt


No interference: RAG runs after a move is chosen and does not affect search/decisions.

Pluggable: If FAISS or Ollama are missing, code gracefully degrades (still logs explanatory stats).

Installation
# (recommended) make a virtual env
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# base deps
pip install numpy

# optional fast retrieval
pip install faiss-cpu

# optional local LLM commentary
# 1) Install Ollama: https://ollama.com/download
# 2) Pull a small model:
#    ollama pull llama3   # or: mistral, phi3

Input format

my_player3.py expects input.txt as:

<myChip>          # 1 or 2
<prev row 1>
<prev row 2>
<prev row 3>
<prev row 4>
<prev row 5>
<curr row 1>
<curr row 2>
<curr row 3>
<curr row 4>
<curr row 5>


Example (empty board, Player 1 to move):

1
00000
00000
00000
00000
00000
00000
00000
00000
00000
00000

Quickstart
A) Single move (standard agent flow)
python3 my_player3.py


Writes: output.txt → e.g., 2,2 or PASS

Appends: explanation.txt → rationale (captures, liberties, similar cases, optional LLM line)

Using Ollama? Ensure ollama serve is running, and you’ve pulled a model.
Disable LLM while testing by setting llm="none" in the RAG call.

B) Self-play (agent vs. agent, stops after N of your moves)
python3 run_selfplay.py


Defaults in run_selfplay.py:

if __name__ == "__main__":
    hybrid_selfplay(
        my_player_path="my_player3.py",
        myChip=1,             # your agent is Player 1
        max_my_moves=5,       # stop after 5 of your moves
        per_move_timeout=10.0 # bump if first run is slow
    )


Console shows board after every ply; explanation.txt accumulates rationales + similar cases.

RAG & explanations

Vectorizer: Encodes next-board state into a small feature vector: me/opp/empty masks + liberty sums.

Index: Uses FAISS (IndexFlatIP) if installed; otherwise, a Python cosine-like fallback.

Similar cases: Shows top-k neighbors with basic metadata (captured, score, note, outcome placeholder).

Explainability: Logs captures, new group size, liberties, and (optionally) a one-liner LLM rationale.

Turn LLM on/off (in my_player3.py RAG hook):

rag.build_and_record_explanation(
  currBoard=currBoard,
  prevBoard=prevBoard,
  move=move_for_exp,
  myChip=myChip,
  eval_score=eval_for_log,
  llm="none",          # change to "ollama" once ready
  explanation_log_path=EXPLAIN_PATH
)

Troubleshooting

All moves are PASS

Increase per_move_timeout in run_selfplay.py (e.g., 10.0).

Temporarily set llm="none" to remove LLM latency.

Print raw output.txt right after the subprocess call to confirm the move text.

No explanation.txt appears

Ensure rag_module.py is in the same folder as my_player3.py.

Confirm these injections exist in my_player3.py (inside the RAG hook):

rag.checkingLiberty = checkingLiberty
rag.removingDeadPositions = removingDeadPositions
rag.gettingPlayerOpponenet = gettingPlayerOpponenet


Use the absolute path for explanation.txt (already done in the hook).

Ollama errors/timeouts

Run ollama serve and pull a small model (mistral, phi3).

Increase the timeout= in rag_module.py’s subprocess.run(...).