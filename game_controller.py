import time
import threading

class GameController:
    def __init__(self, game_state, get_p1_fn, get_p2_fn):
        self.game = game_state
        self.get_p1 = get_p1_fn
        self.get_p2 = get_p2_fn
        
        # Callbacks that the GUI can inject
        self.on_board_update = lambda r, c, player, latency: None
        self.on_game_over = lambda winner, coords: None
        self.on_error = lambda err_msg: None
        self.on_ai_thinking = lambda is_thinking, status_text: None

        self._processing_turn = False
        self._stop_event = threading.Event()

    def process_turn(self, human_move=None, human_latency=0.0):
        """
        Processes the next turn. If the current player is a HumanAgent, it expects `human_move` 
        to be provided (e.g., from a GUI click). If it's an AI Agent, it runs in a background thread.
        """
        if getattr(self, 'paused', False):
            return
            
        if self._processing_turn or self.game.check_win()[0] != 0 or self.game.is_draw():
            return
            
        current_agent = self.get_p1() if self.game.current_turn == 1 else self.get_p2()
        
        # If it's a human, we just apply the move directly
        if current_agent.name == "Human":
            if human_move:
                self._apply_move(human_move, ai_latency=human_latency)
            return
            
        # If it's an AI, we spawn a thread so the UI doesn't freeze
        self._processing_turn = True
        self.on_ai_thinking(True, f"AI Thinking ({current_agent.name})...")
        
        def ai_worker():
            try:
                start_time = time.time()
                move = current_agent.get_move(self.game, self.game.current_turn)
                latency = time.time() - start_time
                
                if self._stop_event.is_set():
                    self._processing_turn = False
                    return

                if move:
                    self._apply_move(move, ai_latency=latency)
                else:
                    self.on_error(f"Agent {current_agent.name} failed to return a valid move.")
                    
            except Exception as e:
                self.on_error(str(e))
                
            finally:
                self._processing_turn = False
                self.on_ai_thinking(False, "Ready")

        threading.Thread(target=ai_worker, daemon=True).start()

    def _apply_move(self, move, ai_latency=0.0):
        if not move or self.game.board[move[0]][move[1]] != 0:
            return
            
        r, c = move
        p = self.game.current_turn
        
        self.game.make_move(r, c, p)
        self.game.current_turn = 3 - p
        self.on_board_update(r, c, p, ai_latency)
        
        winner, coords = self.game.check_win()
        if winner != 0 or self.game.is_draw():
            self.on_game_over(winner, coords)
        else:
            # Check if next player is AI and automatically trigger them
            if not getattr(self, 'paused', False):
                next_agent = self.get_p1() if self.game.current_turn == 1 else self.get_p2()
                if next_agent.name != "Human":
                    # Slight delay to allow UI to breathe
                    threading.Timer(0.5, self.process_turn).start()

    def stop(self):
        self._stop_event.set()
