import os
import copy

def readingGame():
    # read the input file and extract prev board state and current board state 
    myChip = None
    prevBoard = []
    currBoard = []
    
    if os.path.exists("input.txt"):
        with open("input.txt", "r") as file:
            lines = file.readlines()
            myChip = int(lines[0].strip())
            for position in lines[1:6]:  
                curr = []
                for char in position.strip():  
                    curr.append(int(char))
                prevBoard.append(curr)

            for position in lines[6:11]:  
                curr = []
                for char in position.strip(): 
                    curr.append(int(char))
                currBoard.append(curr)
    return myChip, currBoard, prevBoard


def findingEmptyPositions(board, myChip):
    # this function does is that it check the void and empty board positions 
    emptyBoardPosition = []
    for i in range(5):
        for j in range(5):
            if board[i][j] == myChip:
                if not checkingLiberty(board, i, j) and (i,j) not in emptyBoardPosition:
                    emptyBoardPosition.append((i, j))
    return emptyBoardPosition


def gettingPlayerOpponenet(myChip):
    # As there are only 2 possibility meaning if current player is 1 then opponenet is 2 and vica versa
    if myChip == 1:
        return 2
    else:
        return 1

def pickAMove(moveChoosen):
    # we simply pick the first best, legal and valid move and proceed as our next move
    if moveChoosen or len(moveChoosen) > 0:
        return moveChoosen[0]
    else:
        return 'PASS'


def approximationHueristicFunction(board, nextMoveToTake, myChip):
    # this function counts all the instance of my player and opponent and depedeing on that i check if there is 
    # any open area/ liberty to expand and they aren't surrounded or trapped by enemy
    myPlayerCount = 0
    opponentPlayerCount = 0
    hueristicValueCounter = 0
    hueristicValueCounterOpponenet = 0
    for i in range(5):
        for j in range(5):
            if board[i][j] == myChip:
                # got my player so increase counter
                # also from this position we aim to be in group so finding the liberty connected to 
                # exisiting cluseter of us 
                myPlayerCount += 1
                hueristicValueCounter += (25*(myPlayerCount + checkingLiberty(board, i, j)))/25
            elif board[i][j] == gettingPlayerOpponenet(myChip):
                # got enemy so increase counter
                # check enemy liberty to predict his min and our max
                opponentPlayerCount += 1
                hueristicValueCounterOpponenet += (25*(opponentPlayerCount + checkingLiberty(board, i, j)))/25
    # if next is enemy so do our counter - oponent counter
    if nextMoveToTake == myChip:
        return (-1*(3*(hueristicValueCounter - hueristicValueCounterOpponenet)))/(-3)
    return (-1 * (3 * (hueristicValueCounterOpponenet - hueristicValueCounter))) / (-3)



def writingGame(move):
    # write the output file as we have taken a decision
    with open('output.txt', 'w') as file:
        if move == 'PASS':
            file.write(move)
        else:
           file.write(str(move[0])+','+str(move[1]))


def checkingLiberty(board, row, col):
    # checking for the actual connected empty safe area of a cluster 
    # so for each instance i check its 4 directionall neighbors and check if we may can make a valid move which will lead to our 
    # move maximization
    totalCounter = 0
    for point in findingRelatedCluster(board, row, col):
        board = removingDeadPositions(board, (point[0], point[1]))
        validLocationPoints = []
        if 0 <= point[0] - 1 < 5:
            validLocationPoints.append((point[0] - 1, point[1]))
        if 0 <= point[0] + 1 < 5:
            validLocationPoints.append((point[0] + 1, point[1]))
        if 0 <= point[1] - 1 < 5:
            validLocationPoints.append((point[0], point[1] - 1))
        if 0 <= point[1] + 1 < 5:
            validLocationPoints.append((point[0], point[1] + 1))
        for neighbor in validLocationPoints:
            if board[neighbor[0]][neighbor[1]] == 0:
                totalCounter += 1
    return totalCounter


def removingDeadPositions(board, myChip):
    # checking the board first and getting all empty positions and this is done by findingEmptyPositions
    # then remove these empty positions
    deadStonePositions = findingEmptyPositions(board, myChip)
    # depending upon the empty positions found we remove those positions as empty
    if not deadStonePositions or len(deadStonePositions) == 0:
        return board
    # we just remove these stones with empty stone
    for positions in deadStonePositions:
        board[positions[0]][positions[1]] = 0
    return board


