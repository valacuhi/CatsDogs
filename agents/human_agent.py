from agents.base_agent import BaseAgent

class HumanAgent(BaseAgent):
    def __init__(self, name="Human"):
        super().__init__(name)

    def get_move(self, game_state, player_id: int):
        """
        The HumanAgent does not actually compute a move.
        It returns None to signal the GameController to yield and wait for an external (GUI) input.
        """
        return None
