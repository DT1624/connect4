import random
import requests
import numpy as np
from copy import deepcopy

from typing import List
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

# In bảng
def print_board(board):
    for row in board:
        print(" ".join(f"{cell:>2}" for cell in row))

# Tạo bảng với K ô bị block
def create_board(K=2):
    all_cells = [(r, c) for r in range(6) for c in range(7)]
    random_cells = random.sample(all_cells, K)
    board =  [[0 for _ in range(7)] for _ in range(6)]
    for r, c in random_cells:
        board[r][c] = -1
    return board

# Kiểm tra 1 cột có nước đi hợp lệ không
def is_valid_col(board, col):
    for row in range(len(board)):
        if board[row][col] == 0:
            return True
    return False

# Lấy tất cả các cột có nước đi hợp lệ
def get_valid_cols(board):
    return [col for col in range(len(board[0])) if is_valid_col(board, col)]

# Lấy hàng sẽ được thả tới
def get_row(board, col):
    row = len(board) - 1
    while board[row][col] != 0:
        if row == -1:
            return None
        row -= 1
    return row

# Check nước đi nào đó có thắng không
def is_will_winning_move(board, player, col):
    board_copy = deepcopy(board) # copy để tránh thay đổi
    row = get_row(board_copy, col)
    if row is None: # Nếu không có nước đi hợp lệ  cột này
        return False
    # Duyệt các hàng
    board_copy[row][col] = player
    for r in range(len(board_copy)):
        for c in range(len(board_copy[0]) - 3):
            if all(board_copy[r][c + i] == player for i in range(4)):
                print("win", player, row, col, 1)
                return True
    # Duyệt các cột
    for c in range(len(board_copy[0])):
        for r in range(len(board_copy) - 3):
            if all(board_copy[r + i][c] == player for i in range(4)):
                print("win", player, row, col, 1)
                return True
    # Duyệt các đường chéo cùng hướng đường chéo chính
    for r in range(len(board_copy) - 3):
        for c in range(len(board_copy[0]) - 3):
            if all(board_copy[r + i][c + i] == player for i in range(4)):
                print("win", player, row, col, 1)
                return True
    # Duyệt các đường chéo cùng hướng đường chéo phụ
    for r in range(3, len(board_copy)):
        for c in range(len(board_copy[0]) - 3):
            if all(board_copy[r - i][c + i] == player for i in range(4)):
                print("win", player, row, col, 1)
                return True
    return False

# Check đac thắng chưa
def is_winning_move(board, player):
    board_copy = deepcopy(board) # copy để tránh thay đổi
    for r in range(len(board_copy)):
        for c in range(len(board_copy[0]) - 3):
            if all(board_copy[r][c + i] == player for i in range(4)):
                return True
    # Duyệt các cột
    for c in range(len(board_copy[0])):
        for r in range(len(board_copy) - 3):
            if all(board_copy[r + i][c] == player for i in range(4)):
                return True
    # Duyệt các đường chéo cùng hướng đường chéo chính
    for r in range(len(board_copy) - 3):
        for c in range(len(board_copy[0]) - 3):
            if all(board_copy[r + i][c + i] == player for i in range(4)):
                return True
    # Duyệt các đường chéo cùng hướng đường chéo phụ
    for r in range(3, len(board_copy)):
        for c in range(len(board_copy[0]) - 3):
            if all(board_copy[r - i][c + i] == player for i in range(4)):
                return True
    return False

# Check bảng hiện tại có hòa không (thường k cần xét)
def is_draw(board):
    return sum(1 for row in board for cell in row if cell == 0) == 0

# Kiểm tra đã chuyển sang ván mới chưa (có 1 hoặc chưa có nước đi)
def is_new_game(board):
    return sum(1 for row in board for cell in row if cell > 0) <= 1

# Tạo state mới
def get_new_state(old, new, state):
    row, col = 6, 7
    for i in range(len(old)):
        for j in range(len(old[0])):
            if old[i][j] == 0 and new[i][j] > 0:
                row, col = i, j
    if row - 1 >= 0 and new[row-1][col] == -1:
        return state + str(col + 1) + str(col + 1)
    return state + str(col + 1)

def output(old_board, new_board, player, str_state, valid_moves):
    str_state = get_new_state(old_board, new_board, str_state)
    for col in valid_moves:
        if is_will_winning_move(new_board, player, col):
            return col, str_state

    for col in valid_moves:
        if is_will_winning_move(new_board, 3 - player, col):
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




def play_game(current_player):
    # khởi tạo 2 board và str_state ban đầu
    old_board = create_board() #board sau lượt AI
    str_state = ""

    new_board = deepcopy(old_board)
    player = current_player
    print("Old board")
    print_board(old_board)

    while True:
        if is_draw(old_board):
            print("Draw")
            break

        if player == 1:
            choose = int(input(f"Player {player} choose: "))
            # choose =
            # while not is_valid_move(old_board, choose):
            #     choose = int(input("Invalid! Repeat choose: "))
            row = get_row(old_board, choose)
            new_board = deepcopy(old_board)
            new_board[row][choose] = player
            print("New board")
            print_board(new_board)
            if is_winning_move(new_board, player):
                print("Player", player, "win!")
                break
            player = 1 if player == 2 else 2
        else:
            # choose, score = minimax(board, player, MAX_DEPTH, -np.inf, np.inf, True)
            valid_moves = get_valid_cols(new_board)
            (choose, str_state) = output(old_board, new_board, player, str_state, valid_moves)
            str_state += str(choose + 1)
            print(f"Player {player} choose: ", choose)
            row = get_row(new_board, choose)
            old_board = deepcopy(new_board)
            old_board[row][choose] = player
            if row > 0 and old_board[row - 1][choose] == -1:
                str_state += str(choose + 1)
            print("Old board")
            print_board(old_board)
            if is_winning_move(old_board, player):
                print("Player", player, "win!")
                break
            player = 1 if player == 2 else 2

# def minimax(board, )

if __name__ == "__main__":
    play_game(1)