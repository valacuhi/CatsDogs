from game_logic import GameState
from agents.minimax_agent import MinimaxAgent

gs = GameState()
gs.make_move(7, 1, 1)  # Cat plays in middle
mm = MinimaxAgent(depth=4)
move = mm.get_move(gs, 2)
print("Minimax Move:", move)
