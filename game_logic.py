import math
import random

class GameState:
    def __init__(self):
        self.rows = 15
        self.cols = 3
        # 0 = Empty, 1 = Cat (Player 1), 2 = Dog (Player 2 / AI)
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.current_turn = 1 # 1 always starts (Cat)

    def reset(self):
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.current_turn = 1

    def make_move(self, r, c, player):
        if self.board[r][c] == 0:
            self.board[r][c] = player
            return True
        return False

    def check_win(self):
        """
        Scans the board and returns (winning_player, [(r1, c1), ...]) or (0, None).
        Conditions: Vert: 4, Horiz: 3, Diag: 3.
        """
        # Horizontal: 3
        for r in range(self.rows):
            if self.board[r][0] != 0 and self.board[r][0] == self.board[r][1] == self.board[r][2]:
                return self.board[r][0], [(r, 0), (r, 1), (r, 2)]

        # Vertical: 4
        for r in range(self.rows - 3):
            for c in range(self.cols):
                if self.board[r][c] != 0 and self.board[r][c] == self.board[r+1][c] == self.board[r+2][c] == self.board[r+3][c]:
                    return self.board[r][c], [(r, c), (r+1, c), (r+2, c), (r+3, c)]

        # Diagonal: 3 (Top-left to Bottom-right & Bottom-left to Top-right)
        for r in range(self.rows - 2):
            for c in range(self.cols - 2):
                # Right-down
                if self.board[r][c] != 0 and self.board[r][c] == self.board[r+1][c+1] == self.board[r+2][c+2]:
                    return self.board[r][c], [(r, c), (r+1, c+1), (r+2, c+2)]
                # Right-up (starting from r+2)
                if self.board[r+2][c] != 0 and self.board[r+2][c] == self.board[r+1][c+1] == self.board[r][c+2]:
                    return self.board[r+2][c], [(r+2, c), (r+1, c+1), (r, c+2)]

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
            # If empty, return middle of the board to start
            return [(7, 1)]

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

    def minimax(self, depth, is_maximizing, alpha, beta):
        winner, _ = self.check_win()
        if winner == 2:
            return 100 + depth  # AI wins (fastest win)
        elif winner == 1:
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
                self.board[r][c] = 2
                eval = self.minimax(depth - 1, False, alpha, beta)
                self.board[r][c] = 0
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for r, c in moves:
                self.board[r][c] = 1
                eval = self.minimax(depth - 1, True, alpha, beta)
                self.board[r][c] = 0
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def get_best_move(self, depth=4):
        """
        Returns the best move (r, c) for Player 2 (Dog) using Minimax with Alpha-Beta pruning.
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
        
        for r, c in moves:
            self.board[r][c] = 2
            eval = self.minimax(depth - 1, False, alpha, beta)
            self.board[r][c] = 0
            
            if eval > best_eval:
                best_eval = eval
                best_move = (r, c)
            alpha = max(alpha, eval)
            
        # Fallback if somehow nothing is better
        if best_move is None and moves:
            best_move = moves[0]
            
        return best_move
