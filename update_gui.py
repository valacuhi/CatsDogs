import re

with open("gui_app.py", "r") as f:
    content = f.read()

# 1. Add ai_thinking flag
content = content.replace('self.target_wins = 5\n        self.buttons = []', 'self.target_wins = 5\n        self.buttons = []\n        self.ai_thinking = False')

# 2. Modify grid layout to use fixed sizes and generic font
old_grid = '''        for r in range(15):
            row_buttons = []
            for c in range(3):
                btn = tk.Button(board_frame, text=" ", width=4, height=1, font=("Segoe UI Emoji", 14), 
                                bg="white", command=lambda r=r, c=c: self.on_click(r, c))
                btn.grid(row=r, column=c, padx=1, pady=1) # The grid padding creates the grid lines (from bg="#000000")
                row_buttons.append(btn)
            self.buttons.append(row_buttons)'''

new_grid = '''        for r in range(15):
            row_buttons = []
            for c in range(3):
                cell_frame = tk.Frame(board_frame, width=45, height=45)
                cell_frame.grid(row=r, column=c, padx=1, pady=1)
                cell_frame.pack_propagate(False)
                
                btn = tk.Button(cell_frame, text=" ", font=("sans-serif", 18), bg="white", fg="black",
                                command=lambda r=r, c=c: self.on_click(r, c))
                btn.pack(expand=True, fill="both")
                row_buttons.append(btn)
            self.buttons.append(row_buttons)'''

content = content.replace(old_grid, new_grid)

# 3. Modify on_click to use flag instead of disabled state
old_click = '''    def on_click(self, r, c):
        if self.game.check_win()[0] != 0 or self.game.is_draw():
            return
            
        if self.game.make_move(r, c, 1): # Player 1 (Cat)
            self.buttons[r][c].config(text="😸", state=tk.DISABLED, disabledforeground="black")'''

new_click = '''    def on_click(self, r, c):
        if self.ai_thinking or self.game.check_win()[0] != 0 or self.game.is_draw():
            return
            
        if self.game.board[r][c] != 0:
            return
            
        if self.game.make_move(r, c, 1): # Player 1 (Cat)
            self.buttons[r][c].config(text="😸", fg="black")'''
content = content.replace(old_click, new_click)

# 4. Modify trigger_ai_move and apply_ai_move
old_trigger = '''    def trigger_ai_move(self):
        # Disable all empty buttons while AI thinks
        for r in range(15):
            for c in range(3):
                if self.game.board[r][c] == 0:
                    self.buttons[r][c].config(state=tk.DISABLED)'''

new_trigger = '''    def trigger_ai_move(self):
        self.ai_thinking = True'''
content = content.replace(old_trigger, new_trigger)

old_apply = '''    def apply_ai_move(self, r, c):
        self.status_label.config(text="Your Turn", fg="green")
        if r is not None and c is not None:
            if self.game.make_move(r, c, 2):
                self.buttons[r][c].config(text="🐶", state=tk.DISABLED, disabledforeground="black")
        
        # Restore empty buttons if not over
        if not self.check_game_over():
            for br in range(15):
                for bc in range(3):
                    if self.game.board[br][bc] == 0:
                        self.buttons[br][bc].config(state=tk.NORMAL)'''

new_apply = '''    def apply_ai_move(self, r, c):
        self.ai_thinking = False
        self.status_label.config(text="Your Turn", fg="green")
        if r is not None and c is not None:
            if self.game.make_move(r, c, 2):
                self.buttons[r][c].config(text="🐶", fg="black")
        
        self.check_game_over()'''
content = content.replace(old_apply, new_apply)

# 5. Modify end_round
old_end = '''    def end_round(self):
        # Disable all board interaction permanently for this round
        for r in range(15):
            for c in range(3):
                self.buttons[r][c].config(state=tk.DISABLED)'''
new_end = '''    def end_round(self):
        self.ai_thinking = True # Lock the board logically'''
content = content.replace(old_end, new_end)

# 6. Modify next_round
old_next = '''    def next_round(self):
        if self.cat_wins >= self.target_wins or self.dog_wins >= self.target_wins:
            # Complete reset for new tournament
            self.cat_wins = 0
            self.dog_wins = 0
            self.update_score()
            
        self.game.reset()
        for r in range(15):
            for c in range(3):
                self.buttons[r][c].config(text=" ", bg="white", state=tk.NORMAL)'''
new_next = '''    def next_round(self):
        self.ai_thinking = False
        if self.cat_wins >= self.target_wins or self.dog_wins >= self.target_wins:
            # Complete reset for new tournament
            self.cat_wins = 0
            self.dog_wins = 0
            self.update_score()
            
        self.game.reset()
        for r in range(15):
            for c in range(3):
                self.buttons[r][c].config(text=" ", bg="white")'''
content = content.replace(old_next, new_next)

with open("gui_app.py", "w") as f:
    f.write(content)

