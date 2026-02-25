import math
import random

class GameState:
    def __init__(self, rows=12, cols=3, win_v=4, win_h=3, win_d=3):
        self.rows = rows
        self.cols = cols
        self.win_v = win_v
        self.win_h = win_h
        self.win_d = win_d
        # 0 = Empty, 1 = Cat (Player 1), 2 = Dog (Player 2 / AI)
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.current_turn = 1 # 1 always starts (Cat)
        self.last_move = None

    def reset(self):
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.current_turn = 1
        self.last_move = None

    def make_move(self, r, c, player):
        if self.board[r][c] == 0:
            self.board[r][c] = player
            self.last_move = (r, c)
            return True
        return False

    def check_win(self):
        """
        Scans the board and returns (winning_player, [(r1, c1), ...]) or (0, None).
        Conditions depend on init parameters.
        """
        # Horizontal: win_h
        for r in range(self.rows):
            for c in range(self.cols - self.win_h + 1):
                if self.board[r][c] != 0:
                    win = True
                    for i in range(1, self.win_h):
                        if self.board[r][c+i] != self.board[r][c]:
                            win = False
                            break
                    if win:
                        return self.board[r][c], [(r, c+i) for i in range(self.win_h)]

        # Vertical: win_v
        for r in range(self.rows - self.win_v + 1):
            for c in range(self.cols):
                if self.board[r][c] != 0:
                    win = True
                    for i in range(1, self.win_v):
                        if self.board[r+i][c] != self.board[r][c]:
                            win = False
                            break
                    if win:
                        return self.board[r][c], [(r+i, c) for i in range(self.win_v)]

        # Diagonal: win_d
        for r in range(self.rows - self.win_d + 1):
            for c in range(self.cols - self.win_d + 1):
                # Right-down
                if self.board[r][c] != 0:
                    win = True
                    for i in range(1, self.win_d):
                        if self.board[r+i][c+i] != self.board[r][c]:
                            win = False
                            break
                    if win:
                        return self.board[r][c], [(r+i, c+i) for i in range(self.win_d)]
                
                # Right-up (starting from bottom)
                if self.board[r + self.win_d - 1][c] != 0:
                    win = True
                    for i in range(1, self.win_d):
                        if self.board[r + self.win_d - 1 - i][c+i] != self.board[r + self.win_d - 1][c]:
                            win = False
                            break
                    if win:
                        return self.board[r + self.win_d - 1][c], [(r + self.win_d - 1 - i, c+i) for i in range(self.win_d)]

        return 0, None

    def is_draw(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == 0:
                    return False
        return True

    def get_available_moves(self):
        """
        Optimized Proximity-Based Search.
        Only considers empty cells touching an existing piece.
        If board is empty, returns the middle cell.
        """
        moves = []
        has_piece = False

        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] != 0:
                    has_piece = True
                    break
            if has_piece:
                break

        if not has_piece:
            # If empty, return roughly the middle of the board to start
            return [(self.rows // 2, self.cols // 2)]

        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == 0:
                    # check proximity to a played piece
                    is_proximate = False
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                                if self.board[nr][nc] != 0:
                                    is_proximate = True
                                    break
                        if is_proximate:
                            break
                    if is_proximate:
                        moves.append((r, c))
        return moves

    def minimax(self, depth, is_maximizing, alpha, beta, ai_team, human_team):
        winner, _ = self.check_win()
        if winner == ai_team:
            return 100 + depth  # AI wins (fastest win)
        elif winner == human_team:
            return -100 - depth # Human wins (slowest loss)
        elif self.is_draw():
            return 0
        
        if depth == 0:
            return 0
            
        moves = self.get_available_moves()
        if not moves:
            return 0

        if is_maximizing:
            max_eval = -math.inf
            for r, c in moves:
                self.board[r][c] = ai_team
                eval = self.minimax(depth - 1, False, alpha, beta, ai_team, human_team)
                self.board[r][c] = 0
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for r, c in moves:
                self.board[r][c] = human_team
                eval = self.minimax(depth - 1, True, alpha, beta, ai_team, human_team)
                self.board[r][c] = 0
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def get_best_move(self, ai_team, depth=4):
        """
        Returns the best move (r, c) for the AI using Minimax with Alpha-Beta pruning.
        """
        best_eval = -math.inf
        best_move = None
        moves = self.get_available_moves()
        
        # If no moves or game over, return None
        if not moves or self.check_win()[0] != 0:
            return None
            
        # Add a tiny bit of randomness to avoid deterministic loops where all evals are 0
        random.shuffle(moves)
        
        alpha = -math.inf
        beta = math.inf
        
        human_team = 1 if ai_team == 2 else 2
        
        for r, c in moves:
            self.board[r][c] = ai_team
            eval = self.minimax(depth - 1, False, alpha, beta, ai_team, human_team)
            self.board[r][c] = 0
            
            if eval > best_eval:
                best_eval = eval
                best_move = (r, c)
            alpha = max(alpha, eval)
            
        # Fallback if somehow nothing is better
        if best_move is None and moves:
            best_move = moves[0]
            
        return best_move
