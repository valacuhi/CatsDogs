import threading
import requests
import json
import os
import re
import random

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def format_board(board):
    """
    Returns a string representation of the board for the LLM.
    0 -> Empty (.), 1 -> Cat (C), 2 -> Dog (D)
    """
    symbols = {0: '.', 1: 'C', 2: 'D'}
    rows = len(board)
    cols = len(board[0]) if rows > 0 else 0
    rows_str: list[str] = []
    for r in range(rows):
        row = [symbols[board[r][c]] for c in range(cols)]
        rows_str.append(f"Row {r:02d}: " + "  ".join(row))
    return "\n".join(rows_str)

def get_llm_move(board_state, annotated_moves_str, raw_moves_list, ai_provider, model_name, temperature, last_move, callback):
    """
    Runs an API call in a background thread and calls callback(r, c) when done.
    If the AI fails to produce a valid move, it falls back to a random legal move to prevent game breakage.
    """
    def worker():
        rows = len(board_state)
        cols = len(board_state[0]) if rows > 0 else 0
        prompt = f"""You are the "Grandmaster Architect" playing a specialized {rows}x{cols} version of Tic-Tac-Toe.
You are playing as 'D' (Dog). The human player is 'C' (Cat). Empty spaces are '.'.

Winning Conditions:
- Horizontal: 3 or 4 in a row (a full row).
- Vertical: 4 or 5 in a column.
- Diagonal: 3 or 4 in a row diagonally.
(Check the board size to determine exact winning lengths).

The board has {rows} rows (0-{rows-1}) and {cols} columns (0-{cols-1}).
Current Board State:
{format_board(board_state)}

{"[URGENT CONTEXT] The human opponent's LAST MOVE was played at Row " + str(last_move[0]) + ", Column " + str(last_move[1]) + ". Pay special attention to this area as they are likely building a threat!" if last_move else ""}

Top Recommended Legal Moves (Row, Column) and their Mathematical Evaluations:
{annotated_moves_str}

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
            if ai_provider == "Ollama":
                # Connect to your local Ryzen AI 9
                url = "http://localhost:11434/api/chat"
                data = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"temperature": float(temperature)}
                }
                response = requests.post(url, json=data)
                response.raise_for_status()
                result_text = response.json()["message"]["content"]
                
            elif ai_provider == "Google Gemini":
                api_key = os.environ.get("GOOGLE_API_KEY")
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY not found in environment.")
                
                # Using REST API to avoid version-specific python library dependencies
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                headers = {"Content-Type": "application/json"}
                data = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": float(temperature)}
                }
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                result_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            
            else:
                raise ValueError(f"Unknown AI Provider: {ai_provider}")

            # Parse the response for "MOVE: r, c"
            match = re.search(r"MOVE:\s*(\d+),\s*(\d+)", result_text, re.IGNORECASE)
            if match:
                r, c = int(match.group(1)), int(match.group(2))
                if (r, c) in raw_moves_list:
                    callback(r, c)
                    return
            
            print(f"AI returned invalid format or illegal move: {result_text}")
            # Fallback if AI hallucinates formatting or makes illegal move
            if raw_moves_list:
                fallback_move = random.choice(raw_moves_list)
                callback(fallback_move[0], fallback_move[1])
            else:
                callback(None, None)

        except Exception as e:
            print(f"AI Bridge Thread Error: {e}")
            if raw_moves_list:
                fallback_move = random.choice(raw_moves_list)
                callback(fallback_move[0], fallback_move[1])
            else:
                callback(None, None)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