def findingRelatedCluster(board, row, col, cluster=None, visited=None):
    # find all related connected clusters
    if cluster is None:
        cluster = []  
    if visited is None:
        visited = set()  
    if (row, col) in visited:
        return cluster
    visited.add((row, col))
    cluster.append((row, col))
    
    deadStonePositions = findingEmptyPositions(board, (row, col))
    if len(deadStonePositions) == 0 or not deadStonePositions:
        updatedBoard = board
    else:
        for positions in deadStonePositions:
            board[positions[0]][positions[1]] = 0
        updatedBoard = board

    validLocationPoints = []
    if 0 <= row - 1 < 5:
        validLocationPoints.append((row - 1, col))
    if 0 <= row + 1 < 5:
        validLocationPoints.append((row + 1, col))
    if 0 <= col - 1 < 5:
        validLocationPoints.append((row, col - 1))
    if 0 <= col + 1 < 5:
        validLocationPoints.append((row, col + 1))

    adjacentToBeFound = []
    for point in validLocationPoints:
        if updatedBoard[point[0]][point[1]] == updatedBoard[row][col]:
            adjacentToBeFound.append(point)
    for neighbor in adjacentToBeFound:
        findingRelatedCluster(board, neighbor[0], neighbor[1], cluster, visited)
    
    return cluster


def findingAllLegalMoves(board, prevBoard, myChip):
    getLegalMoves = []
    for i in range(5):
        for j in range(5):
            if board[i][j] != 0:
                # If the position that we are checking currently is already occupied so we need to consider it and just skip it
                continue
            # copy the board to different location to avaoid any inplace update 
            duplicateBoard = copy.deepcopy(board)
            duplicateBoard[i][j] = myChip
            conquoredPositions = findingEmptyPositions(duplicateBoard, gettingPlayerOpponenet(myChip))
            duplicateBoard = removingDeadPositions(duplicateBoard, gettingPlayerOpponenet(myChip))
            ckeckKOFlag = True
            for r in range(5):
                for c in range(5):
                    if duplicateBoard[r][c] != prevBoard[r][c]:
                        ckeckKOFlag = False
                        break
                if not ckeckKOFlag:
                    break
            if checkingLiberty(duplicateBoard, i, j) >= 1 and not (conquoredPositions and ckeckKOFlag):
                getLegalMoves.append((i, j))
    return getLegalMoves



def alphaBetaPruning(currBoard, prevBoard, maximumDepthToGo, alpha, beta, myChip, isRoot=True, heuristicVal=None, currentOpponent=None):
    
    if isRoot:
        moves = []
        mostOptimalBestestMove = 0
        copyCurrBoard = copy.deepcopy(currBoard)
        for move in findingAllLegalMoves(currBoard, prevBoard, myChip):
            nextPossibleStateMove = copy.deepcopy(currBoard)
            nextPossibleStateMove[move[0]][move[1]] = myChip
            nextPossibleStateMove = removingDeadPositions(nextPossibleStateMove, gettingPlayerOpponenet(myChip))
            getApproximateHueristic = approximationHueristicFunction(nextPossibleStateMove,gettingPlayerOpponenet(myChip),myChip)
            evaluation = alphaBetaPruning(nextPossibleStateMove, copyCurrBoard,maximumDepthToGo, alpha, beta,myChip,isRoot=False,heuristicVal=getApproximateHueristic,currentOpponent=gettingPlayerOpponenet(myChip))
            calculatedPerformanceScore = (-8 * evaluation) / 8
            if calculatedPerformanceScore > mostOptimalBestestMove or not moves or len(moves) == 0:
                mostOptimalBestestMove = calculatedPerformanceScore
                alpha = mostOptimalBestestMove
                moves = [move]
            elif calculatedPerformanceScore == mostOptimalBestestMove:
                moves.append(move)

        return moves
    else:
        if maximumDepthToGo == 0:
            return heuristicVal
        # or else we can search deeper as we have the limit for going deep and finding still remain
        mostOptimalBestestMove = heuristicVal
        copyCurrBoardR = copy.deepcopy(currBoard)

        for move in findingAllLegalMoves(currBoard, prevBoard, currentOpponent):
            nextPossibleStateMove = copy.deepcopy(currBoard)
            nextPossibleStateMove[move[0]][move[1]] = currentOpponent
            nextPossibleStateMove = removingDeadPositions(nextPossibleStateMove, gettingPlayerOpponenet(currentOpponent))

            getApproximateHueristic = approximationHueristicFunction(
                nextPossibleStateMove,
                gettingPlayerOpponenet(currentOpponent),
                myChip
            )

            # decreasing the search depth by 1 as we want to go till the last possible threshold of depth in the tree to find min-max using alpha beta
            evaluation = alphaBetaPruning(nextPossibleStateMove, copyCurrBoardR,maximumDepthToGo - 1,alpha,beta,myChip,isRoot=False,
                heuristicVal=getApproximateHueristic,
                currentOpponent=gettingPlayerOpponenet(currentOpponent)
            )

            calculatedPerformanceScore = (-8 * evaluation) / 8

            if calculatedPerformanceScore > mostOptimalBestestMove:
                mostOptimalBestestMove = calculatedPerformanceScore

            newCalculatedPerformanceScore = (-8 * mostOptimalBestestMove) / 8

            if currentOpponent == gettingPlayerOpponenet(myChip):
                myPlayer = newCalculatedPerformanceScore
                if myPlayer < alpha:  
                    return mostOptimalBestestMove
                if mostOptimalBestestMove > beta:
                    beta = mostOptimalBestestMove

            elif currentOpponent == myChip:
                opponent = newCalculatedPerformanceScore
                if opponent < beta:
                    return mostOptimalBestestMove
                if mostOptimalBestestMove > alpha:
                    alpha = mostOptimalBestestMove

        return mostOptimalBestestMove


