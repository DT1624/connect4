import random
import requests
import numpy as np
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
    row = len(board) - 1
    while board[row][col] != 0:
        print(row, col, board[row][col])
        if row == -1:
            return None
        row -= 1
    return row

# Check nước đi nào đó có thắng không
def is_winning_move(board, player, col):
    board_copy = deepcopy(board)
    row = get_row(board_copy, col)
    board_copy[row][col] = player
    for r in range(len(board_copy)):
        for c in range(len(board_copy[0]) - 3):
            if all(board_copy[r][c + i] == player for i in range(4)):
                return True
    for c in range(len(board_copy[0])):
        for r in range(len(board_copy) - 3):
            if all(board_copy[r + i][c] == player for i in range(4)):
                return True
    for r in range(len(board_copy) - 3):
        for c in range(len(board_copy[0]) - 3):
            if all(board_copy[r + i][c + i] == player for i in range(4)):
                return True
    for r in range(3, len(board_copy)):
        for c in range(len(board_copy[0]) - 3):
            if all(board_copy[r - i][c + i] == player for i in range(4)):
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
    print(f"str = {str_state}")

    try:
        url = f"http://connect4.gamesolver.org/solve?pos={str_state}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://connect4.gamesolver.org/",
            "Origin": "https://connect4.gamesolver.org",
            "Connection": "keep-alive",
            "Sec-Fetch-Site": "same-origin",
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response = response.json()
        scores = response['score']
        max_val = np.max(scores)
        col = random.choice([i for i, v in enumerate(scores) if v == max_val])
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


def is_draw(board):
    return sum(1 for row in board for cell in row if cell == 0) == 0

def play_game(curent_player):
    # khởi tạo 2 board và str_state ban đầu
    old_board = create_board() #board sau lượt AI
    str_state = ""

    all_cells = [(r, c) for r in range(len(old_board)) for c in range(len(old_board[0]))]
    random_cells = random.sample(all_cells, 2)
    for r, c in random_cells:
        old_board[r][c] = -1

    new_board = deepcopy(old_board)
    player = curent_player
    print("Old board")
    print_board(old_board)

    while True:
        if is_draw(old_board):
            print("Draw")
            break

        if(player == 1):
            choose = int(input(f"Player {player} choose: "))
            # choose =
            # while not is_valid_move(old_board, choose):
            #     choose = int(input("Invalid! Repeat choose: "))
            row = get_row(old_board, choose)
            new_board = deepcopy(old_board)
            new_board[row][choose] = player
            print("New board")
            print_board(new_board)
            if is_winning_move(new_board, player, choose):
                print("Player", player, "win!")
                break
            player = 1 if player == 2 else 2
        else:
            # choose, score = minimax(board, player, MAX_DEPTH, -np.inf, np.inf, True)
            (choose, str_state) = output(old_board, new_board, player, str_state, [0, 1, 2, 3, 4, 5, 6])
            str_state += str(choose + 1)
            print((f"Player {player} choose: "), choose)
            row = get_row(new_board, choose)
            old_board = deepcopy(new_board)
            old_board[row][choose] = player
            print("Old board")
            print_board(old_board)
            if is_winning_move(old_board, player, choose):
                print("Player", player, "win!")
                break
            player = 1 if player == 2 else 2

if __name__ == "__main__":
    play_game(1)