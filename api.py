from copy import deepcopy
import requests
import random

from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel
from typing import List

from pyngrok import ngrok

EMPTY = 0

# function
def print_board(board):
    for a in board:
        print(a)

def create_board():
    return [[0 for _ in range(7)] for _ in range(6)]

def is_board_empty(board):
    return all(cell == 0 for row in board for cell in row)

def get_row(board, col):
    for row in reversed(range(len(board))):
        if board[row][col] == EMPTY:
            return row
    return None

def state_new(old, new, state):
    for i in range(len(old)):
        for j in range(len(old[0])):
            if old[i][j] * new[i][j] == 0 and old[i][j] != new[i][j]:
                state += str(j + 1)
                return state
    return state

# kiểm tra 1 cột có valid
def is_valid_move(board, col):
    return board[0][col] == EMPTY

# lấy tất cả các cột valid
def get_valid_moves(board):
    return [col for col in range(len(board[0])) if is_valid_move(board, col)]

def output(old_board, new_board, str_state, valid_moves):
    str_state = state_new(old_board, new_board, str_state)

    col = random.choice(valid_moves)

    try:
        url = f"http://ludolab.net/solve/connect4?position={str_state}&level=10"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        response = response.json()
        print(response)
        # response.sort(key=lambda move: (-int(move["score"]), move["move"]))
        best_move = max(response, key=lambda move: move["score"])
        filtered_moves = [move for move in response if move["score"] >= 0]
        if len(filtered_moves) > 0:
            best_move = random.choice(filtered_moves)
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


# Create API by ngrok
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
        # if game_state.is_new_game:
        #     old_board = create_board()
        #     str_state = ""
        new_board = deepcopy(game_state.board)

        print("new board")
        print_board(new_board)

        print(game_state.current_player)
        print(game_state)
        if not game_state.valid_moves:
            raise ValueError("No valid move")

        selected_move, str_state = output(old_board, new_board, str_state, game_state.valid_moves)
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

# if __name__ == "__main__":
#     port = 8080
#     public_url = ngrok.connect(str(port)).public_url  # Kết nối ngrok
#     print(f"🔥 Public URL: {public_url}")  # Hiển thị link API
#
#     # Chạy FastAPI với Uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=port)