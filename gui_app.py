import tkinter as tk
from tkinter import messagebox
from game_logic import GameState
from ai_bridge import get_llm_move
import pygame
import os
import glob
import random
try:
    from PIL import Image, ImageTk
except ImportError:
    pass

class CatsDogsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Feline vs. Canine 15x3")
        self.geometry("600x950")
        
        # Make the main window look nicer
        self.config(bg="#e8e8e8")
        
        # Initialize Audio
        pygame.mixer.init()
        self.sounds = {}
        for s in ["cat_turn", "dog_turn", "cat_win_round", "dog_win_round", "cat_win_tournament", "dog_win_tournament"]:
            files = glob.glob(os.path.join("Audio", f"{s}*.mp3"))
            if files:
                self.sounds[s] = [pygame.mixer.Sound(f) for f in files]
        
        # dynamic sizes
        self.board_size_var = tk.StringVar(value="15x3")
        self.rows = 15
        self.cols = 3
        
        self.game = GameState(rows=15, cols=3, win_v=4, win_h=3, win_d=3)
        self.cat_wins = 0
        self.dog_wins = 0
        self.target_wins = 5
        self.buttons = []
        self.ai_thinking = False
        self.cat_img = tk.PhotoImage(file="cat.png")
        self.dog_img = tk.PhotoImage(file="dog.png")
        
        self.human_team = tk.IntVar(value=1)
        self.sound_enabled = tk.BooleanVar(value=True)
        self.starting_team = 1
        self.ai_move_counter = 0
        
        # Declare UI attributes to satisfy static type checkers / linters
        self.score_label: tk.Label
        self.ai_var: tk.StringVar
        self.ai_models: dict
        self.temp_slider: tk.Scale
        self.minimax_depth_var: tk.IntVar
        self.depth_menu: tk.OptionMenu
        self.mcts_sim_var: tk.IntVar
        self.sim_menu: tk.OptionMenu
        self.status_label: tk.Label
        self.next_round_btn: tk.Button
        self.team_rbtn_cat: tk.Radiobutton
        self.team_rbtn_dog: tk.Radiobutton
        self.sound_chk: tk.Checkbutton
        self.size_rbtn_15x3: tk.Radiobutton
        self.size_rbtn_12x4: tk.Radiobutton
        self.interrupt_btn: tk.Button
        self.board_container: tk.Frame
        self.board_frame: tk.Frame
        
        self.create_widgets()
        self.recreate_board_ui()
        
    def create_widgets(self):
        # ---------------- TOP BAR ----------------
        top_frame = tk.Frame(self, bg="#d0d0d0")
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        self.score_label = tk.Label(top_frame, text=f"Cats: {self.cat_wins} | Dogs: {self.dog_wins}", 
                                    font=("Helvetica", 18, "bold"), bg="#d0d0d0")
        self.score_label.pack(side=tk.LEFT, padx=10)
        
        rules_btn = tk.Button(top_frame, text="Game Rules", font=("Arial", 10, "bold"), command=self.show_rules)
        rules_btn.pack(side=tk.RIGHT, padx=10)
        
        # ---------------- SIDEBAR ----------------
        sidebar = tk.Frame(self, width=220, bg="#ffffff", bd=2, relief=tk.GROOVE)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
        tk.Label(sidebar, text="Tournament Mode", font=("Arial", 14, "bold"), bg="#ffffff", fg="#333333").pack(pady=(10, 5))
        tk.Label(sidebar, text="First to 5 wins", font=("Arial", 10), bg="#ffffff", fg="#666666").pack()
        
        tk.Frame(sidebar, height=2, bg="#cccccc").pack(fill=tk.X, pady=10, padx=10)
        
        tk.Label(sidebar, text="Board Size", font=("Arial", 12, "bold"), bg="#ffffff").pack(pady=5)
        self.size_rbtn_15x3 = tk.Radiobutton(sidebar, text="15x3", variable=self.board_size_var, value="15x3", bg="#ffffff", font=("Arial", 10), command=self.on_size_change)
        self.size_rbtn_15x3.pack(anchor="w", padx=10)
        self.size_rbtn_12x4 = tk.Radiobutton(sidebar, text="12x4", variable=self.board_size_var, value="12x4", bg="#ffffff", font=("Arial", 10), command=self.on_size_change)
        self.size_rbtn_12x4.pack(anchor="w", padx=10)
        
        tk.Label(sidebar, text="Your Team", font=("Arial", 12, "bold"), bg="#ffffff").pack(pady=5)
        self.team_rbtn_cat = tk.Radiobutton(sidebar, text="Cats", variable=self.human_team, value=1, bg="#ffffff", font=("Arial", 10))
        self.team_rbtn_cat.pack(anchor="w", padx=10)
        self.team_rbtn_dog = tk.Radiobutton(sidebar, text="Dogs", variable=self.human_team, value=2, bg="#ffffff", font=("Arial", 10))
        self.team_rbtn_dog.pack(anchor="w", padx=10)
        
        tk.Frame(sidebar, height=2, bg="#cccccc").pack(fill=tk.X, pady=10, padx=10)
        
        tk.Label(sidebar, text="Opponent", font=("Arial", 12, "bold"), bg="#ffffff").pack(pady=5)
        self.ai_var = tk.StringVar(value="Minimax")
        self.ai_var.trace_add("write", self.on_ai_change)
        
        # Provide mapping for models
        self.ai_models = {
            "Minimax": "minimax",
            "Monte Carlo": "mcts",
            "Mistral 7B": "mistralai/mistral-7b-instruct:free",
            "Phi-3 Mini": "microsoft/phi-3-mini-4k-instruct:free",
            "Llama 3 8B": "meta-llama/llama-3-8b-instruct:free",
            "Claude 3.5 Sonnet": "anthropic/claude-3.5-sonnet",
            "GPT-4o Mini": "openai/gpt-4o-mini",
            "Gemini 1.5 Pro": "gemini-1.5-pro",
            "Gemini 2.0 Flash": "gemini-2.0-flash"
        }
        
        for choice in self.ai_models.keys():
            tk.Radiobutton(sidebar, text=choice, variable=self.ai_var, value=choice, bg="#ffffff", font=("Arial", 10)).pack(anchor="w", padx=10)
            
        tk.Label(sidebar, text="Minimax Depth", font=("Arial", 10, "bold"), bg="#ffffff").pack(pady=(10, 0))
        self.minimax_depth_var = tk.IntVar(value=4)
        self.depth_menu = tk.OptionMenu(sidebar, self.minimax_depth_var, 3, 4, 5, 6)
        self.depth_menu.config(bg="#ffffff", width=10)
        self.depth_menu.pack(pady=5)
        
        tk.Label(sidebar, text="MCTS Simulations", font=("Arial", 10, "bold"), bg="#ffffff").pack(pady=(10, 0))
        self.mcts_sim_var = tk.IntVar(value=1000)
        self.sim_menu = tk.OptionMenu(sidebar, self.mcts_sim_var, 500, 1000, 2500, 5000)
        self.sim_menu.config(bg="#ffffff", width=10, state=tk.DISABLED)
        self.sim_menu.pack(pady=5)
            
        tk.Label(sidebar, text="LLM Temperature (0.0-1.0)", bg="#ffffff", font=("Arial", 10, "bold")).pack(pady=(10,0))
        self.temp_slider = tk.Scale(sidebar, from_=0.0, to=1.0, resolution=0.1, orient=tk.HORIZONTAL, bg="#ffffff", highlightthickness=0)
        self.temp_slider.set(0.1)
        self.temp_slider.pack(fill=tk.X, padx=10)
        
        tk.Frame(sidebar, height=2, bg="#cccccc").pack(fill=tk.X, pady=10, padx=10)
        
        self.sound_chk = tk.Checkbutton(sidebar, text="Sound ON", variable=self.sound_enabled, bg="#ffffff", font=("Arial", 10, "bold"))
        self.sound_chk.pack(pady=5)
        
        self.status_label = tk.Label(sidebar, text="Ready", bg="#ffffff", fg="green", font=("Arial", 11, "italic"))
        self.status_label.pack(pady=10)
        
        tk.Frame(sidebar, height=2, bg="#cccccc").pack(fill=tk.X, pady=10, padx=10)

        self.next_round_btn = tk.Button(sidebar, text="Next Round", state=tk.DISABLED, command=self.next_round, 
                                        font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", activebackground="#45a049")
        self.next_round_btn.pack(pady=20, fill=tk.X, padx=20)
        
        self.interrupt_btn = tk.Button(sidebar, text="Interrupt AI", state=tk.DISABLED, command=self.on_interrupt_click,
                                       font=("Arial", 11, "bold"), bg="#f44336", fg="white", activebackground="#e53935")
        self.interrupt_btn.pack(pady=0, fill=tk.X, padx=20)
        
        # ---------------- BOARD ----------------
        self.board_container = tk.Frame(self, bg="#e8e8e8")
        self.board_container.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=20, pady=10)
        self.board_frame = None
        
    def on_ai_change(self, *args):
        if hasattr(self, 'depth_menu') and hasattr(self, 'sim_menu'):
            choice = self.ai_var.get()
            if choice == "Minimax":
                self.depth_menu.config(state=tk.NORMAL)
                self.sim_menu.config(state=tk.DISABLED)
            elif choice == "Monte Carlo":
                self.depth_menu.config(state=tk.DISABLED)
                self.sim_menu.config(state=tk.NORMAL)
            else:
                self.depth_menu.config(state=tk.DISABLED)
                self.sim_menu.config(state=tk.DISABLED)
        
    def recreate_board_ui(self):
        if self.board_frame is not None:
            self.board_frame.destroy()
            
        self.board_frame = tk.Frame(self.board_container, bg="#000000") 
        self.board_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        self.buttons = []
        for r in range(self.rows):
            row_buttons = []
            for c in range(self.cols):
                cell_frame = tk.Frame(self.board_frame, width=55, height=55)
                cell_frame.grid(row=r, column=c, padx=1, pady=1)
                cell_frame.pack_propagate(False)
                
                def make_cmd(row: int, col: int):
                    return lambda: self.on_click(row, col)

                btn = tk.Button(cell_frame, text=" ", font=("sans-serif", 14), bg="white", fg="black",
                                command=make_cmd(r, c))
                btn.pack(expand=True, fill="both")
                row_buttons.append(btn)
            self.buttons.append(row_buttons)

    def on_size_change(self):
        size = self.board_size_var.get()
        if size == "15x3":
            self.rows = 15
            self.cols = 3
            self.game = GameState(rows=15, cols=3, win_v=4, win_h=3, win_d=3)
        else:
            self.rows = 12
            self.cols = 4
            self.game = GameState(rows=12, cols=4, win_v=5, win_h=4, win_d=4)
        
        self.recreate_board_ui()

    def show_rules(self):
        msg = ("Welcome to Feline vs. Canine!\n\n"
               "The Setup: Choose 15x3 or 12x4 board.\n"
               "Cats (😇) vs Dogs (😈)\n\n"
               "Winning Conditions (15x3):\n"
               "1. Vertical: 4-in-a-row\n"
               "2. Horizontal: 3-in-a-row\n"
               "3. Diagonal: 3-in-a-row diagonally\n\n"
               "Winning Conditions (12x4):\n"
               "1. Vertical: 5-in-a-row\n"
               "2. Horizontal: 4-in-a-row\n"
               "3. Diagonal: 4-in-a-row diagonally\n\n"
               "Tournament Mode: Keep playing rounds until one faction reaches 5 wins.")
        messagebox.showinfo("Rules", msg)

    def on_click(self, r, c):
        if self.ai_thinking or self.game.check_win()[0] != 0 or self.game.is_draw():
            return
            
        if self.game.board[r][c] != 0:
            return
            
        self.team_rbtn_cat.config(state=tk.DISABLED)
        self.team_rbtn_dog.config(state=tk.DISABLED)
        self.size_rbtn_15x3.config(state=tk.DISABLED)
        self.size_rbtn_12x4.config(state=tk.DISABLED)
            
        if self.game.make_move(r, c, self.human_team.get()):
            img = self.cat_img if self.human_team.get() == 1 else self.dog_img
            snd = "cat_turn" if self.human_team.get() == 1 else "dog_turn"
            self.buttons[r][c].config(image=img, text="")
            if snd in self.sounds and self.sounds[snd] and self.sound_enabled.get():
                random.choice(self.sounds[snd]).play()
            
            if self.check_game_over():
                return
                
            self.ai_thinking = True
            self.after(1000, self.trigger_ai_move)

    def on_interrupt_click(self):
        if self.ai_thinking:
            # Interrupting the AI
            self.ai_move_counter += 1
            self.ai_thinking = False
            self.status_label.config(text="AI Interrupted!\nSelect new AI & Retry.", fg="red")
            self.interrupt_btn.config(text="Retry AI Move", bg="#FF9800", activebackground="#F57C00", state=tk.NORMAL)
        else:
            # Retrying the AI move
            self.trigger_ai_move()

    def trigger_ai_move(self):
        self.ai_thinking = True
        self.ai_move_counter += 1
        current_counter = self.ai_move_counter
        self.interrupt_btn.config(text="Interrupt AI", state=tk.NORMAL, bg="#f44336", activebackground="#e53935")
                
        ai_choice = self.ai_var.get()
        if "Minimax" in ai_choice:
            self.status_label.config(text="Minimax thinking...", fg="blue")
            self.update_idletasks()
            
            ai_team = 3 - self.human_team.get()
            depth_val = self.minimax_depth_var.get()
            best_move = self.game.get_best_move(ai_team, depth=depth_val)
            # Use after to allow UI strictly synchronous process to breathe momentarily
            self.after(50, lambda: self.apply_ai_move(best_move[0] if best_move else None, best_move[1] if best_move else None, current_counter))
        elif "Monte Carlo" in ai_choice:
            self.status_label.config(text=f"MCTS simulating\n {self.mcts_sim_var.get()} games...", fg="blue")
            self.update_idletasks()
            
            ai_team = 3 - self.human_team.get()
            simulations = self.mcts_sim_var.get()
            
            # Using a thread so UI does not completely lock up during thousands of simulations
            def mcts_worker():
                best_move = self.game.get_best_move_mcts(ai_team, simulations=simulations)
                self.after(0, lambda: self.apply_ai_move(best_move[0] if best_move else None, best_move[1] if best_move else None, current_counter))
            
            import threading
            threading.Thread(target=mcts_worker, daemon=True).start()

        else:
            self.status_label.config(text="LLM thinking...", fg="purple")
            provider = "Google Gemini" if "Gemini" in ai_choice else "OpenRouter"
            model = self.ai_models[ai_choice]
            ai_team = 3 - self.human_team.get()
            evaluated_moves = self.game.get_evaluated_moves(ai_team, depth=2)
            
            if not evaluated_moves:
                return
                
            best_score = evaluated_moves[0][1]
            
            # 1. Auto-Pilot: If there is a guaranteed win, take it immediately!
            if best_score >= 50:
                print(f"CENTAUR AUTO-PILOT: Found guaranteed win at {evaluated_moves[0][0]}, skipping LLM!")
                self.after(50, lambda: self.apply_ai_move(evaluated_moves[0][0][0], evaluated_moves[0][0][1], current_counter))
                return
                
            # 2. Filter out blunders (score <= -50)
            safe_moves = [m for m, s in evaluated_moves if s > -50]
            
            # If all moves lose anyway, just give the LLM all moves
            if not safe_moves:
                safe_moves = [m for m, s in evaluated_moves]
                
            # 3. Auto-Pilot: If there is exactly ONE safe move (forced block), take it immediately!
            if len(safe_moves) == 1:
                print(f"CENTAUR AUTO-PILOT: Found forced block at {safe_moves[0]}, skipping LLM to prevent a blunder!")
                self.after(50, lambda: self.apply_ai_move(safe_moves[0][0], safe_moves[0][1], current_counter))
                return
                
            # 4. If multiple safe/strategic moves exist, annotate them for the LLM
            annotated_moves = []
            for (r, c), score in evaluated_moves:
                if (r, c) not in safe_moves:
                    continue # Do not present blunders to the LLM
                
                if score > 0:
                    tag = " [Advantageous]"
                else:
                    tag = " [Safe]"
                annotated_moves.append(f"({r}, {c}){tag}")
                
            moves_str = "\n".join(annotated_moves[:7]) # Provide top 7 options max
            temp = self.temp_slider.get()
            
            # Simple callback, LLM is now restricted to only picking from safe_moves
            def callback(r, c):
                self.after(0, lambda: self.apply_ai_move(r, c, current_counter))
                
            get_llm_move(self.game.board, moves_str, safe_moves, provider, model, temp, self.game.last_move, callback)

    def apply_ai_move(self, r, c, counter_at_time_of_request):
        if counter_at_time_of_request != self.ai_move_counter:
            return  # Move was interrupted/cancelled
            
        self.ai_thinking = False
        self.interrupt_btn.config(text="Interrupt AI", state=tk.DISABLED, bg="#f44336", activebackground="#e53935")
        self.status_label.config(text="Your Turn", fg="green")
        if r is not None and c is not None:
            ai_team = 3 - self.human_team.get()
            if self.game.make_move(r, c, ai_team):
                img = self.cat_img if ai_team == 1 else self.dog_img
                snd = "cat_turn" if ai_team == 1 else "dog_turn"
                self.buttons[r][c].config(image=img, text="")
                if snd in self.sounds and self.sounds[snd] and self.sound_enabled.get():
                    random.choice(self.sounds[snd]).play()
        
        self.check_game_over()

    def check_game_over(self):
        winner, coords = self.game.check_win()
        if winner != 0:
            for r, c in coords:
                self.buttons[r][c].config(bg="#ff4d4d") # Highlight winning line in red
            
            if winner == 1:
                self.cat_wins += 1
                self.status_label.config(text="Cats win the round!", fg="orange")
                if "cat_win_round" in self.sounds and self.sounds["cat_win_round"] and self.sound_enabled.get():
                    random.choice(self.sounds["cat_win_round"]).play()
                self.starting_team = 2 # Loser starts next round
            else:
                self.dog_wins += 1
                self.status_label.config(text="Dogs win the round!", fg="orange")
                if "dog_win_round" in self.sounds and self.sounds["dog_win_round"] and self.sound_enabled.get():
                    random.choice(self.sounds["dog_win_round"]).play()
                self.starting_team = 1 # Loser starts next round
                
            self.update_score()
            self.end_round()
            return True
            
        if self.game.is_draw():
            self.status_label.config(text="It's a draw!", fg="orange")
            self.end_round()
            return True
            
        return False

    def end_round(self):
        self.ai_thinking = True # Lock the board logically
                
        if self.cat_wins >= self.target_wins or self.dog_wins >= self.target_wins:
            champion = "Cats" if self.cat_wins >= self.target_wins else "Dogs"
            
            # Play tournament win sound
            sound_key = "cat_win_tournament" if self.cat_wins >= self.target_wins else "dog_win_tournament"
            if sound_key in self.sounds and self.sounds[sound_key] and self.sound_enabled.get():
                random.choice(self.sounds[sound_key]).play()
                
            self.status_label.config(text=f"{champion} won the tournament!", fg="red", font=("Arial", 12, "bold"))
            messagebox.showinfo("Tournament Over", f"🎉 {champion} win the tournament! 🎉")
            
            # Show the victory image popup
            try:
                img_file = "cats_win.png" if self.cat_wins >= self.target_wins else "dogs_win.png"
                if os.path.exists(img_file):
                    win_window = tk.Toplevel(self)
                    win_window.title(f"{champion} Win!")
                    win_window.config(bg="white")
                    
                    img = Image.open(img_file)
                    img.thumbnail((600, 600), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    lbl = tk.Label(win_window, image=photo, bg="white")
                    lbl.image = photo  # keep reference
                    lbl.pack(padx=20, pady=20)
                    
                    tk.Button(win_window, text="Awesome!", font=("Arial", 14), command=win_window.destroy).pack(pady=10)
            except Exception as e:
                print(f"Could not load victory image: {e}")
                
            self.next_round_btn.config(text="New Tournament", state=tk.NORMAL, bg="#2196F3")
        else:
            self.next_round_btn.config(text="Next Round", state=tk.NORMAL, bg="#4CAF50")
            
        self.interrupt_btn.config(text="Interrupt AI", state=tk.DISABLED, bg="#f44336")

    def next_round(self):
        self.ai_thinking = False
        if self.cat_wins >= self.target_wins or self.dog_wins >= self.target_wins:
            # Complete reset for new tournament
            self.cat_wins = 0
            self.dog_wins = 0
            self.update_score()
            self.starting_team = 1 # Default back to cats
            self.team_rbtn_cat.config(state=tk.NORMAL)
            self.team_rbtn_dog.config(state=tk.NORMAL)
            self.size_rbtn_15x3.config(state=tk.NORMAL)
            self.size_rbtn_12x4.config(state=tk.NORMAL)
            
        self.game.reset()
        for r in range(self.rows):
            for c in range(self.cols):
                self.buttons[r][c].config(image="", text=" ", bg="white")
                
        self.status_label.config(text="Ready", fg="green")
        self.next_round_btn.config(text="Next Round", state=tk.DISABLED, bg="#cccccc")
        self.interrupt_btn.config(text="Interrupt AI", state=tk.DISABLED, bg="#f44336")
        
        if self.starting_team != self.human_team.get():
            self.team_rbtn_cat.config(state=tk.DISABLED)
            self.team_rbtn_dog.config(state=tk.DISABLED)
            self.size_rbtn_15x3.config(state=tk.DISABLED)
            self.size_rbtn_12x4.config(state=tk.DISABLED)
            self.ai_thinking = True
            self.after(500, self.trigger_ai_move)

    def update_score(self):
        self.score_label.config(text=f"Cats: {self.cat_wins} | Dogs: {self.dog_wins}")

if __name__ == "__main__":
    app = CatsDogsApp()
    app.mainloop()
