import json
import os
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

# def state_new1(old, new, state):
#     for j in range(len(old[0])):
#         for i in range(len(old)):
#             if old[i][j] * new[i][j] == 0 and old[i][j] != new[i][j]:
#                 state += str(j + 1)
#                 return state
#             if old[i][j] != 0:
#                 break
#     return state
def state_new(old: list[list[int]], new: list[list[int]], state: str) -> str:
    for col in range(len(old[0])):
        for row in range(len(old)):
            old_cell = old[row][col]
            new_cell = new[row][col]
            if old_cell != new_cell and old_cell == 0 and new_cell > 0:
                return state + str(col + 1)

            if old_cell != 0:
                break  # Không cần xét tiếp cột này nếu ô đầu đã khác 0
    return state

# kiểm tra 1 cột có valid
def is_valid_move(board, col):
    return board[0][col] == EMPTY

# lấy tất cả các cột valid
def get_valid_moves(board):
    return [col for col in range(len(board[0])) if is_valid_move(board, col)]

def get_data():
    filename = "board_response_test.jsonl"
    existing_data_map = {}
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for line_number, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            obj = json.loads(line)
                            key = obj.get("board")
                            value = obj.get("response")
                            key = json.dumps(key, sort_keys=False)
                            if key is not None:
                                existing_data_map[key] = value
                        except json.JSONDecodeError as e:
                            print(f"Error JSON at line {line_number}: {e}")
        except Exception as e:
            print(f"Could not read '{filename}': {e}")

    return existing_data_map

def output(old_board, new_board, str_state, valid_moves, data_map):
    str_state = state_new(old_board, new_board, str_state)

    col = random.choice(valid_moves)
    key = json.dumps(new_board, sort_keys=False)
    if key in data_map:
        response = data_map[key]
        # print(response)
        best_move = max(response, key=lambda move: move["score"])
        col = int(best_move["move"]) - 1
        return col, str_state

    try:
        url = f"http://ludolab.net/solve/connect4?position={str_state}&level=10"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        response = response.json()
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
data_map = get_data()

@app.get("/api/test")
async def health_check():
    return {"status": "ok", "message": "Server is running"}

@app.post("/api/connect4-move")
async def make_move(game_state: GameState) -> AIResponse:
    try:
        global old_board, str_state, data_map
        if sum(1 for row in game_state.board for cell in row if cell != 0) <= 1:
            old_board = create_board()
            str_state = ""
        new_board = [row[:] for row in game_state.board]

        if not game_state.valid_moves:
            raise ValueError("No valid move")

        selected_move, str_state = output(old_board, new_board, str_state, game_state.valid_moves, data_map)
        str_state += str(selected_move + 1)

        old_board = [row[:] for row in new_board]
        row = get_row(old_board, selected_move)
        old_board[row][selected_move] = game_state.current_player
        # print("old board")
        # print_board(old_board)

        # print("Choose", selected_move)

        return AIResponse(move=selected_move)
    except Exception as e:
        if game_state.valid_moves:
            return AIResponse(move=game_state.valid_moves[0])
        raise HTTPException(status_code=400, detail=str(e))