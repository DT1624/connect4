import math
import random
import time

import requests
import numpy as np

from typing import List
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

# clone board
def clone_board(board):
    return [row[:] for row in board]

# In bảng
def print_board(board):
    for row in board:
        print(" ".join(f"{cell:>2}" for cell in row))

def create_board():
    return [[0 for _ in range(7)] for _ in range(6)]

# Tạo bảng với K ô bị block
def add_block(board, K=2):
    all_cells = [(r, c) for r in range(6) for c in range(7)]
    random_cells = random.sample(all_cells, K)
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
    board_copy = clone_board(board) # copy để tránh thay đổi
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
                print("win", player, row, col, 2)
                return True
    # Duyệt các đường chéo cùng hướng đường chéo chính
    for r in range(len(board_copy) - 3):
        for c in range(len(board_copy[0]) - 3):
            if all(board_copy[r + i][c + i] == player for i in range(4)):
                print("win", player, row, col, 3)
                return True
    # Duyệt các đường chéo cùng hướng đường chéo phụ
    for r in range(3, len(board_copy)):
        for c in range(len(board_copy[0]) - 3):
            if all(board_copy[r - i][c + i] == player for i in range(4)):
                print("win", player, row, col, 4)
                return True
    return False

# Check đac thắng chưa
def is_winning_move(board, player):
    board_copy = clone_board(board) # copy để tránh thay đổi
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

# Hàm check win dựa theo 1 nước đi hiện tại
def is_move_win(board, player, row, col):
    rows, cols = len(board), len(board[0])
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    for dr, dc in directions:
        count_val = 1

        r, c = row - dr, col - dc
        while 0 <= r < rows and 0 <= c < cols and board[r][c] == player:
            count_val += 1
            r -= dr
            c -= dc

        r, c = row + dr, col + dc
        while 0 <= r < rows and 0 <= c < cols and board[r][c] == player:
            count_val += 1
            r += dr
            c += dc

        if count_val >= 4:
            return True
    return False

# Hàm check có nước nào nên đi để đảm bảo không
# 1. Đánh đó chắc chắn thắng (nước đi sẽ tạo 1 vùng 3 trống trải)
def find_depth(board, player):
    not_choose_cols = []
    valid_cols1 = get_valid_cols(board)
    for col1 in valid_cols1:
        count_will_win = 0 # số cột đối thủ đi thì mình sẽ thắng
        board1 = clone_board(board)
        row1 = get_row(board1, col1)
        board1[row1][col1] = player

        # Nếu nước đi thắng luôn thì chọn ngay
        # Ưu tiên thắng luôn trước nên xét trước
        if is_move_win(board1, player, row1, col1):
            return col1, not_choose_cols

        valid_cols2 = get_valid_cols(board1)
        for col2 in valid_cols2:
            count_opp_win = 0  # đếm số cột mà mình đánh tiếp sẽ thua
            board2 = clone_board(board1)
            row2 = get_row(board2, col2)
            board2[row2][col2] = 3-player
            # Đi khiến đối phương thẳng luôn => không nên chọn
            if is_move_win(board2, 3-player, row2, col2):
                if col1 not in not_choose_cols:
                    not_choose_cols.append(col1)
                    break

            valid_cols3 = get_valid_cols(board2)
            for col3 in valid_cols3:
                board3 = clone_board(board2)
                row3 = get_row(board3, col3)
                board3[row3][col3] = player
                # Đi khiến đối phương thẳng luôn => không nên chọn
                if is_move_win(board3, player, row3, col3):
                    count_will_win += 1
                    break # thoát không cần đếm thêm

                valid_cols4 = get_valid_cols(board3)
                for col4 in valid_cols4:
                    board4 = clone_board(board3)
                    row4 = get_row(board4, col4)
                    board4[row4][col4] = 3-player
                    # Đi khiến đối phương thẳng luôn
                    if is_move_win(board4, 3-player, row4, col4):
                        count_opp_win += 1
                        break  # thoát không cần đếm thêm
            if count_opp_win == len(valid_cols3):
                if col1 not in not_choose_cols:
                    not_choose_cols.append(col1)
                    break

        if count_will_win == len(valid_cols2):
            return col1, not_choose_cols # Nếu nước đi làm đối thủ đi nước nào cũng thua
    return -1, not_choose_cols #không xét nữa mà dùng theo kết quả state


# Check bảng hiện tại có hòa không (thường k cần xét)
def is_draw(board):
    return sum(1 for row in board for cell in row if cell == 0) == 0

# Kiểm tra bảng đã kết thúc game chưa
def is_end_game(board):
    return is_winning_move(board, 1) or is_winning_move(board, 2) or is_draw(board)

# Kiểm tra đã chuyển sang ván mới chưa (có 1 hoặc chưa có nước đi)
def is_new_game(board):
    return sum(1 for row in board for cell in row if cell > 0) <= 1

