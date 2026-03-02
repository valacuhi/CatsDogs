import os
import requests
import re
from agents.base_agent import BaseAgent
from agents.minimax_agent import MinimaxAgent

class LLMAgent(BaseAgent):
    def __init__(self, provider, model_name, temperature, prompt_prefix, fallback_enabled, name="LLMAgent"):
        super().__init__(name)
        self.provider = provider
        self.model_name = model_name
        self.temperature = temperature
        self.prompt_prefix = prompt_prefix
        self.fallback_enabled = fallback_enabled
        self.last_fallback_used = None

    def get_evaluated_moves(self, game_state, player_id, depth=2):
        moves = game_state.get_available_moves()
        evals = []
        mm = MinimaxAgent(depth=depth)
        human_team = 1 if player_id == 2 else 2
        
        # We need a copy of the board since minimax modifies it
        for r, c in moves:
            game_state.board[r][c] = player_id
            score = mm.minimax(game_state, depth - 1, False, -float('inf'), float('inf'), player_id, human_team)
            game_state.board[r][c] = 0
            if score > 50:
                score += 100 # Emphasize winning
            evals.append(((r, c), score))
        evals.sort(key=lambda x: x[1], reverse=True)
        return evals

    def format_board(self, board):
        symbols = {0: '.', 1: 'C', 2: 'D'}
        rows_str = []
        for r in range(len(board)):
            row = [symbols[board[r][c]] for c in range(len(board[0]))]
            rows_str.append(f"Row {r:02d}: " + "  ".join(row))
        return "\n".join(rows_str)

    def get_move(self, game_state, player_id: int):
        self.last_fallback_used = None
        evals = self.get_evaluated_moves(game_state, player_id, depth=2)
        if not evals: return None
        
        safe = [m for m, s in evals if s > -50] or [m for m, s in evals]
        m_str = "\n".join([f"({r}, {c}) [{'Adv' if s>0 else 'Safe'}]" for (r,c), s in evals if (r,c) in safe][:7])
        
        prompt = f"""You are the "Grandmaster Architect" playing a specialized {game_state.rows}x{game_state.cols} version of Tic-Tac-Toe.
You are playing as '{'C' if player_id==1 else 'D'}'. The human player is '{'D' if player_id==1 else 'C'}'. Empty spaces are '.'.

{self.prompt_prefix}

Winning Conditions:
- Horizontal: 3 or 4 in a row (a full row).
- Vertical: 4 or 5 in a column.
- Diagonal: 3 or 4 in a row diagonally.

Current Board State:
{self.format_board(game_state.board)}

{"[URGENT CONTEXT] The human opponent's LAST MOVE was played at Row " + str(game_state.last_move[0]) + ", Column " + str(game_state.last_move[1]) + ". Pay special attention to this area as they are likely building a threat!" if game_state.last_move else ""}

Top Recommended Legal Moves (Row, Column) and their Mathematical Evaluations:
{m_str}

Analyze the board carefully step-by-step:
1. Review the Recommended Legal Moves list provided above.
2. If any move is tagged [GUARANTEED WIN - YOU MUST CHOOSE THIS], you MUST choose it to end the game.
3. If no immediate win exists, choose one of the top [Safe] or [Advantageous] moves that best builds a long-term strategy or blocks the opponent's "LAST MOVE" threat.
4. Do not choose moves tagged [BLUNDER] unless there are absolutely no other options.

You MUST write down your thought process briefly, evaluating rows, columns, and diagonals.
Finally, your very last line MUST be exactly: "MOVE: r, c" where r and c are the coordinates of your chosen move.
"""
        try:
            result_text = ""
            if self.provider == "Local Ollama":
                url = "http://localhost:11434/api/chat"
                data = {
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"temperature": float(self.temperature)}
                }
                response = requests.post(url, json=data)
                response.raise_for_status()
                result_text = response.json()["message"]["content"]
                
            elif self.provider == "Google Gemini":
                api_key = os.environ.get("GOOGLE_API_KEY")
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY not found in environment.")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={api_key}"
                headers = {"Content-Type": "application/json"}
                data = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": float(self.temperature)}
                }
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                result_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                
            elif self.provider == "OpenRouter":
                api_key = os.environ.get("OPENROUTER_API_KEY")
                if not api_key:
                    raise ValueError("OPENROUTER_API_KEY not found in environment.")
                url = "https://openrouter.ai/api/v1/chat/completions"
                headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
                data = {
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": float(self.temperature)
                }
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                result_text = response.json()["choices"][0]["message"]["content"]
            else:
                raise ValueError(f"Unknown AI Provider: {self.provider}")

            # Parse the response
            match = re.search(r"MOVE:\s*(\d+),\s*(\d+)", result_text, re.IGNORECASE)
            if match:
                r, c = int(match.group(1)), int(match.group(2))
                raw_moves = [m[0] for m in evals]
                if (r, c) in raw_moves:
                    return (r, c)
            
            print(f"AI returned invalid format or illegal move: {result_text}")
            if self.fallback_enabled:
                self.last_fallback_used = "mm(4)"
                mm = MinimaxAgent(depth=4)
                return mm.get_move(game_state, player_id)
            else:
                raise ValueError(f"Connection failed to {self.provider}. Enable Fallback to use Minimax.")

        except Exception as e:
            print(f"LLMAgent Error: {e}")
            if self.fallback_enabled:
                self.last_fallback_used = "mm(4)"
                mm = MinimaxAgent(depth=4)
                return mm.get_move(game_state, player_id)
            else:
                raise ValueError(f"Connection failed to {self.provider}. Enable Fallback to use Minimax.")
