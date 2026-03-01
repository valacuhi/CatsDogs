import tkinter as tk
from tkinter import messagebox, ttk
from game_logic import GameState
from ai_bridge import get_llm_move
import pygame
import os
import glob
import random
import time
import threading

try:
    from PIL import Image, ImageTk
except ImportError:
    pass

class CatsDogsApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("AI Evolution Workbench: 15x3 / 12x4")
        self.geometry("1150x950")
        self.config(bg="#f0f0f0")
        
        # --- ROBUST AUDIO INITIALIZATION ---
        self.sound_active = tk.BooleanVar(value=False)
        self.sounds = {}
        try:
            pygame.mixer.init()
            self.sound_active.set(True)
            # Only try to load sounds if mixer actually initialized
            for s in ["cat_turn", "dog_turn", "cat_win_round", "dog_win_round", "cat_win_tournament", "dog_win_tournament"]:
                files = glob.glob(os.path.join("Audio", f"{s}*.mp3"))
                if files:
                    self.sounds[s] = [pygame.mixer.Sound(f) for f in files]
        except (ImportError, NotImplementedError, pygame.error):
            print("Audio mixer not available. Proceeding in silent mode.")
            self.sound_active.set(False)

        # Core State
        self.board_size_var = tk.StringVar(value="15x3")
        self.hardware_choice = tk.StringVar(value="Ryzen AI 9")
        self.game = GameState(rows=15, cols=3, win_v=4, win_h=3, win_d=3)
        self.cat_wins, self.dog_wins = 0, 0
        self.target_wins = 5
        self.ai_thinking = False
        self.ai_move_counter = 0

        # Mapping for Models
        self.ai_models = {
            "Local Qwen": "qwen2.5-coder:7b",
            "Local DeepSeek": "deepseek-r1:8b",
            "Gemini 2.5 Pro": "gemini-2.5-pro",
            "Gemini 2.0 Flash": "gemini-2.0-flash"
        }

        # P1 & P2 Vars
        self.p1_type = tk.StringVar(value="Human")
        self.p1_provider = tk.StringVar(value="Local Ollama")
        self.p1_model_choice = tk.StringVar(value="Local Qwen")
        self.p1_centaur = tk.BooleanVar(value=False)
        self.p1_fallback = tk.BooleanVar(value=False)
        self.p1_local_algo = tk.StringVar(value="Minimax")
        self.p1_mm_depth = tk.StringVar(value="4")
        self.p1_mcts_sims = tk.StringVar(value="1000")
        self.p1_temperature = tk.DoubleVar(value=0.1)
        
        self.p2_type = tk.StringVar(value="AI")
        self.p2_provider = tk.StringVar(value="Local Ollama")
        self.p2_model_choice = tk.StringVar(value="Local DeepSeek")
        self.p2_centaur = tk.BooleanVar(value=False)
        self.p2_fallback = tk.BooleanVar(value=False)
        self.p2_local_algo = tk.StringVar(value="Minimax")
        self.p2_mm_depth = tk.StringVar(value="4")
        self.p2_mcts_sims = tk.StringVar(value="1000")
        self.p2_temperature = tk.DoubleVar(value=0.1)

        # Setup tracing for auto-updating models based on provider
        self.p1_provider.trace_add("write", lambda var, index, mode: self.on_provider_change(1))
        self.p2_provider.trace_add("write", lambda var, index, mode: self.on_provider_change(2))

        # Pre-declare dynamic widgets that cause lints
        self.dummy_img: any = None
        self.next_round_btn: any = None

        self.create_widgets()
        self.recreate_board_ui()

        # Assets
        try:
            self.cat_img = tk.PhotoImage(file="cat.png")
            self.dog_img = tk.PhotoImage(file="dog.png")
        except:
            self.cat_img = None
            self.dog_img = None

    def on_provider_change(self, player):
        """Updates the default model string when the provider changes."""
        provider = self.p1_provider.get() if player == 1 else self.p2_provider.get()
        model_var = self.p1_model_choice if player == 1 else self.p2_model_choice

        if provider == "Local Ollama":
            model_var.set("Local Qwen" if player == 1 else "Local DeepSeek")
        elif provider == "Google Gemini":
            model_var.set("Gemini 2.5 Pro") # Default Gemini model
        elif provider == "OpenRouter":
            model_var.set("deepseek/deepseek-r1")
        elif provider == "Minimax":
            model_var.set("Optimal (Depth 4)")
        elif provider == "Monte Carlo":
            model_var.set("MCTS")

    def on_size_change(self):
        """Restores the 12x4 board logic from the backup."""
        if self.board_size_var.get() == "15x3":
            self.game = GameState(rows=15, cols=3, win_v=4, win_h=3, win_d=3)
        else:
            # 12x4 variant usually needs harder win conditions
            self.game = GameState(rows=12, cols=4, win_v=5, win_h=4, win_d=4)
        self.recreate_board_ui()

    def create_widgets(self):
        top_frame = tk.Frame(self, bg="#333", height=60)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        self.score_label = tk.Label(top_frame, text="Cats: 0 | Dogs: 0", fg="white", bg="#333", font=("Arial", 18, "bold"))
        self.score_label.pack(pady=10)

        left_panel = tk.Frame(self, width=320, bg="#ffffff", padx=15, pady=15, bd=1, relief=tk.SOLID)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        
        right_panel = tk.Frame(self, width=280, bg="#ffffff", padx=15, pady=15, bd=1, relief=tk.SOLID)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)

        # Game Variant Selector
        variant_f = tk.Frame(left_panel, bg="white")
        variant_f.pack(fill=tk.X, pady=(0, 10))
        tk.Label(variant_f, text="Variant:", font=("Arial", 10, "bold"), bg="white").pack(side=tk.LEFT)
        tk.Radiobutton(variant_f, text="15x3", variable=self.board_size_var, value="15x3", bg="white", command=self.on_size_change).pack(side=tk.LEFT)
        tk.Radiobutton(variant_f, text="12x4", variable=self.board_size_var, value="12x4", bg="white", command=self.on_size_change).pack(side=tk.LEFT)

        # Hardware Selector
        hw_f = tk.Frame(left_panel, bg="white")
        hw_f.pack(fill=tk.X, pady=(0, 10))
        tk.Label(hw_f, text="Host HW:", font=("Arial", 10, "bold"), bg="white").pack(side=tk.LEFT)
        tk.Radiobutton(hw_f, text="Ryzen AI 9", variable=self.hardware_choice, value="Ryzen AI 9", bg="white").pack(side=tk.LEFT)
        tk.Radiobutton(hw_f, text="Intel i7", variable=self.hardware_choice, value="Intel i7-7700HQ", bg="white").pack(side=tk.LEFT)

        # TEAM P1
        tk.Label(left_panel, text="TEAM CAT (P1)", font=("Arial", 12, "bold"), bg="#FFD54F").pack(fill=tk.X, pady=5)
        tk.Radiobutton(left_panel, text="Human", variable=self.p1_type, value="Human", bg="white").pack(anchor="w")
        tk.Radiobutton(left_panel, text="AI", variable=self.p1_type, value="AI", bg="white").pack(anchor="w")
        
        p1_f = tk.LabelFrame(left_panel, text="AI Config (P1)", bg="white")
        p1_f.pack(fill=tk.X, pady=5)
        tk.OptionMenu(p1_f, self.p1_provider, "Local Ollama", "Google Gemini", "OpenRouter", "Minimax", "Monte Carlo").pack(fill=tk.X)
        tk.Entry(p1_f, textvariable=self.p1_model_choice, font=("Consolas", 9)).pack(fill=tk.X, pady=2)
        tk.Checkbutton(p1_f, text="Use Centaur Mode", variable=self.p1_centaur, bg="white").pack(anchor="w")
        tk.Checkbutton(p1_f, text="Fallback on Error", variable=self.p1_fallback, bg="white").pack(anchor="w")
        
        sub_p1 = tk.Frame(p1_f, bg="white")
        sub_p1.pack(fill=tk.X, pady=2)
        tk.Label(sub_p1, text="Algo:", font=("Arial", 8, "italic"), bg="white").grid(row=0, column=0, sticky="w")
        tk.OptionMenu(sub_p1, self.p1_local_algo, "Minimax", "Monte Carlo").grid(row=0, column=1, sticky="ew")
        tk.Label(sub_p1, text="Depth:", font=("Arial", 8, "italic"), bg="white").grid(row=1, column=0, sticky="w")
        tk.OptionMenu(sub_p1, self.p1_mm_depth, "1", "2", "3", "4", "5", "6", "7").grid(row=1, column=1, sticky="ew")
        tk.Label(sub_p1, text="Sims:", font=("Arial", 8, "italic"), bg="white").grid(row=2, column=0, sticky="w")
        tk.OptionMenu(sub_p1, self.p1_mcts_sims, "500", "1000", "2500", "5000", "10000").grid(row=2, column=1, sticky="ew")
        tk.Label(sub_p1, text="Temp:", font=("Arial", 8, "italic"), bg="white").grid(row=3, column=0, sticky="w")
        tk.Scale(sub_p1, variable=self.p1_temperature, from_=0.0, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, bg="white").grid(row=3, column=1, sticky="ew")

        # TEAM P2
        tk.Label(left_panel, text="TEAM DOG (P2)", font=("Arial", 12, "bold"), bg="#64B5F6", fg="white").pack(fill=tk.X, pady=(20, 5))
        tk.Radiobutton(left_panel, text="Human", variable=self.p2_type, value="Human", bg="white").pack(anchor="w")
        tk.Radiobutton(left_panel, text="AI", variable=self.p2_type, value="AI", bg="white").pack(anchor="w")
        
        p2_f = tk.LabelFrame(left_panel, text="AI Config (P2)", bg="white")
        p2_f.pack(fill=tk.X, pady=5)
        tk.OptionMenu(p2_f, self.p2_provider, "Local Ollama", "Google Gemini", "OpenRouter", "Minimax", "Monte Carlo").pack(fill=tk.X)
        tk.Entry(p2_f, textvariable=self.p2_model_choice, font=("Consolas", 9)).pack(fill=tk.X, pady=2)
        tk.Checkbutton(p2_f, text="Use Centaur Mode", variable=self.p2_centaur, bg="white").pack(anchor="w")
        tk.Checkbutton(p2_f, text="Fallback on Error", variable=self.p2_fallback, bg="white").pack(anchor="w")

        sub_p2 = tk.Frame(p2_f, bg="white")
        sub_p2.pack(fill=tk.X, pady=2)
        tk.Label(sub_p2, text="Algo:", font=("Arial", 8, "italic"), bg="white").grid(row=0, column=0, sticky="w")
        tk.OptionMenu(sub_p2, self.p2_local_algo, "Minimax", "Monte Carlo").grid(row=0, column=1, sticky="ew")
        tk.Label(sub_p2, text="Depth:", font=("Arial", 8, "italic"), bg="white").grid(row=1, column=0, sticky="w")
        tk.OptionMenu(sub_p2, self.p2_mm_depth, "1", "2", "3", "4", "5", "6", "7").grid(row=1, column=1, sticky="ew")
        tk.Label(sub_p2, text="Sims:", font=("Arial", 8, "italic"), bg="white").grid(row=2, column=0, sticky="w")
        tk.OptionMenu(sub_p2, self.p2_mcts_sims, "500", "1000", "2500", "5000", "10000").grid(row=2, column=1, sticky="ew")
        tk.Label(sub_p2, text="Temp:", font=("Arial", 8, "italic"), bg="white").grid(row=3, column=0, sticky="w")
        tk.Scale(sub_p2, variable=self.p2_temperature, from_=0.0, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, bg="white").grid(row=3, column=1, sticky="ew")

        # Next Round Button in Left Panel
        self.next_round_btn = tk.Button(left_panel, text="Next Round", command=self.next_round, state=tk.DISABLED, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"))
        self.next_round_btn.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        # ANALYTICS in Right Panel
        tk.Label(right_panel, text="LIVE STATS", font=("Arial", 10, "bold"), bg="white").pack(pady=(30, 0))
        self.stats_box = tk.Text(right_panel, height=5, width=35, font=("Consolas", 9), bg="#f8f8f8")
        self.stats_box.pack(pady=5)
        self.status_label = tk.Label(right_panel, text="Ready", font=("Arial", 10, "italic"), bg="white", fg="green")
        self.status_label.pack(pady=5)

        tk.Checkbutton(right_panel, text="Sound ON", variable=self.sound_active, bg="white").pack(pady=5)

        self.board_container = tk.Frame(self, bg="#f0f0f0")
        self.board_container.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=20)
        self.board_frame = None

    def update_stats(self, latency=0, confidence="N/A", provider="Local Ollama"):
        self.stats_box.delete("1.0", tk.END)
        self.stats_box.insert(tk.END, f"Move Latency: {latency:.2f}s\n")
        self.stats_box.insert(tk.END, f"AI Logic: {confidence}\n")
        
        if provider in ["Local Ollama", "Minimax", "Monte Carlo"]:
            hardware = self.hardware_choice.get()
        else:
            hardware = f"Cloud ({provider})"
            
        self.stats_box.insert(tk.END, f"Hardware: {hardware}\n")

    def recreate_board_ui(self):
        if self.board_frame: self.board_frame.destroy()
        self.board_frame = tk.Frame(self.board_container, bg="#000")
        self.board_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.dummy_img = tk.PhotoImage(width=1, height=1)
        self.buttons = []
        for r in range(self.game.rows):
            row_btns = []
            for c in range(self.game.cols):
                btn = tk.Button(self.board_frame, image=self.dummy_img, compound="center", width=60, height=60, bg="white", command=lambda r=r, c=c: self.on_click(r, c))
                btn.grid(row=r, column=c, padx=1, pady=1)
                row_btns.append(btn)
            self.buttons.append(row_btns)

    def on_click(self, r, c):
        if self.ai_thinking or self.game.board[r][c] != 0: return
        p_type = self.p1_type.get() if self.game.current_turn == 1 else self.p2_type.get()
        if p_type == "Human": self.apply_move(r, c)

    def apply_move(self, r, c):
        p = self.game.current_turn
        if self.game.make_move(r, c, p):
            if self.cat_img and p == 1:
                self.buttons[r][c].config(image=self.cat_img, width=60, height=60)
            elif self.dog_img and p == 2:
                self.buttons[r][c].config(image=self.dog_img, width=60, height=60)
            else:
                self.buttons[r][c].config(image=self.dummy_img, text="C" if p == 1 else "D", font=("Arial", 12, "bold"))
            
            # Sound safety check
            snd_k = "cat_turn" if p == 1 else "dog_turn"
            if self.sound_active.get() and snd_k in self.sounds:
                random.choice(self.sounds[snd_k]).play()

            if not self.check_game_over():
                self.game.current_turn = 3 - p
                n_type = self.p1_type.get() if self.game.current_turn == 1 else self.p2_type.get()
                if n_type == "AI": self.after(500, self.trigger_ai_move)

    def trigger_ai_move(self):
        if self.game.check_win()[0] != 0 or self.game.is_draw(): return
        self.ai_thinking, self.start_time = True, time.time()
        self.ai_move_counter += 1
        curr_c = self.ai_move_counter
        
        p = self.game.current_turn
        # Determine which team variables to use
        if p == 1:
            prov, choice, cent, fallback, local_algo = self.p1_provider.get(), self.p1_model_choice.get(), False, self.p1_fallback.get(), self.p1_local_algo.get()
            mm_depth = int(self.p1_mm_depth.get())
            mcts_sims = int(self.p1_mcts_sims.get())
            temp = self.p1_temperature.get()
        else:
            prov, choice, cent, fallback, local_algo = self.p2_provider.get(), self.p2_model_choice.get(), False, self.p2_fallback.get(), self.p2_local_algo.get()
            mm_depth = int(self.p2_mm_depth.get())
            mcts_sims = int(self.p2_mcts_sims.get())
            temp = self.p2_temperature.get()

        # Map friendly name to model string
        mod = self.ai_models.get(choice, choice)
        self.status_label.config(text=f"AI Thinking ({choice})...", fg="purple")

        # 1. MCTS Logic (Restored from backup)
        if prov == "Monte Carlo":
            def mcts_worker():
                m = self.game.get_best_move_mcts(p, simulations=mcts_sims)
                self.after(0, lambda: self.apply_ai_move(m, "MCTS", curr_c, prov))
            threading.Thread(target=mcts_worker, daemon=True).start()
            return

        # 2. Minimax Logic
        if prov == "Minimax":
            m = self.game.get_best_move(p, depth=mm_depth)
            self.after(500, lambda: self.apply_ai_move(m, "Optimal", curr_c, prov))
            return

        # 3. LLM Logic (Existing)
        evals = self.game.get_evaluated_moves(p, depth=2)
        if not evals: return
        safe = [m for m, s in evals if s > -50] or [m for m, s in evals]
        m_str = "\n".join([f"({r}, {c}) [{'Adv' if s>0 else 'Safe'}]" for (r,c), s in evals if (r,c) in safe][:7])
        
        def handle_llm_callback(r, c, is_fallback):
            if is_fallback:
                # Dispatch to local algorithm
                if local_algo == "Monte Carlo":
                    def mcts_fallback_worker():
                        fm = self.game.get_best_move_mcts(p, simulations=mcts_sims)
                        self.after(0, lambda: self.apply_ai_move(fm, "MCTS (Fallback)", curr_c, prov))
                    threading.Thread(target=mcts_fallback_worker, daemon=True).start()
                else: # Minimax
                    fm = self.game.get_best_move(p, depth=mm_depth)
                    self.after(500, lambda: self.apply_ai_move(fm, "Optimal (Fallback)", curr_c, prov))
            else:
                self.after(0, lambda: self.apply_ai_move((r, c) if r is not None else None, "LLM", curr_c, prov))

        get_llm_move(self.game.board, m_str, safe, prov, mod, temp, self.game.last_move, fallback, handle_llm_callback)

    def apply_ai_move(self, move, conf, counter, provider="Local Ollama"):
        if counter != self.ai_move_counter: return
        self.update_stats(time.time() - self.start_time, conf, provider)
        
        if move is None:
            self.status_label.config(text="API Error / Invalid Move", fg="red")
            self.ai_thinking = False
            return

        self.ai_thinking = False
        if move: self.apply_move(move[0], move[1])

    def check_game_over(self):
        winner, coords = self.game.check_win()
        if winner != 0:
            for r, c in coords: self.buttons[r][c].config(bg="#ff4d4d")
            if winner == 1: self.cat_wins += 1
            else: self.dog_wins += 1
            self.update_score()
            self.end_round()
            return True
        if self.game.is_draw():
            self.end_round()
            return True
        return False

    def update_score(self):
        self.score_label.config(text=f"Cats: {self.cat_wins} | Dogs: {self.dog_wins}")

    def end_round(self):
        self.ai_thinking = True
        self.next_round_btn.config(state=tk.NORMAL)
        if self.cat_wins >= self.target_wins or self.dog_wins >= self.target_wins:
            winner = "Cats" if self.cat_wins >= self.target_wins else "Dogs"
            messagebox.showinfo("Tournament Over", f"{winner} are the champions!")

    def next_round(self):
        if self.cat_wins >= self.target_wins or self.dog_wins >= self.target_wins:
            self.cat_wins, self.dog_wins = 0, 0
            self.update_score()
        self.game.reset()
        self.recreate_board_ui()
        self.next_round_btn.config(state=tk.DISABLED)
        self.ai_thinking = False
        n_type = self.p1_type.get() if self.game.current_turn == 1 else self.p2_type.get()
        if n_type == "AI": self.after(500, self.trigger_ai_move)

if __name__ == "__main__":
    app = CatsDogsApp()
    app.mainloop()
