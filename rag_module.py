# rag_module.py
from anthropic import Anthropic
import copy, time, json, subprocess, os
from typing import Tuple, List, Union
import numpy as np

try:
    import faiss  # pip install faiss-cpu
except Exception:
    faiss = None

BOARD_SIZE = 5  # must match your agent

# ====== You must import these from your agent if this is a separate file ======
# from your_agent_file import checkingLiberty, removingDeadPositions, gettingPlayerOpponenet
# If you paste this inside the same file (below your function defs), it will see them.

# ---------- small helpers ----------
def _neighbors(r, c):
    if r > 0: yield (r-1, c)
    if r < BOARD_SIZE-1: yield (r+1, c)
    if c > 0: yield (r, c-1)
    if c < BOARD_SIZE-1: yield (r, c+1)

def _apply_move(currBoard, prevBoard, move, player):
    """
    Returns (next_board, legal:bool, captured_count:int).
    Uses your existing capture rules & KO via prevBoard comparison.
    """
    if move == 'PASS':
        return copy.deepcopy(currBoard), True, 0

    r, c = move
    if currBoard[r][c] != 0:
        return currBoard, False, 0

    nb = copy.deepcopy(currBoard)
    nb[r][c] = player
    # capture opponent stones (your function)
    before = sum(nb[i][j] != 0 for i in range(BOARD_SIZE) for j in range(BOARD_SIZE))
    nb = removingDeadPositions(nb, gettingPlayerOpponenet(player))
    after = sum(nb[i][j] != 0 for i in range(BOARD_SIZE) for j in range(BOARD_SIZE))

    # KO check: if identical to prevBoard, illegal
    if prevBoard and nb == prevBoard:
        return currBoard, False, 0

    # suicide check: placed stone must have liberties
    # (Using your checkingLiberty)
    if move != 'PASS' and checkingLiberty(nb, r, c) == 0:
        return currBoard, False, 0

    return nb, True, max(0, before - after)

def _board_features(board, myChip):
    """
    Lightweight vector: [me(25), opp(25), empty(25), my_lib_sum, opp_lib_sum] -> L2-normalized.
    Compatible with cosine-like search (IndexFlatIP).
    """
    arr = np.array(board, dtype=np.int8)
    me   = (arr == myChip).astype(np.float32).flatten()
    opp  = (arr == gettingPlayerOpponenet(myChip)).astype(np.float32).flatten()
    emp  = (arr == 0).astype(np.float32).flatten()

    my_libs = 0; opp_libs = 0
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if arr[i, j] == myChip:
                my_libs += checkingLiberty(board, i, j)
            elif arr[i, j] == gettingPlayerOpponenet(myChip):
                opp_libs += checkingLiberty(board, i, j)

    feat = np.concatenate([me, opp, emp, np.array([my_libs, opp_libs], dtype=np.float32)])
    nrm = np.linalg.norm(feat) + 1e-9
    return (feat / nrm).astype('float32')

# ---------- FAISS-backed (or fallback) index ----------
class CaseIndex:
    def __init__(self, dim: int):
        self.dim = dim
        self.enabled = faiss is not None
        self.metas: List[dict] = []
        if self.enabled:
            self.index = faiss.IndexFlatIP(dim)  # cosine-ish with normalized vectors
        else:
            self.index = None
            self.vecs: List[np.ndarray] = []

    def add(self, vec: np.ndarray, meta: dict):
        if self.enabled:
            self.index.add(vec[np.newaxis, :])
        else:
            self.vecs.append(vec)
        self.metas.append(meta)

    def search(self, vec: np.ndarray, k: int = 5):
        if len(self.metas) == 0:
            return []
        if self.enabled:
            D, I = self.index.search(vec[np.newaxis, :], k)
            res = []
            for d, idx in zip(D[0], I[0]):
                if idx == -1: continue
                res.append((float(d), self.metas[idx]))
            return res
        else:
            sims = []
            for i, v in enumerate(self.vecs):
                sims.append((float(np.dot(vec, v)), self.metas[i]))
            sims.sort(key=lambda x: -x[0])
            return sims[:k]

# global, in-memory (simple) index
RAG_INDEX = CaseIndex(dim=25*3 + 2)

def genai_commentary_ollama(prompt: str, model: str = "llama3"):
    """
    Requires: Ollama installed & a model pulled (e.g., `ollama pull llama3`).
    Returns short text or default string if Ollama not available.
    """
    try:
        out = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15
        )
        text = out.stdout.decode("utf-8").strip()
        return text if text else "Rationale: prioritizes connection, liberties, and capture threat."
    except Exception:
        return "Rationale: prioritizes connection, liberties, and capture threat."

def genai_commentary_claude_mcp(prompt: str):
    try:
        client = Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )

        response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=80,
            temperature=0.2,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.content[0].text.strip()

    except Exception as e:
        return f"Rationale (Claude MCP fallback): {str(e)}"

# ---------- Main entry you will call from main() ----------
def build_and_record_explanation(currBoard, prevBoard, move: Union[str, Tuple[int,int]], myChip: int,
                                 eval_score: float = None,
                                 llm: str = "none",  # "none" | "ollama" | "claude_mcp"
                                 explanation_log_path: str = "explanation.txt"):
    """
    1) Applies the chosen move to produce next_board
    2) Computes features & retrieves similar past positions
    3) Writes a readable explanation to explanation.txt
    4) Inserts the case into the in-memory index

    Returns: (explanation_text, next_board, captured_count)
    """
    next_board, ok, captured = _apply_move(currBoard, prevBoard, move, myChip)
    if not ok:
        explanation = f"Move {move} deemed illegal by auxiliary checker (kept agent output unchanged)."
        _append_log(explanation_log_path, explanation)
        return explanation, currBoard, 0

    vec = _board_features(next_board, myChip)
    neighbors = RAG_INDEX.search(vec, k=3)

    # quick local stats
    local_stats = []
    if move != 'PASS':
        r, c = move
        # count group size and liberties of the placed stone
        grp_size = _group_size(next_board, r, c)
        libs = checkingLiberty(next_board, r, c)
        local_stats.append(f"new_group_size={grp_size}")
        local_stats.append(f"liberties={libs}")

    # LLM commentary (optional)
    llm_txt = ""
    if llm == "ollama":
        llm_txt = genai_commentary_ollama(_llm_prompt(currBoard, move, eval_score))
    elif llm == "claude_mcp":
        llm_txt = genai_commentary_claude_mcp(_llm_prompt(currBoard, move, eval_score))

    # craft explanation text
    lines = []
    lines.append(f"Move {move} | eval={eval_score if eval_score is not None else 'n/a'} | captured={captured}")
    if local_stats:
        lines.append("- " + ", ".join(local_stats))
    if neighbors:
        lines.append("- Similar past positions:")
        for sim, meta in neighbors:
            lines.append(f"  • sim={sim:.2f} | note={meta.get('note','')} | outcome={meta.get('outcome','n/a')}")
    else:
        lines.append("- Similar past positions: none yet (index will improve over time).")
    if llm_txt:
        lines.append(f"- LLM: {llm_txt}")

    explanation = "\n".join(lines)
    _append_log(explanation_log_path, explanation)

    # store case for future retrieval
    RAG_INDEX.add(vec, {
        "move": move,
        "score": float(eval_score) if eval_score is not None else None,
        "note": f"captured={captured}",
        "outcome": "n/a"
    })

    return explanation, next_board, captured

# ---------- convenience utils ----------
def _append_log(path, text):
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"=== {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n{text}\n\n")

def _llm_prompt(currBoard, move, eval_score):
    flat = "".join(str(x) for row in currBoard for x in row)
    return (
        "You are explaining a 5x5 Go-like move.\n"
        f"Board(flat): {flat}\n"
        f"Chosen move: {move}; eval: {eval_score}\n"
        "Explain in one or two short sentences why this move is strategically sound, focusing on liberties, connection, and capture threat."
    )

def _group_size(board, r, c):
    # BFS with color match
    col = board[r][c]
    if col == 0: return 0
    seen = set([(r, c)])
    q = [(r, c)]
    sz = 1
    while q:
        cr, cc = q.pop()
        for nr, nc in _neighbors(cr, cc):
            if (nr, nc) not in seen and board[nr][nc] == col:
                seen.add((nr, nc))
                q.append((nr, nc))
                sz += 1
    return sz