# Đánh giá điểm qua từng window kích thước 4
def evaluate_window(window, player):
    score = 0
    opp_player = 1 if player == 2 else 1

    if window.count(player) == 4:
        score += 1000
    elif window.count(opp_player) == 4:
        score -= 1000
    elif window.count(player) == 3 and window.count(0) == 1:
        score += 50
    elif window.count(opp_player) == 3 and window.count(0) == 1:
        score -= 100
    elif window.count(player) == 2 and window.count(0) == 2:
        score += 10
    elif window.count(opp_player) == 2 and window.count(0) == 2:
        score -= 8

    return score

# Đánh giá điểm thế cờ của player
def score_position(board, player):
    if is_winning_move(board, player):
        return 1000000
    if is_winning_move(board, 3 - player):
        return -1000000
    score = 0

    center_col = len(board[0]) // 2
    center_count = sum([1 for row in range(len(board)) if board[row][center_col] == player])
    score += center_count * 3

    rows = len(board)
    cols = len(board[0])
    for row in range(rows):
        for col in range(cols):
            if col + 3 < cols:
                score += evaluate_window(board[row][col: col + 4], player)
            if row + 3 < rows:
                score += evaluate_window([board[row+i][col] for i in range(4)], player)
            if row + 3 < rows and col + 3 < cols:
                score += evaluate_window([board[row + i][col + i] for i in range(4)], player)
            if row - 3 > 0 and col + 3 < cols:
                score += evaluate_window([board[row - i][col + i] for i in range(4)], player)

    return score

# Hàm minimax
def minimax(board, depth, alpha, beta, player, isMax, max_time=None):
    valid_cols = get_valid_cols(board)
    if is_winning_move(board, player):
        return None, 1000000  # Win
    elif is_winning_move(board, 3 - player):
        return None, -1000000  # Loss
    elif is_draw(board):
        return None, 0  #Draw
    if depth == 0 or (max_time and time.time() > max_time):
        return None, score_position(board, player)

    if isMax:
        value = -math.inf
        column = random.choice(valid_cols)
        for col in valid_cols:
            row = get_row(board, col)
            board[row][col] = player
            new_score = minimax(board, depth-1, alpha, beta, 3-player, not isMax, max_time)[1]
            board[row][col] = 0
            if new_score > value:
                value = new_score
                column = col
            alpha = max(alpha, value)
            if alpha > beta:
                break
        return column, value
    else:
        value = math.inf
        column = random.choice(valid_cols)
        for col in valid_cols:
            row = get_row(board, col)
            board[row][col] = player
            new_score = minimax(board, depth - 1, alpha, beta, 3 - player, not isMax, max_time)[1]
            board[row][col] = 0
            if new_score < value:
                value = new_score
                column = col
            beta = min(beta, value)
            if alpha > beta:
                break
        return column, value

# Iterative Deepening
def iterative_minimax(board, player, max_time=5.0):
    start_time = time.time()
    end_time = start_time + max_time
    best_move = None
    for depth in range(7, 10):
        if time.time() > end_time:
            break
        best_move, score = minimax(board, depth, -math.inf, math.inf, player, True, end_time)
    return best_move

# Tạo state mới
# Chỉ xét các vị trí thay đổi mà vị trí trong bảng cũ là 0 và bảng mới là > 0
# Check ô trên nó có phải -1 không
# bỏ qua ô -1 ở hàng cuối k xét gì
def get_new_state(old, new, state):
    row, col = 6, 7
    for i in range(len(old)):
        for j in range(len(old[0])):
            if old[i][j] == 0 and new[i][j] > 0:
                row, col = i, j
    # Thiếu trường hợp -1 xuất hiện ở hàng cuối thì chưa cập nhật trạng thái
    if (row, col) == (6, 7): # khi chơi trước tại đầu ván
        return state
    if row - 1 >= 0 and new[row-1][col] == -1:
        return state + str(col + 1) + str(col + 1)
    return state + str(col + 1)

