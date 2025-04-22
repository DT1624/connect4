import numpy as np
import random

ROWS = 6
COLS = 7
AI = 1  # player 1
PLAYER = 2  # player2
EMPTY = 0
MAX_DEPTH = 1  # Độ sâu tìm kiếm

# Thứ tự nước đi ưu tiên (trung tâm trước)
move_order = [3, 2, 4, 1, 5, 0, 6]

# tạo bảng khi tự chơi
def create_board():
    return np.zeros((ROWS, COLS), dtype=int)

# kiểm tra 1 cột có valid
def is_valid_move(board, col):
    return col >= 0 and col < COLS and board[0][col] == EMPTY

# lấy tất cả các cột valid
def get_valid_moves(board):
    return [col for col in range(COLS) if is_valid_move(board, col)]

# gán giá trị cho ô trong bảng
def drop_piece(board, row, col, player):
    board[row][col] = player

# in bảng
def print_board(board):
    print(np.where(board == EMPTY, 0, np.where(board == AI, AI, PLAYER)))

   
# kiểm tra nước đi đã thắng chưa 
def is_winning_move(board, player):
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(board[r][c + i] == player for i in range(4)):
                return True
    for c in range(COLS):
        for r in range(ROWS - 3):
            if all(board[r + i][c] == player for i in range(4)):
                return True
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r + i][c + i] == player for i in range(4)):
                return True
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if all(board[r - i][c + i] == player for i in range(4)):
                return True
    return False

# kiểm tra có full board và hòa chưa
def is_draw(board):
    return all(board[0][col] != EMPTY for col in range(COLS))

# lấy vị trí row thấp nhất trong columns
def get_row(board, col):
    row = ROWS - 1
    while(board[row][col] != EMPTY):
        row -= 1
    return row
    
#  cần điều chỉnh tham số
def evaluate_window(window, player):
    score = 0
    opp_piece = AI if player == PLAYER else AI
    
    if window.count(player) == 4:
        score += 5
    elif window.count(player) == 3 and window.count(EMPTY) == 1:
        score += 3
    elif window.count(player) == 2 and window.count(EMPTY) == 2:
        score += 1
    
    if window.count(opp_piece) == 3 and window.count(EMPTY) == 1:
        score -= 3
    
    return score

def score_position(board, piece):
    score = 0
    
    # Trung tâm
    center_array = [int(i) for i in list(board[:, COLS // 2])]
    score += center_array.count(piece) * 3
    
    # Hàng ngang
    for r in range(ROWS):
        row_array = [int(i) for i in list(board[r, :])]
        for c in range(COLS-3):
            score += evaluate_window(row_array[c:c+4], piece)
    
    # Cột dọc
    for c in range(COLS):
        col_array = [int(i) for i in list(board[:, c])]
        for r in range(ROWS-3):
            score += evaluate_window(col_array[r:r+4], piece)
    
    # Đường chéo \
    for r in range(ROWS-3):
        for c in range(COLS-3):
            window = [board[r+i][c+i] for i in range(4)]
            score += evaluate_window(window, piece)
    
    # Đường chéo /
    for r in range(3, ROWS):
        for c in range(COLS-3):
            window = [board[r-i][c+i] for i in range(4)]
            score += evaluate_window(window, piece)
    
    return score


def minimax(board, player, depth, alpha, beta, maximizingPlayer):
    valid_moves = get_valid_moves(board)
    # print(depth, valid_moves)
    
    if depth == 0:
        return (None, score_position(board, player))
    
    best_col = random.choice(valid_moves)
    if maximizingPlayer: # đang muốn tìm tối đa
        value = -np.inf

        for col in move_order:
            if col in valid_moves:
                row = get_row(board, col)
                temp_board = board.copy()
                drop_piece(temp_board, row, col, player)
                new_score = minimax(temp_board, player, depth-1, alpha, beta, False)[1] # tìm nước đi làm tối thiểu đối thủ
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
                
        # print(player, best_col, value)
        return best_col, value
    else: # đang ở nước đi tối thiếu cho đối thủ
        value = np.inf

        for col in move_order:
            if col in valid_moves:
                row = get_row(board, col)
                temp_board = board.copy()
                drop_piece(temp_board, row, col, player)
                new_score = minimax(temp_board, player, depth-1, alpha, beta, True)[1] # tìm nước đi tối đa cho cá nhân
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
                
        # print(player, best_col, value)
        return best_col, value

def play_game(curent_player):
    board = create_board()
    # người bắt đầu
    player = curent_player 
    print_board(board)
    while True:
        if is_draw(board):
            print("Draw")
            break
        
        if(player == PLAYER):
            choose = int(input(f"Player {player} choose: "))
            # choose, score = minimax(board, player, MAX_DEPTH, -np.inf, np.inf, player == curent_player)
            # print(player, score)
            while not is_valid_move(board, choose):
                choose = int(input("Invalid! Repeat choose: "))
            row = get_row(board, choose)
            board[row][choose] = player
            print_board(board)
            if is_winning_move(board, player):
                print("Player", player, "win!")
                break
            player = PLAYER if player == AI else AI
        else:
            choose, score = minimax(board, player, MAX_DEPTH, -np.inf, np.inf, True)
            print(player, score)
            print((f"Player {player} choose: "), choose)
            row = get_row(board, choose)
            board[row][choose] = player
            print_board(board)
            if(is_winning_move(board, player)):
                print("Player", player, "win!")
                break
            player = PLAYER if player == AI else AI

# if __name__ == "__main__":
#     play_game(PLAYER)
    
# from fastapi import FastAPI, HTTPException
# import random
# import uvicorn
# import numpy as np
# from pydantic import BaseModel
# from typing import List
# from pyngrok import ngrok  # Import Ngrok

# app = FastAPI()

# class GameState(BaseModel):
#     board: List[List[int]]
#     current_player: int
#     valid_moves: List[int]

# class AIResponse(BaseModel):
#     move: int

# MAX_DEPTH = 4  

# def minimax(board, depth, alpha, beta, maximizing_player, current_player):
#     return random.choice([move for move in range(len(board[0])) if board[0][move] == 0])

# @app.post("/api/connect4-move")
# async def make_move(game_state: GameState) -> AIResponse:
#     print("")
#     try:
#         if not game_state.valid_moves:
#             raise ValueError("Không có nước đi hợp lệ")
            
#         selected_move = minimax(game_state.board, MAX_DEPTH, -np.inf, np.inf, True, game_state.current_player)
        
#         return AIResponse(move=selected_move)
#     except Exception as e:
#         if game_state.valid_moves:
#             return AIResponse(move=game_state.valid_moves[0])
#         raise HTTPException(status_code=400, detail=str(e))


# if __name__ == "__main__":
#     # Mở cổng nội bộ chạy Uvicorn
#     port = 8080
#     public_url = ngrok.connect(port).public_url  # Kết nối ngrok
#     print(f"🔥 Public URL: {public_url}")  # Hiển thị link API

#     # Chạy FastAPI với Uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=port)

import requests

url = "http://ludolab.net/solve/connect4?position=4444444444&level=10"

try:
    response = requests.get(url)
    response.raise_for_status()  # Tự động báo lỗi nếu HTTP status code không phải 200-299
    
    try:
        data = response.json()
        print(data)
    except requests.exceptions.JSONDecodeError:
        print("Không thể giải mã JSON, phản hồi từ server:")
        print(response.text)

except requests.exceptions.RequestException as e:
    print(f"Lỗi khi gửi request: {e}")
