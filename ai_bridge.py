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
    rows_str: list[str] = []
    for r in range(15):
        row = [symbols[board[r][c]] for c in range(3)]
        rows_str.append(f"Row {r:02d}: " + "  ".join(row))
    return "\n".join(rows_str)

def get_llm_move(board_state, available_moves, ai_provider, model_name, temperature, callback):
    """
    Runs an API call in a background thread and calls callback(r, c) when done.
    If the AI fails to produce a valid move, it falls back to a random legal move to prevent game breakage.
    """
    def worker():
        prompt = f"""You are the "Grandmaster Architect" playing a specialized 15x3 version of Tic-Tac-Toe.
You are playing as 'D' (Dog). The human player is 'C' (Cat). Empty spaces are '.'.

Winning Conditions:
- Horizontal: 3 in a row (a full row).
- Vertical: 4 in a column.
- Diagonal: 3 in a row diagonally.

The board has 15 rows (0-14) and 3 columns (0-2).
Current Board State:
{format_board(board_state)}

Strict Legal Move List (Row, Column):
{available_moves}

Analyze the board. You MUST choose one of the strict legal moves to either:
1. Block the opponent (C) from winning on their next turn.
2. Complete your own winning line (D).
3. Set up a future win.

Respond ONLY with the coordinates of your chosen move in the exact format: "MOVE: r, c"
Do not include any other text, reasoning, or markdown around your response.
"""
        try:
            result_text = ""
            if ai_provider == "OpenRouter":
                api_key = os.environ.get("OPENROUTER_API_KEY")
                if not api_key:
                    raise ValueError("OPENROUTER_API_KEY not found in environment.")
                    
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": float(temperature)
                }
                response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
                response.raise_for_status()
                result_text = response.json()["choices"][0]["message"]["content"]

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
                if (r, c) in available_moves:
                    callback(r, c)
                    return
            
            print(f"AI returned invalid format or illegal move: {result_text}")
            # Fallback if AI hallucinates formatting or makes illegal move
            if available_moves:
                fallback_move = random.choice(available_moves)
                callback(fallback_move[0], fallback_move[1])
            else:
                callback(None, None)

        except Exception as e:
            print(f"AI Bridge Thread Error: {e}")
            if available_moves:
                fallback_move = random.choice(available_moves)
                callback(fallback_move[0], fallback_move[1])
            else:
                callback(None, None)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
