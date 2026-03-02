import math
import random
from agents.base_agent import BaseAgent

class MinimaxAgent(BaseAgent):
    def __init__(self, depth=4, name="Minimax"):
        super().__init__(name)
        self.depth = depth

    def get_move(self, game_state, player_id: int):
        best_eval = -math.inf
        best_move = None
        moves = game_state.get_available_moves()
        
        if not moves or game_state.check_win()[0] != 0:
            return None
            
        random.shuffle(moves)
        alpha = -math.inf
        beta = math.inf
        human_team = 1 if player_id == 2 else 2
        
        for r, c in moves:
            game_state.board[r][c] = player_id
            eval = self.minimax(game_state, self.depth - 1, False, alpha, beta, player_id, human_team)
            game_state.board[r][c] = 0
            
            if eval > best_eval:
                best_eval = eval
                best_move = (r, c)
            alpha = max(alpha, eval)
            
        if best_move is None and moves:
            best_move = moves[0]
            
        return best_move

    def minimax(self, game_state, depth, is_maximizing, alpha, beta, ai_team, human_team):
        winner, _ = game_state.check_win()
        if winner == ai_team:
            return 100 + depth  # AI wins
        elif winner == human_team:
            return -100 - depth # Human wins
        elif game_state.is_draw():
            return 0
        
        if depth == 0:
            return 0
            
        moves = game_state.get_available_moves()
        if not moves:
            return 0

        if is_maximizing:
            max_eval = -math.inf
            for r, c in moves:
                game_state.board[r][c] = ai_team
                eval = self.minimax(game_state, depth - 1, False, alpha, beta, ai_team, human_team)
                game_state.board[r][c] = 0
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for r, c in moves:
                game_state.board[r][c] = human_team
                eval = self.minimax(game_state, depth - 1, True, alpha, beta, ai_team, human_team)
                game_state.board[r][c] = 0
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval
