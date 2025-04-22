import json
import os.path
from copy import deepcopy

import requests
import random
import time

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

def is_draw(board):
    return all(cell != EMPTY for cell in board[0])

def get_row(board, col):
    for row in reversed(range(len(board))):
        if board[row][col] == EMPTY:
            return row
    return None

def is_winning_move(board, player):
    rows = len(board)
    cols = len(board[0])

    for r in range(rows):
        for c in range(cols - 3):
            if all(board[r][c + i] == player for i in range(4)):
                return True

    for c in range(cols):
        for r in range(rows - 3):
            if all(board[r + i][c] == player for i in range(4)):
                return True

    for r in range(rows - 3):
        for c in range(cols - 3):
            if all(board[r + i][c + i] == player for i in range(4)):
                return True

    for r in range(3, rows):
        for c in range(cols - 3):
            if all(board[r - i][c + i] == player for i in range(4)):
                return True
    return False


def state_new(old, new, state):
    for i in range(len(old)):
        for j in range(len(old[0])):
            if old[i][j] != new[i][j]:
                state += str(j + 1)
                return state
    return state


def output(old_board, new_board, str_state, existing_data):
    # if it is new game
    if is_board_empty(new_board) or sum(cell != 0 for row in new_board for cell in row) == 1:
        print("This is new game")
        old_board = create_board()
        str_state = ""
    print("old board")
    print_board(old_board)
    print("new board")
    print_board(new_board)
    str_state = state_new(old_board, new_board, str_state)

    # filename = "D:/Tài liệu 2022-2026/(II 2024-2025)/Trí tuệ nhân tạo/ConnectFour - Copy/board_response_test.jsonl"
    col = random.choice(get_valid_moves(new_board))

    check = False
    for item in existing_data:
        if item["board"] == new_board:
            response = item["response"]
            best_move = max(response, key=lambda move: move["score"])
            print(item["response"])
            col = int(best_move["move"]) - 1
            check = True
    if not check:
        print("Not exists")
        try:
            url = f"http://ludolab.net/solve/connect4?position={str_state}&level=10"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            response = response.json()
            response.sort(key=lambda move: (-move["score"], move["move"]))
            print(response)
            best_move = max(response, key=lambda move: move["score"])
            col = int(best_move["move"]) - 1
        except requests.exceptions.RequestException as e:
            print(f"🌐 Request failed: {e}")
        except (ValueError, KeyError) as e:
            print(f"❗ Error API: {e}")
        except Exception as e:
            print(f"⚠️ ERROR: {e}")

    else:
        print("Already exists")

    return col, str_state

    # try:
    #     url = f"http://ludolab.net/solve/connect4?position={str_state}&level=10"
    #     response = requests.get(url, timeout=2)
    #     response.raise_for_status()
    #     data = response.json()
    #     # print(data)
    #     filtered_data = [int(move["move"]) - 1 for move in data if move["score"] >= 0]
    #     print(filtered_data)
    #     for moves in data:
    #         print(moves)
    #
    #     # Get max score move
    #     best_move = max(data, key=lambda move: move["score"])
    #     move = int(best_move["move"]) - 1
    #
    #     if move in valid_moves:
    #         return move, str_state
    #     return random.choice(valid_moves), str_state
    # except requests.exceptions.RequestException as e:
    #     print(f"🌐 Request failed: {e}")
    # except (ValueError, KeyError) as e:
    #     print(f"❗ Error API: {e}")
    # except Exception as e:
    #     print(f"⚠️ ERROR: {e}")
    #
    # return random.choice(valid_moves), str_state

# Create API by ngrok
app = FastAPI()