# Hàm nhận trạng thái của bảng cũ và bảng hiện tại để tra về nước đi tối ưu
def output(last_board, new_board, player, last_state, valid_moves):
    # lấy trạng thái sau nước đi của đối phương
    last_state = get_new_state(last_board, new_board, last_state)

    # Check liệu có nước đi nào cần ưu tiên không, và những nước đi nên tránh
    # != -1 là có nước đi ưu tiên (sẽ thắng)
    result, not_choose_cols = find_depth(new_board, player)
    if result != -1:
        # Có vị trí ưu tiên, cần kiểm tra xem có thắng được luôn không
        # Nếu chưa thắng luôn thì cần kiểm tra xem có thể thua được không
        if is_will_winning_move(new_board, player, result):
            return result, last_state

    # Check nếu không chặn thì đối thủ có thắng được không
    for col in valid_moves:
        if is_will_winning_move(new_board, 3 - player, col):
            return col, last_state

    # Nếu đánh ở vị trí nào cũng không khiến thua được thì chọn nước tối ưu đã tìm
    if result != -1:
        return result, last_state

    print(valid_moves)
    print(not_choose_cols)
    if len(valid_moves) == len(not_choose_cols):
        return random.choice(valid_moves), last_state

    col = random.choice(valid_moves)
    print(f"str = {last_state}")
    try:
        url = f"http://connect4.gamesolver.org/solve?pos={last_state}"
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
        valid_scores = [score for score in scores if abs(score) < 20]
        print(response)
        print(valid_scores)
        max_val = np.max(valid_scores)
        col = random.choice([i for i, v in enumerate(scores) if v == max_val])
    except requests.exceptions.RequestException as e:
        print(f"🌐 Request failed: {e}")
    except (ValueError, KeyError) as e:
        print(f"❗ Error API: {e}")
    except Exception as e:
        print(f"⚠️ ERROR: {e}")

    # Đảm bảo là nước đi sẽ luôn hợp lệ được
    result_cols = list(set(valid_moves) - set(not_choose_cols))
    if col not in result_cols:
        col = random.choice(result_cols)
    print(f"col choose = {col}")
    return col, last_state

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
        start = time.time()
        global old_board, str_state

        # Nếu mà bắt đầu ván chơi mới
        if sum(1 for row in game_state.board for cell in row if cell > 0) <= 1:
            old_board = create_board()
            str_state = ""
            for col in range(len(game_state.board[0])):
                if game_state.board[5][col] == -1:
                    str_state += str(col + 1)

        new_board = clone_board(game_state.board)
        print("new board")
        print_board(new_board)

        print(f"state = {str_state}")
        print(game_state)

        if not game_state.valid_moves:
            raise ValueError("No valid move")

        selected_move, str_state = output(old_board, new_board, game_state.current_player ,str_state, game_state.valid_moves)
        str_state += str(selected_move + 1)

        row = get_row(new_board, selected_move)
        new_board[row][selected_move] = game_state.current_player
        old_board = clone_board(new_board)
        if row > 0 and old_board[row - 1][selected_move] == -1:
            str_state += str(selected_move + 1)
        print("old board")
        print_board(old_board)

        print("Choose", selected_move)
        print(f"{time.time() - start:.4f}")
        return AIResponse(move=selected_move)
    except Exception as e:
        if game_state.valid_moves:
            return AIResponse(move=game_state.valid_moves[0])
        raise HTTPException(status_code=400, detail=str(e))

def simulate(board, player):
    result = {}
    board_copy = clone_board(board)
    valid_cols = get_valid_cols(board_copy)
    for col in range(len(board_copy[0])):
        if col in valid_cols:
            row = get_row(board, col)
            board_copy[row][col] = player
            new_col = minimax(board_copy, 4, -math.inf, math.inf, 3 - player, True)[0]
            new_row = get_row(board_copy, new_col)
            b_copy = clone_board(board_copy)
            b_copy[new_row][new_col] = 3 - player
            result[col] = score_position(board, player)
        else:
            result[col] = 'Unknow'
    return result

# 2 logic tự chơi
def play_game(current_player):
    global old_board, str_state
    old_board = create_board() #board sau lượt AI
    str_state = ""

    new_board = clone_board(old_board)
    new_board = add_block(new_board)
    player = current_player
    print("Old board")
    print_board(old_board)

    while True:
        start = time.time()
        if is_draw(old_board):
            print("Draw")
            break

        if player == 1:
            print("New board")
            print_board(new_board)
            print(f"state = '{str_state}'")

            valid_moves = get_valid_cols(new_board)
            (choose, str_state) = output(old_board, new_board, player, str_state, valid_moves)
            str_state += str(choose + 1)

            print(f"Player {player} choose: {choose}")
            row = get_row(new_board, choose)
            new_board[row][choose] = player
            old_board = clone_board(new_board)
            if row > 0 and old_board[row - 1][choose] == -1:
                str_state += str(choose + 1)
            player = 1 if player == 2 else 2
        else:
            print("New board")
            print_board(new_board)
            print(f"state = '{str_state}'")

            valid_moves = get_valid_cols(new_board)
            (choose, str_state) = output(old_board, new_board, player, str_state, valid_moves)
            str_state += str(choose + 1)
            print(f"Player {player} choose: {choose}")
            row = get_row(new_board, choose)
            new_board[row][choose] = player
            old_board = clone_board(new_board)
            if row > 0 and old_board[row - 1][choose] == -1:
                str_state += str(choose + 1)
            player = 1 if player == 2 else 2

        if is_winning_move(new_board, 1):
            print("Player 1 win!")
            break
        if is_winning_move(new_board, 2):
            print("Player 2 win!")
            break
        amount_time = time.time() - start
        if amount_time > 10:
            print("Timeout")
            return
        print(f"{time.time() - start:.4f}")

if __name__ == "__main__":
    play_game(1)