import tkinter as tk
from tkinter import messagebox
from game_logic import GameState
from ai_bridge import get_llm_move

class CatsDogsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Feline vs. Canine 15x3")
        self.geometry("600x850")
        
        # Make the main window look nicer
        self.config(bg="#e8e8e8")
        
        self.game = GameState()
        self.cat_wins = 0
        self.dog_wins = 0
        self.target_wins = 5
        self.buttons = []
        self.ai_thinking = False
        self.cat_img = tk.PhotoImage(file="cat.png")
        self.dog_img = tk.PhotoImage(file="dog.png")
        
        # Declare UI attributes to satisfy static type checkers / linters
        self.score_label: tk.Label
        self.ai_var: tk.StringVar
        self.ai_models: dict
        self.temp_slider: tk.Scale
        self.status_label: tk.Label
        self.next_round_btn: tk.Button
        
        self.create_widgets()
        
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
        
        tk.Label(sidebar, text="Opponent AI", font=("Arial", 12, "bold"), bg="#ffffff").pack(pady=5)
        self.ai_var = tk.StringVar(value="Local Minimax")
        
        # Provide mapping for models
        self.ai_models = {
            "Local Minimax": "minimax",
            "OpenRouter (Mistral)": "mistralai/mistral-7b-instruct:free",
            "OpenRouter (Phi-3)": "microsoft/phi-3-mini-4k-instruct:free",
            "Google Gemini": "gemini-2.0-flash"
        }
        
        for choice in self.ai_models.keys():
            tk.Radiobutton(sidebar, text=choice, variable=self.ai_var, value=choice, bg="#ffffff", font=("Arial", 10)).pack(anchor="w", padx=10)
            
        tk.Label(sidebar, text="LLM Temperature (0.0-1.0)", bg="#ffffff", font=("Arial", 10, "bold")).pack(pady=(20,0))
        self.temp_slider = tk.Scale(sidebar, from_=0.0, to=1.0, resolution=0.1, orient=tk.HORIZONTAL, bg="#ffffff", highlightthickness=0)
        self.temp_slider.set(0.1)
        self.temp_slider.pack(fill=tk.X, padx=10)
        
        self.status_label = tk.Label(sidebar, text="Ready", bg="#ffffff", fg="green", font=("Arial", 11, "italic"))
        self.status_label.pack(pady=20)
        
        tk.Frame(sidebar, height=2, bg="#cccccc").pack(fill=tk.X, pady=10, padx=10)

        self.next_round_btn = tk.Button(sidebar, text="Next Round", state=tk.DISABLED, command=self.next_round, 
                                        font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", activebackground="#45a049")
        self.next_round_btn.pack(pady=20, fill=tk.X, padx=20)
        
        # ---------------- BOARD ----------------
        board_container = tk.Frame(self, bg="#e8e8e8")
        board_container.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        # Center the board within the container
        board_frame = tk.Frame(board_container, bg="#000000") 
        board_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        for r in range(15):
            row_buttons = []
            for c in range(3):
                cell_frame = tk.Frame(board_frame, width=55, height=55)
                cell_frame.grid(row=r, column=c, padx=1, pady=1)
                cell_frame.pack_propagate(False)
                
                def make_cmd(row: int, col: int):
                    return lambda: self.on_click(row, col)

                btn = tk.Button(cell_frame, text=" ", font=("sans-serif", 14), bg="white", fg="black",
                                command=make_cmd(r, c))
                btn.pack(expand=True, fill="both")
                row_buttons.append(btn)
            self.buttons.append(row_buttons)

    def show_rules(self):
        msg = ("Welcome to Feline vs. Canine 15x3!\n\n"
               "The Setup: 15 rows by 3 columns.\n"
               "Cats (😇) vs Dogs (😈)\n\n"
               "Winning Conditions:\n"
               "1. Vertical: 4-in-a-row in a single column\n"
               "2. Horizontal: 3-in-a-row (an entire row)\n"
               "3. Diagonal: 3-in-a-row diagonally\n\n"
               "Tournament Mode: Keep playing rounds until one faction reaches 5 wins.")
        messagebox.showinfo("Rules", msg)

    def on_click(self, r, c):
        if self.ai_thinking or self.game.check_win()[0] != 0 or self.game.is_draw():
            return
            
        if self.game.board[r][c] != 0:
            return
            
        if self.game.make_move(r, c, 1): # Player 1 (Cat)
            self.buttons[r][c].config(image=self.cat_img, text="")
            
            if self.check_game_over():
                return
                
            self.trigger_ai_move()

    def trigger_ai_move(self):
        self.ai_thinking = True
                
        ai_choice = self.ai_var.get()
        if "Minimax" in ai_choice:
            self.status_label.config(text="Minimax thinking...", fg="blue")
            self.update_idletasks()
            
            # depth=4 is usually instantaneous for this size, depth=5 or 6 could be used depending on performance
            best_move = self.game.get_best_move(depth=4)
            # Use after to allow UI strictly synchronous process to breathe momentarily
            self.after(50, self.apply_ai_move, best_move[0] if best_move else None, best_move[1] if best_move else None)
        else:
            self.status_label.config(text="LLM AI thinking...", fg="purple")
            provider = "OpenRouter" if "OpenRouter" in ai_choice else "Google Gemini"
            model = self.ai_models[ai_choice]
            
            moves = self.game.get_available_moves()
            temp = self.temp_slider.get()
            
            # Callback ensures apply_ai_move runs back on the main Tkinter thread via `after(0, ...)`
            def callback(r, c):
                self.after(0, self.apply_ai_move, r, c)
                
            get_llm_move(self.game.board, moves, provider, model, temp, callback)

    def apply_ai_move(self, r, c):
        self.ai_thinking = False
        self.status_label.config(text="Your Turn", fg="green")
        if r is not None and c is not None:
            if self.game.make_move(r, c, 2):  # Player 2 (Dog)
                self.buttons[r][c].config(image=self.dog_img, text="")
        
        self.check_game_over()

    def check_game_over(self):
        winner, coords = self.game.check_win()
        if winner != 0:
            for r, c in coords:
                self.buttons[r][c].config(bg="#ff4d4d") # Highlight winning line in red
            
            if winner == 1:
                self.cat_wins += 1
                self.status_label.config(text="Cats win the round!", fg="orange")
            else:
                self.dog_wins += 1
                self.status_label.config(text="Dogs win the round!", fg="orange")
                
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
            self.status_label.config(text=f"{champion} won the tournament!", fg="red", font=("Arial", 12, "bold"))
            messagebox.showinfo("Tournament Over", f"🎉 {champion} win the tournament! 🎉")
            self.next_round_btn.config(text="New Tournament", state=tk.NORMAL, bg="#2196F3")
        else:
            self.next_round_btn.config(text="Next Round", state=tk.NORMAL, bg="#4CAF50")

    def next_round(self):
        self.ai_thinking = False
        if self.cat_wins >= self.target_wins or self.dog_wins >= self.target_wins:
            # Complete reset for new tournament
            self.cat_wins = 0
            self.dog_wins = 0
            self.update_score()
            
        self.game.reset()
        for r in range(15):
            for c in range(3):
                self.buttons[r][c].config(image="", text=" ", bg="white")
                
        self.status_label.config(text="Ready", fg="green")
        self.next_round_btn.config(text="Next Round", state=tk.DISABLED, bg="#cccccc")

    def update_score(self):
        self.score_label.config(text=f"Cats: {self.cat_wins} | Dogs: {self.dog_wins}")

if __name__ == "__main__":
    app = CatsDogsApp()
    app.mainloop()
