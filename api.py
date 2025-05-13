import random
import requests
from copy import deepcopy

import uvicorn
from typing import List
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException


EMPTY = 0

# function
def print_board(board):
    for a in board:
        print(a)


def create_board():
    return [[0 for _ in range(7)] for _ in range(6)]

def is_board_empty(board):
    return all(cell == 0 for row in board for cell in row)

# Lấy hàng sẽ được thả tới
def get_row(board, col):
    row = len(board)
    if row == -1: return None
    while board[row][col] != 0:
        row -= 1
    return row

# Check nước đi nào đó có thắng không
def is_winning_move(board, player, col):
    row = get_row(board, col)
    board[row][col] = player
    for r in range(len(board)):
        for c in range(len(board[0]) - 3):
            if all(board[r][c + i] == player for i in range(4)):
                return True
    for c in range(len(board[0])):
        for r in range(len(board) - 3):
            if all(board[r + i][c] == player for i in range(4)):
                return True
    for r in range(len(board) - 3):
        for c in range(len(board[0]) - 3):
            if all(board[r + i][c + i] == player for i in range(4)):
                return True
    for r in range(3, len(board)):
        for c in range(len(board[0]) - 3):
            if all(board[r - i][c + i] == player for i in range(4)):
                return True
    return False

def state_new(old, new, state):
    for i in range(len(old)):
        for j in range(len(old[0])):
            if old[i][j] * new[i][j] == 0 and old[i][j] != new[i][j] and new[i][j] > 0:
                state += str(j + 1)
                return state
    return state

def output(old_board, new_board, player, str_state, valid_moves):
    str_state = state_new(old_board, new_board, str_state)
    for col in valid_moves:
        if is_winning_move(new_board, player, col) or is_winning_move(new_board, 3 - player, col):
            return col, str_state

    col = random.choice(valid_moves)

    try:
        url = f"http://ludolab.net/solve/connect4?position={str_state}&level=10"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        response = response.json()
        print(response)
        # response.sort(key=lambda move: (-int(move["score"]), move["move"]))
        best_move = max(response, key=lambda move: move["score"])
        col = int(best_move["move"]) - 1
    except requests.exceptions.RequestException as e:
        print(f"🌐 Request failed: {e}")
    except (ValueError, KeyError) as e:
        print(f"❗ Error API: {e}")
    except Exception as e:
        print(f"⚠️ ERROR: {e}")

    if col not in valid_moves:
        col = random.choice(valid_moves)

    return col, str_state

app = FastAPI()

class GameState(BaseModel):
    board: List[List[int]]
    current_player: int
    valid_moves: List[int]
    # is_new_game: bool

class AIResponse(BaseModel):
    move: int

old_board = create_board()
str_state = ""

@app.get("/api/test")
async def health_check():
    return {"status": "ok", "message": "Server is running"}

@app.post("/api/connect4-move")
async def make_move(game_state: GameState) -> AIResponse:
    try:
        global old_board, str_state
        if sum(1 for row in game_state.board for cell in row if cell > 0) <= 1:
            old_board = create_board()
            str_state = ""
        new_board = deepcopy(game_state.board)

        print("new board")
        print_board(new_board)

        print(game_state.current_player)
        print(game_state)
        if not game_state.valid_moves:
            raise ValueError("No valid move")

        selected_move, str_state = output(old_board, new_board, game_state.current_player ,str_state, game_state.valid_moves)
        str_state += str(selected_move + 1)

        old_board = deepcopy(new_board)
        row = get_row(old_board, selected_move)
        old_board[row][selected_move] = game_state.current_player
        print("old board")
        print_board(old_board)

        print("Choose", selected_move)

        return AIResponse(move=selected_move)
    except Exception as e:
        if game_state.valid_moves:
            return AIResponse(move=game_state.valid_moves[0])
        raise HTTPException(status_code=400, detail=str(e))