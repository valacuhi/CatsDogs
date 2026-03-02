class BaseAgent:
    def __init__(self, name="BaseAgent"):
        self.name = name

    def get_move(self, game_state, player_id: int):
        """
        Calculates and returns a move for this agent.
        :param game_state: The current GameState object.
        :param player_id: The integer representing this player on the board (e.g. 1 or 2).
        :return: (r, c) tuple of the chosen move.
        """
        raise NotImplementedError("Agents must implement get_move()")