class GameState(BaseModel):
    board: List[List[int]]
    current_player: int
    valid_moves: List[int]

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
        start_time = time.time()
        print(game_state.current_player)
        if not game_state.valid_moves:
            raise ValueError("No valid move")

        global old_board, str_state, existing_data
        new_board = deepcopy(game_state.board)

        selected_move, str_state = output(old_board, new_board, str_state, existing_data)
        str_state += str(selected_move + 1)

        old_board = deepcopy(new_board)
        row = get_row(old_board, selected_move)
        old_board[row][selected_move] = game_state.current_player

        # check if won, reset old_board, new_board, str_state
        if is_winning_move(old_board, game_state.current_player) or is_draw(old_board):
            if is_winning_move(old_board, game_state.current_player):
                print("You win")
            else:
                print("DRAW")
            old_board = create_board()
            str_state = ""

        print("Choose", selected_move)
        print("time = ", time.time() - start_time)
        return AIResponse(move=selected_move)
    except Exception as e:
        if game_state.valid_moves:
            return AIResponse(move=game_state.valid_moves[0])
        raise HTTPException(status_code=400, detail=str(e))

# kiểm tra 1 cột có valid
def is_valid_move(board, col):
    return board[0][col] == EMPTY

# lấy tất cả các cột valid
def get_valid_moves(board):
    return [col for col in range(len(board[0])) if is_valid_move(board, col)]


def play_game(player):
    board = create_board()
    print_board(board)
    state = ""

    filename = "D:/UET 2022-2026\(II 2024-2025)/Trí tuệ nhân tạo/ConnectFour - Copy/board_response_test.jsonl"
    print(os.path.exists(filename))
    existing_data = []
    with open(filename, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    obj = json.loads(line)
                    existing_data.append(obj)
                except json.JSONDecodeError as e:
                    print(f"Error Jsom {line_number}: {e}")
    print(len(existing_data))

    while True:
        if is_draw(board):
            print("Draw")
            break

        if (player == 1):
            col = int(input(f"Player {player} choose: "))
            while not is_valid_move(board, col):
                col = int(input("Invalid! Repeat choose: "))
            row = get_row(board, col)
            state += str(col + 1)
            board[row][col] = 1
            print_board(board)

            if is_winning_move(board, player):
                print("Player", player, "win!")
                break
            player = 1 if player == 2 else 2
        else:

            valid_moves = get_valid_moves(board)
            col = random.choice(valid_moves)
            check = False
            for item in existing_data:
                if item["board"] == board:
                    response = item["response"]
                    # print(response)
                    best_move = max(response, key=lambda move: move["score"])
                    col = int(best_move["move"]) - 1
                    check = True
            if not check:
                print("Not exists board")
                print(state)
                url = f"http://ludolab.net/solve/connect4?position={state}&level=10"
                response = requests.get(url, timeout=2)
                response.raise_for_status()
                response = response.json()
                response.sort(key=lambda move: (-move["score"], move["move"]))
                best_move = max(response, key=lambda move: move["score"])
                col = int(best_move["move"]) - 1
                data_add = {
                    "board": board,
                    "state": state,
                    "response": response
                }
                with open(filename, "a", encoding="utf-8") as f:
                    f.write(json.dumps(data_add) + "\n")
                print(f"✅ Appended to {filename}")

            print((f"Player {player} choose: "), col)
            state += str(col + 1)
            row = get_row(board, col)
            board[row][col] = 2
            print_board(board)

            if (is_winning_move(board, player)):
                print("Player", player, "win!")
                break
            player = 1 if player == 2 else 2

def get_data(file = "D:/UET 2022-2026/(II 2024-2025)/Trí tuệ nhân tạo/ConnectFour - Copy/board_response_test.jsonl"):
    data = []
    with open(file, "r", encoding="utf-8") as f:
        for number_line, lines in enumerate(f, 1):
            lines = lines.strip()
            if lines:
                try:
                    obj = json.loads(lines)
                    data.append(obj)
                except json.JSONDecodeError as e:
                    print(f"Error Jsom {number_line}: {e}")
    return data

if __name__ == "__main__":
    filename = "D:/UET 2022-2026/(II 2024-2025)/Trí tuệ nhân tạo/ConnectFour - Copy/board_response_test.jsonl"
    print(os.path.exists(filename))
    existing_data = get_data()

    # exising_data = []
    port = 8080
    public_url = ngrok.connect(str(port)).public_url  # Kết nối ngrok
    print(f"🔥 Public URL: {public_url}")  # Hiển thị link API

    # Chạy FastAPI với Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)

# if __name__ == "__main__":
#     play_game(1)

