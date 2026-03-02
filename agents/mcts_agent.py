import random
from agents.base_agent import BaseAgent

class MCTSAgent(BaseAgent):
    def __init__(self, simulations=1000, name="Monte Carlo"):
        super().__init__(name)
        self.simulations = simulations

    def get_move(self, game_state, player_id: int):
        moves = game_state.get_available_moves()
        if not moves or game_state.check_win()[0] != 0:
            return None
            
        human_team = 1 if player_id == 2 else 2
        best_move = None
        best_score = -float('inf')
        
        sims_per_move = max(10, self.simulations // len(moves))
        original_board = [row[:] for row in game_state.board]
        
        for r, c in moves:
            score = 0
            for _ in range(sims_per_move):
                # Restore board for simulation
                for ir in range(game_state.rows):
                    for ic in range(game_state.cols):
                        game_state.board[ir][ic] = original_board[ir][ic]
                
                game_state.board[r][c] = player_id
                current_player = human_team
                
                while True:
                    winner, _ = game_state.check_win()
                    if winner != 0:
                        if winner == player_id:
                            score += 1
                        elif winner == human_team:
                            score -= 2 # Penalize losses heavier
                        break
                        
                    temp_moves = game_state.get_available_moves()
                    if not temp_moves:
                        break # draw
                        
                    nr, nc = random.choice(temp_moves)
                    game_state.board[nr][nc] = current_player
                    current_player = 1 if current_player == 2 else 2
            
            if score > best_score:
                best_score = score
                best_move = (r, c)
                
        # Restore original board completely after all simulations
        game_state.board = [row[:] for row in original_board]
        
        if best_move is None and moves:
            best_move = random.choice(moves)
            
        return best_move
