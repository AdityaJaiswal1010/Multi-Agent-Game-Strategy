# run_selfplay.py
import os, time, copy, subprocess, sys, traceback
import my_player3 as agent

BOARD_SIZE = 5
def hybrid_selfplay(my_player_path="my_player3.py", myChip=1, max_my_moves=5, per_move_timeout=3.0):
    """
    Runs a game where:
    - Your agent (my_player3.py) plays as `myChip` (1 or 2)
    - The opponent is also my_player3.py but run separately by this script
    - Stops after `max_my_moves` moves by your agent.
    """

    prevBoard = zeros()
    currBoard = zeros()
    to_move = 1  # Player 1 starts
    my_moves = 0
    ply = 0

    explain_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "explanation.txt")

    # Clear old outputs
    if os.path.exists("output.txt"):
        os.remove("output.txt")

    print(f"Hybrid play: You = P{myChip}, Opponent = P{agent.gettingPlayerOpponenet(myChip)}")
    print(f"Stops after {max_my_moves} moves by your agent.\n")

    while my_moves < max_my_moves:
        # Prepare input for current player
        write_input(to_move, prevBoard, currBoard)

        # Call agent externally so RAG + Ollama still run
        try:
            subprocess.run([sys.executable, my_player_path], check=True, timeout=per_move_timeout)
        except subprocess.TimeoutExpired:
            print(f"[ply {ply}] Timeout for P{to_move}. Forcing PASS.")
            move = "PASS"
        except subprocess.CalledProcessError as e:
            print(f"[ply {ply}] Agent crashed: {e}. Forcing PASS.")
            move = "PASS"
        else:
            move = read_output()

        # Apply move to board state
        nextBoard, ok, captured = apply_move(currBoard, prevBoard, move, to_move)
        if not ok:
            print(f"[ply {ply}] P{to_move} illegal move {move}. Forcing PASS.")
            move = "PASS"
            nextBoard = currBoard

        # Log result
        print(f"[ply {ply}] P{to_move} move: {move} | captured={captured}")
        print_board(nextBoard)

        # Count your agent's moves only
        if to_move == myChip and move != "PASS":
            my_moves += 1

        # Switch player for next turn
        prevBoard, currBoard = currBoard, nextBoard
        to_move = agent.gettingPlayerOpponenet(to_move)
        ply += 1

    print(f"Stopped after {my_moves} moves by your agent.")
    print(f"Check explanation.txt for detailed rationales.")

def zeros():
    return [[0]*BOARD_SIZE for _ in range(BOARD_SIZE)]

def write_input(myChip, prevBoard, currBoard, path="input.txt"):
    with open(path, "w") as f:
        f.write(str(myChip) + "\n")
        for r in prevBoard: f.write("".join(str(x) for x in r) + "\n")
        for r in currBoard: f.write("".join(str(x) for x in r) + "\n")

def read_output(path="output.txt"):
    with open(path, "r") as f:
        t = f.read().strip()
        if t.upper() == "PASS": return "PASS"
        r, c = t.split(","); return (int(r), int(c))

def apply_move(currBoard, prevBoard, move, player):
    if move == "PASS": return copy.deepcopy(currBoard), True, 0
    r, c = move
    if currBoard[r][c] != 0: return currBoard, False, 0
    nb = copy.deepcopy(currBoard)
    nb[r][c] = player
    before = sum(nb[i][j] != 0 for i in range(BOARD_SIZE) for j in range(BOARD_SIZE))
    nb = agent.removingDeadPositions(nb, agent.gettingPlayerOpponenet(player))
    after  = sum(nb[i][j] != 0 for i in range(BOARD_SIZE) for j in range(BOARD_SIZE))
    captured = max(0, before - after)
    if prevBoard and nb == prevBoard: return currBoard, False, 0  # KO
    if move != "PASS" and agent.checkingLiberty(nb, r, c) == 0: return currBoard, False, 0  # suicide
    return nb, True, captured

def print_board(b):
    for row in b: print("".join(str(x) for x in row))
    print()

def self_play(max_seconds=10.0, max_plies=10, per_move_timeout=3.0):
    start = time.time()
    prevBoard = zeros()
    currBoard = zeros()
    to_move = 1
    ply = 0
    explain_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "explanation.txt")
    if os.path.exists("output.txt"): os.remove("output.txt")

    print(f"Self-play: up to {max_plies} plies or {max_seconds:.1f}s (explanations -> {explain_path})\n")
    while ply < max_plies and (time.time() - start) < max_seconds:
        write_input(to_move, prevBoard, currBoard)
        try:
            subprocess.run([sys.executable, "my_player3.py"], check=True, timeout=per_move_timeout)
        except subprocess.TimeoutExpired:
            print(f"[ply {ply}] Agent timed out for player {to_move}. Stopping."); break
        except subprocess.CalledProcessError as e:
            print(f"[ply {ply}] Agent error: {e}. Stopping."); break

        try:
            move = read_output()
        except Exception:
            traceback.print_exc(); print(f"[ply {ply}] Could not read output.txt. Stopping."); break

        nextBoard, ok, captured = apply_move(currBoard, prevBoard, move, to_move)
        if not ok:
            print(f"[ply {ply}] P{to_move} illegal move {move}. Forcing PASS.")
            move = "PASS"; nextBoard = currBoard

        print(f"[ply {ply}] P{to_move} move: {move} | captured={captured}")
        print_board(nextBoard)

        prevBoard, currBoard = currBoard, nextBoard
        to_move = agent.gettingPlayerOpponenet(to_move)
        ply += 1

    print("Done. Check explanation.txt for appended rationales & similar cases.")

if __name__ == "__main__":
    # Your agent plays as Player 1, stops after 5 moves
    hybrid_selfplay(
        my_player_path="my_player3.py",  # path to your agent file
        myChip=1,                        # you = Player 1 (set 2 if you want Player 2)
        max_my_moves=15,                  # stop after 5 moves by your agent
        per_move_timeout=100
    )