def main():
    myChip, currBoard, prevBoard = readingGame()
    # initially check if the central board is empty and if soo just put the myPlayer chip there only 
    # if we have the flag of empty as true we no need run through the whole  min max thing
    flag=0
    flagToogle = False
    for i in range(5):
        for j in range(5):
            if currBoard[i][j] != 0:
                if i == 2 and j == 2:
                    flagToogle = True
                flag += 1

    if (flag==0 and myChip==1) or (flag==1 and myChip==2 and flagToogle is False):
        moveChoosen = [(2,2)]
    else:
        alphaValue = float('-inf')
        betaValue = float('inf')
        moveChoosen = alphaBetaPruning(currBoard, prevBoard, 2, alphaValue, betaValue, myChip)
    
    if moveChoosen == [] or moveChoosen == None or len(moveChoosen) == 0:
        nextMoveToMake = ['PASS']
    else:
        if not moveChoosen or len(moveChoosen) == 0:
            nextMoveToMake = 'PASS'
        else:
            nextMoveToMake = pickAMove(moveChoosen)
        # --- RAG & explanation hook (non-intrusive) ---
    import os
    try:
        import rag_module as rag  # separate file in same dir
        # inject your agent functions so rag_module can use them
        rag.checkingLiberty = checkingLiberty
        rag.removingDeadPositions = removingDeadPositions
        rag.gettingPlayerOpponenet = gettingPlayerOpponenet
    except ImportError:
        rag = None

    # Optional: compute a quick eval for logging (no effect on your agent)
    eval_for_log = None
    try:
        if isinstance(nextMoveToMake, tuple):  # only if we actually placed a stone
            nb = copy.deepcopy(currBoard)
            r, c = nextMoveToMake
            nb[r][c] = myChip
            nb = removingDeadPositions(nb, gettingPlayerOpponenet(myChip))
            eval_for_log = approximationHueristicFunction(nb, gettingPlayerOpponenet(myChip), myChip)
    except Exception:
        pass

    # absolute path so you know exactly where the file is
    EXPLAIN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "explanation.txt")

    if rag:
        try:
            # If your move is not a tuple, treat it as PASS for explanation purposes
            move_for_exp = nextMoveToMake if isinstance(nextMoveToMake, tuple) else 'PASS'
            print(f"[RAG] writing explanation to: {EXPLAIN_PATH} | move: {move_for_exp}")
            rag.build_and_record_explanation(
                currBoard=currBoard,
                prevBoard=prevBoard,
                move=move_for_exp,
                myChip=myChip,
                eval_score=eval_for_log,
                llm="ollama",  # keep "none" unless Ollama is installed & running or claude_mcp if you have claude api key
                explanation_log_path=EXPLAIN_PATH
            )
        except Exception as e:
            print(f"[RAG] skipped due to error: {e}")
    # --- end RAG hook ---

    writingGame(nextMoveToMake)

if __name__ == "__main__":
    main()
