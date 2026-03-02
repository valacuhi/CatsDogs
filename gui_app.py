import tkinter as tk
from tkinter import messagebox, ttk
from game_logic import GameState
from game_controller import GameController
from agents.human_agent import HumanAgent
from agents.minimax_agent import MinimaxAgent
from agents.mcts_agent import MCTSAgent
from agents.llm_agent import LLMAgent
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
        self.next_starter = 1
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
        self.p1_mm_depth = tk.StringVar(value="4")
        self.p1_mcts_sims = tk.StringVar(value="1000")
        self.p1_temperature = tk.DoubleVar(value=0.1)
        self.p1_prompt_prefix = tk.StringVar(value="")
        
        self.p2_type = tk.StringVar(value="AI")
        self.p2_provider = tk.StringVar(value="Local Ollama")
        self.p2_model_choice = tk.StringVar(value="Local DeepSeek")
        self.p2_centaur = tk.BooleanVar(value=False)
        self.p2_fallback = tk.BooleanVar(value=False)
        self.p2_mm_depth = tk.StringVar(value="4")
        self.p2_mcts_sims = tk.StringVar(value="1000")
        self.p2_temperature = tk.DoubleVar(value=0.1)
        self.p2_prompt_prefix = tk.StringVar(value="")

        self.auto_play = tk.BooleanVar(value=False)

        # Setup tracing for auto-updating models based on provider
        self.p1_provider.trace_add("write", lambda var, index, mode: self.on_provider_change(1))
        self.p2_provider.trace_add("write", lambda var, index, mode: self.on_provider_change(2))

        # Pre-declare dynamic widgets that cause lints
        self.dummy_img: any = None
        self.next_round_btn: any = None
        self.stats_box: any = None
        self.status_label: any = None
        self.history_box: any = None
        self.move_list = []

        self.create_widgets()
        self.recreate_board_ui()

        # Assets
        try:
            self.cat_img = tk.PhotoImage(file="cat.png")
            self.dog_img = tk.PhotoImage(file="dog.png")
        except:
            self.cat_img = None
            self.dog_img = None
            
        self.controller = None
        self.setup_controller()

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
        tk.Label(sub_p1, text="Depth(Minimax):", font=("Arial", 8, "italic"), bg="white").grid(row=0, column=0, sticky="w")
        tk.OptionMenu(sub_p1, self.p1_mm_depth, "1", "2", "3", "4", "5", "6", "7").grid(row=0, column=1, sticky="ew")
        tk.Label(sub_p1, text="Sims(MCTS):", font=("Arial", 8, "italic"), bg="white").grid(row=1, column=0, sticky="w")
        tk.OptionMenu(sub_p1, self.p1_mcts_sims, "500", "1000", "2500", "5000", "10000").grid(row=1, column=1, sticky="ew")
        tk.Label(sub_p1, text="Temp:", font=("Arial", 8, "italic"), bg="white").grid(row=2, column=0, sticky="w")
        tk.Scale(sub_p1, variable=self.p1_temperature, from_=0.0, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, bg="white").grid(row=2, column=1, sticky="ew")
        tk.Label(sub_p1, text="Strategy Prefix:", font=("Arial", 8, "italic"), bg="white").grid(row=3, column=0, sticky="w")
        tk.Entry(sub_p1, textvariable=self.p1_prompt_prefix, font=("Consolas", 8)).grid(row=3, column=1, sticky="ew")

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
        tk.Label(sub_p2, text="Depth(Minimax):", font=("Arial", 8, "italic"), bg="white").grid(row=0, column=0, sticky="w")
        tk.OptionMenu(sub_p2, self.p2_mm_depth, "1", "2", "3", "4", "5", "6", "7").grid(row=0, column=1, sticky="ew")
        tk.Label(sub_p2, text="Sims(MCTS):", font=("Arial", 8, "italic"), bg="white").grid(row=1, column=0, sticky="w")
        tk.OptionMenu(sub_p2, self.p2_mcts_sims, "500", "1000", "2500", "5000", "10000").grid(row=1, column=1, sticky="ew")
        tk.Label(sub_p2, text="Temp:", font=("Arial", 8, "italic"), bg="white").grid(row=2, column=0, sticky="w")
        tk.Scale(sub_p2, variable=self.p2_temperature, from_=0.0, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, bg="white").grid(row=2, column=1, sticky="ew")
        tk.Label(sub_p2, text="Strategy Prefix:", font=("Arial", 8, "italic"), bg="white").grid(row=3, column=0, sticky="w")
        tk.Entry(sub_p2, textvariable=self.p2_prompt_prefix, font=("Consolas", 8)).grid(row=3, column=1, sticky="ew")

        # Next Round Button in Left Panel
        tk.Checkbutton(left_panel, text="Auto-Play Next Round", variable=self.auto_play, bg="white", font=("Arial", 9, "bold")).pack(side=tk.BOTTOM, pady=(0, 5))
        self.next_round_btn = tk.Button(left_panel, text="Next Round", command=self.next_round, state=tk.DISABLED, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"))
        self.next_round_btn.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        # ANALYTICS in Right Panel
        tk.Label(right_panel, text="LIVE STATS", font=("Arial", 10, "bold"), bg="white").pack(pady=(30, 0))
        self.stats_box = tk.Text(right_panel, height=5, width=35, font=("Consolas", 9), bg="#f8f8f8")
        self.stats_box.pack(pady=5)
        self.status_label = tk.Label(right_panel, text="Ready", font=("Arial", 10, "italic"), bg="white", fg="green")
        self.status_label.pack(pady=5)

        tk.Checkbutton(right_panel, text="Sound ON", variable=self.sound_active, bg="white").pack(pady=5)
        
        tk.Label(right_panel, text="MOVE HISTORY", font=("Arial", 10, "bold"), bg="white").pack(pady=(15, 0))
        hist_frame = tk.Frame(right_panel, bg="white")
        hist_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.history_box = tk.Text(hist_frame, height=12, width=35, font=("Consolas", 9), bg="#f8f8f8")
        self.history_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        hist_scroll = tk.Scrollbar(hist_frame, command=self.history_box.yview)
        hist_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_box.config(yscrollcommand=hist_scroll.set)
        
        self.move_list = []

        self.board_container = tk.Frame(self, bg="#f0f0f0")
        self.board_container.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=20)
        self.board_frame = None

    def update_stats(self, latency=0, confidence="N/A", provider="Local Ollama", depth=4, sims=1000, temp=0.1):
        self.stats_box.delete("1.0", tk.END)
        self.stats_box.insert(tk.END, f"Move Latency: {latency:.2f}s\n")
        self.stats_box.insert(tk.END, f"AI Logic: {confidence}\n")
        
        if provider == "Human":
            hardware = "Human Interaction"
        elif provider in ["Local Ollama", "Minimax", "Monte Carlo"]:
            hardware = self.hardware_choice.get()
        else:
            hardware = f"Cloud ({provider})"
            
        self.stats_box.insert(tk.END, f"Hardware: {hardware}\n")
        
        if provider == "Minimax":
            self.stats_box.insert(tk.END, f"Setting: Depth {depth}\n")
        elif provider == "Monte Carlo":
            self.stats_box.insert(tk.END, f"Setting: Sims {sims}\n")
        elif provider == "Human":
            self.stats_box.insert(tk.END, f"Setting: N/A\n")
        else:
            self.stats_box.insert(tk.END, f"Setting: Temp {temp}\n")

    def recreate_board_ui(self):
        if self.board_frame: self.board_frame.destroy()
        self.board_frame = tk.Frame(self.board_container, bg="#000")
        self.board_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.dummy_img = tk.PhotoImage(width=1, height=1)
        self.buttons = []
        
        # Column labels (1, 2, 3...)
        for c in range(self.game.cols):
            lbl = tk.Label(self.board_frame, text=str(c+1), bg="#f0f0f0", font=("Arial", 10, "bold"))
            lbl.grid(row=0, column=c+1, pady=(0, 2), sticky="nsew")
            
        for r in range(self.game.rows):
            # Row labels (A, B, C...)
            lbl = tk.Label(self.board_frame, text=chr(65+r), bg="#f0f0f0", font=("Arial", 10, "bold"), width=3)
            lbl.grid(row=r+1, column=0, padx=(0, 2), sticky="nsew")
            
            row_btns = []
            for c in range(self.game.cols):
                btn = tk.Button(self.board_frame, image=self.dummy_img, compound="center", width=60, height=60, bg="white", command=lambda r=r, c=c: self.on_click(r, c))
                btn.grid(row=r+1, column=c+1, padx=1, pady=1)
                row_btns.append(btn)
            self.buttons.append(row_btns)

    def get_agent(self, player_num):
        p_type = self.p1_type.get() if player_num == 1 else self.p2_type.get()
        if p_type == "Human":
            return HumanAgent()
            
        prov = self.p1_provider.get() if player_num == 1 else self.p2_provider.get()
        model = self.p1_model_choice.get() if player_num == 1 else self.p2_model_choice.get()
        mm_depth = int(self.p1_mm_depth.get() if player_num == 1 else self.p2_mm_depth.get())
        mcts_sims = int(self.p1_mcts_sims.get() if player_num == 1 else self.p2_mcts_sims.get())
        temp = self.p1_temperature.get() if player_num == 1 else self.p2_temperature.get()
        prefix = self.p1_prompt_prefix.get() if player_num == 1 else self.p2_prompt_prefix.get()
        fallback = self.p1_fallback.get() if player_num == 1 else self.p2_fallback.get()

        if prov == "Minimax":
            return MinimaxAgent(depth=mm_depth)
        elif prov == "Monte Carlo":
            return MCTSAgent(simulations=mcts_sims)
        else:
            mod = self.ai_models.get(model, model)
            return LLMAgent(provider=prov, model_name=mod, temperature=temp, prompt_prefix=prefix, fallback_enabled=fallback)

    def setup_controller(self):
        if self.controller:
            self.controller.stop()
            
        self.controller = GameController(
            self.game, 
            lambda: self.get_agent(1), 
            lambda: self.get_agent(2)
        )
        
        self.controller.on_board_update = self.on_board_update
        self.controller.on_game_over = self.on_game_over
        self.controller.on_error = self.on_error
        self.controller.on_ai_thinking = self.on_ai_thinking_cb
        
        # Start game
        self.controller.process_turn()

    def on_click(self, r, c):
        if self.ai_thinking or self.game.board[r][c] != 0: return
        self.update_stats(latency=0, confidence="Manual Input", provider="Human")
        self.controller.process_turn((r, c))

    def update_history_display(self):
        self.history_box.delete("1.0", tk.END)
        text = ""
        move_num = 1
        i = 0
        while i < len(self.move_list):
            p1, m1 = self.move_list[i]
            if p1 == 1:
                col1 = f"C: {m1:<3}"
                if i + 1 < len(self.move_list):
                    p2, m2 = self.move_list[i+1]
                    if p2 == 2:
                        col2 = f"D: {m2:<3}"
                        text += f"{move_num:2d}. {col1} | {col2}\n"
                        i += 2
                        move_num += 1
                        continue
                text += f"{move_num:2d}. {col1}\n"
                i += 1
                move_num += 1
            else:
                col2 = f"D: {m1:<3}"
                text += f"{move_num:2d}.          | {col2}\n"
                i += 1
                move_num += 1
                
        self.history_box.insert(tk.END, text)
        self.history_box.see(tk.END)

    def on_board_update(self, r, c, p):
        self.after(0, lambda: self._gui_board_update(r, c, p))
        
    def _gui_board_update(self, r, c, p):
        if self.cat_img and p == 1:
            self.buttons[r][c].config(image=self.cat_img, width=60, height=60)
        elif self.dog_img and p == 2:
            self.buttons[r][c].config(image=self.dog_img, width=60, height=60)
        else:
            self.buttons[r][c].config(image=self.dummy_img, text="C" if p == 1 else "D", font=("Arial", 12, "bold"))
            
        snd_k = "cat_turn" if p == 1 else "dog_turn"
        if self.sound_active.get() and snd_k in self.sounds:
            random.choice(self.sounds[snd_k]).play()
            
        move_str = f"{chr(65+r)}{c+1}"
        self.move_list.append((p, move_str))
        self.update_history_display()

    def on_game_over(self, winner, coords):
        self.after(0, lambda: self._gui_game_over(winner, coords))
        
    def _gui_game_over(self, winner, coords):
        if winner != 0:
            for r, c in coords: self.buttons[r][c].config(bg="#ff4d4d")
            if winner == 1: 
                self.cat_wins += 1
                self.next_starter = 2
            else: 
                self.dog_wins += 1
                self.next_starter = 1
            self.update_score()
            self.end_round()
        elif self.game.is_draw():
            self.end_round()

    def on_error(self, err_msg):
        self.after(0, lambda: self.status_label.config(text=err_msg, fg="red"))
        
    def on_ai_thinking_cb(self, is_thinking, status_text):
        self.ai_thinking = is_thinking
        color = "purple" if is_thinking else "green"
        self.after(0, lambda: self.status_label.config(text=status_text, fg=color))

    def update_score(self):
        self.score_label.config(text=f"Cats: {self.cat_wins} | Dogs: {self.dog_wins}")

    def end_round(self):
        self.next_round_btn.config(state=tk.NORMAL)
        if self.cat_wins >= self.target_wins or self.dog_wins >= self.target_wins:
            winner = "Cats" if self.cat_wins >= self.target_wins else "Dogs"
            messagebox.showinfo("Tournament Over", f"{winner} are the champions!")
        elif self.auto_play.get():
            self.after(1000, lambda: self.next_round())

    def next_round(self):
        if self.cat_wins >= self.target_wins or self.dog_wins >= self.target_wins:
            self.cat_wins, self.dog_wins = 0, 0
            self.next_starter = 1
            self.update_score()
        self.game.reset(starting_player=self.next_starter)
        self.move_list = []
        self.update_history_display()
        self.recreate_board_ui()
        self.next_round_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Ready")
        self.setup_controller()

if __name__ == "__main__":
    app = CatsDogsApp()
    app.mainloop()
