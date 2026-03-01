#!/usr/bin/env python3

"""
Tic-Tac-Toe: 15x3 (GUI Version)
A graphical, mouse-based game for two players or vs. CPU.

Rules:
- 4-in-a-row vertically wins.
- 3-in-a-row horizontally or diagonally wins.
"""

import tkinter as tk
from tkinter import font, messagebox
import random

# --- Game Constants --- Defines basic parameters of the game
ROWS = 15 
COLS = 3
EMPTY = ' '  # <-- MODIFIED: Changed from '.' to ' '
PLAYER_X = '\U0001F638' # Always Human
PLAYER_O = '\U0001F63E' # Human or Computer

# --- Core Game Logic ---
def create_board_logic():
    """Returns a 15x3 list-of-lists model of the board."""
    return [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]

def check_win(board, player):
    """Checks the board model for any winning condition."""
    # 1. Check Vertical Wins (4-in-a-row)
    for c in range(COLS):
        for r in range(ROWS - 3):
            if (board[r][c] == player and
                board[r+1][c] == player and
                board[r+2][c] == player and
                board[r+3][c] == player):
                return [(r, c), (r+1, c), (r+2, c), (r+3, c)]
    # 2. Check Horizontal Wins (3-in-a-row)
    for r in range(ROWS):
        if (board[r][0] == player and
            board[r][1] == player and
            board[r][2] == player):
            return [(r, 0), (r, 1), (r, 2)]
    # 3. Check Diagonal (Down-Right) Wins (3-in-a-row)
    for r in range(ROWS - 2):
        if (board[r][0] == player and
            board[r+1][1] == player and
            board[r+2][2] == player):
            return [(r, 0), (r+1, 1), (r+2, 2)]
    # 4. Check Diagonal (Down-Left) Wins (3-in-a-row)
    for r in range(ROWS - 2):
        if (board[r][2] == player and
            board[r+1][1] == player and
            board[r+2][0] == player):
            return [(r, 2), (r+1, 1), (r+2, 0)]
    return None

def is_board_full(board):
    """Checks if the board model is completely full."""
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == EMPTY:
                return False 
    return True

# --- NEW: AI Helper Function ---
def find_potential_vertical_move(board, player, length):
    """
    Finds a move to extend (or block) a vertical line of 'length' for 'player'.
    e.g., length=2 -> finds 2-in-a-row and returns the empty spot to make it 3.
    """
    for c in range(COLS):
        for r in range(ROWS - length):
            # Check for 'length' pieces in a row
            is_threat = True
            for i in range(length):
                if board[r+i][c] != player:
                    is_threat = False
                    break
            
            if is_threat:
                # Found 'length' pieces. Can we play *below*?
                if (r + length) < ROWS and board[r + length][c] == EMPTY:
                    # e.g., found 2 at (5,0), (6,0). Play at (7,0).
                    return (r + length, c) 
                
                # Can we play *above*?
                if (r - 1) >= 0 and board[r - 1][c] == EMPTY:
                    # e.g., found 2 at (5,0), (6,0). Play at (4,0).
                    return (r - 1, c)
    return None


# --- MODIFIED: Stronger AI ---
def get_computer_move(board, ai_marker, human_marker):
    """
    Generates a move for the AI with a clear priority list.
    """
    empty_cells = []
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == EMPTY:
                empty_cells.append((r, c))
    
    if not empty_cells: return None
    if len(empty_cells) == ROWS * COLS: return random.choice(empty_cells)

    # Priority 1: Win (1-ply)
    for r, c in empty_cells:
        board[r][c] = ai_marker
        if check_win(board, ai_marker):
            board[r][c] = EMPTY
            return (r, c)
        board[r][c] = EMPTY
        
    # Priority 2: Block (1-ply)
    for r, c in empty_cells:
        board[r][c] = human_marker
        if check_win(board, human_marker):
            board[r][c] = EMPTY
            return (r, c)
        board[r][c] = EMPTY
        
    # Priority 3: Block human's 3-in-a-row vertical (to prevent 4-win)
    move = find_potential_vertical_move(board, human_marker, 3)
    if move and move in empty_cells:
        return move

    # Priority 4: Build AI's 3-in-a-row vertical (to make 4-win)
    move = find_potential_vertical_move(board, ai_marker, 3)
    if move and move in empty_cells:
        return move

    # Priority 5: Block human's 2-in-a-row vertical
    move = find_potential_vertical_move(board, human_marker, 2)
    if move and move in empty_cells:
        return move

    # Priority 6: Build AI's 2-in-a-row vertical
    move = find_potential_vertical_move(board, ai_marker, 2)
    if move and move in empty_cells:
        return move
        
    # Priority 7: Random
    return random.choice(empty_cells)


# --- (2) GUI Application Class ---

class TicTacToeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("15x3 Tic-Tac-Toe")
        self.root.resizable(False, False) 
        
        # Define fonts
        self.cell_font = font.Font(family='Helvetica', size=12, weight='bold')
        self.label_font = font.Font(family='Helvetica', size=14)
        self.button_font = font.Font(family='Helvetica', size=12)

        # Game state variables
        self.board_model = create_board_logic()
        self.current_player = PLAYER_X
        self.game_mode = None # 'PvP' or 'PvC'
        self.game_over = True
        
        # --- MODIFIED: Switched to root.grid() layout ---
        
        # Configure the main window's grid
        self.root.grid_columnconfigure(0, weight=1)
        
        # Frame for the board grid
        self.board_frame = tk.Frame(root)
        self.board_frame.grid(row=0, column=0, padx=10, pady=(10, 0)) # Board is row 0

        # Frame for status label and menu buttons
        self.menu_frame = tk.Frame(root)
        self.menu_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=(0, 10)) # Menu is row 1
        
        # A 2D list to hold the button widgets
        self.cell_buttons = []
        self.create_board_widgets()
        
        # --- Configure the Menu Frame's internal grid ---
        
        # Column 0 (status) gets all the extra space
        self.menu_frame.grid_columnconfigure(0, weight=1, minsize=300)
        
        # Status label
        self.status_label = tk.Label(self.menu_frame, text="Select a game mode to start!", font=self.label_font, anchor='w')
        self.status_label.grid(row=0, column=0, sticky='ew', padx=5) # 'ew' = stretch
        
        # Radio Buttons
        self.starter_var = tk.StringVar(value='human')
        self.radio_human = tk.Radiobutton(
            self.menu_frame, text="You Start", variable=self.starter_var,
            value='human', state='disabled', command=self.on_starter_select
        )
        self.radio_human.grid(row=0, column=1, padx=5)
        
        self.radio_cpu = tk.Radiobutton(
            self.menu_frame, text="CPU Starts", variable=self.starter_var,
            value='cpu', state='disabled', command=self.on_starter_select
        )
        self.radio_cpu.grid(row=0, column=2, padx=5)
        
        # Menu buttons
        self.quit_button = tk.Button(self.menu_frame, text="Quit", font=self.button_font, command=root.quit)
        self.quit_button.grid(row=0, column=3, padx=5 )
        
        self.reset_button = tk.Button(self.menu_frame, text="New Game", font=self.button_font, command=self.prompt_game_mode)
        self.reset_button.grid(row=0, column=4, padx=5)
        
        # Initial prompt to start
        self.prompt_game_mode()

    def prompt_game_mode(self):
        """Asks the user to select Player vs Player or Player vs Computer."""
        self.root.withdraw() 
        
        choice = messagebox.askquestion("New Game", "Welcome to 15x3 Tic-Tac-Toe!\n\nDo you want to play against the computer?",
                                        icon='question', type='yesnocancel')
        
        if choice == 'yes':
            self.game_mode = 'PvC'
            self.start_game()
        elif choice == 'no':
            self.game_mode = 'PvP'
            self.start_game()
        else: # 'cancel' or closed dialog
            self.root.quit()
            return

        self.root.deiconify()

    def start_game(self):
        """Initializes all game variables for a new game."""
        self.game_over = True 
        self.board_model = create_board_logic()
        
        # Reset the visual appearance of all buttons
        for r in range(ROWS):
            for c in range(COLS):
                button = self.cell_buttons[r][c]
                # <-- MODIFIED: Set fg='black' to reset winner's red
                button.config(text=EMPTY, fg='black', bg='#f0f0f0')
        
        if self.game_mode == 'PvP':
            self.current_player = PLAYER_X
            self.radio_human.config(state='disabled')
            self.radio_cpu.config(state='disabled')
            self.game_over = False
            self.update_status_label()
            
        elif self.game_mode == 'PvC':
            self.radio_human.config(state='normal')
            self.radio_cpu.config(state='normal')
            self.starter_var.set('human')
            self.status_label.config(text="Please select who starts.")

    def on_starter_select(self):
        """Called when a radio button is clicked (only in PvC mode)."""
        if self.game_over is False:
            return 
            
        self.game_over = False # The game officially begins NOW
        
        self.radio_human.config(state='disabled')
        self.radio_cpu.config(state='disabled')
        
        starter = self.starter_var.get()
        
        if starter == 'human':
            self.current_player = PLAYER_X
            self.update_status_label()
        else: # 'cpu'
            self.current_player = PLAYER_O
            self.update_status_label()
            self.root.after(250, self.computer_turn)

    def create_board_widgets(self):
        """Creates the 15x3 grid of buttons and row/col labels."""
        # Create Column Headers (1, 2, 3)
        for c in range(COLS):
            label = tk.Label(self.board_frame, text=f"{c+1}", font=self.cell_font, width=4)
            label.grid(row=0, column=c+1, pady=2)
        # Create Row Headers (1-15) and Cell Buttons
        for r in range(ROWS):
            label = tk.Label(self.board_frame, text=f"{r+1}", font=self.cell_font, width=3)
            label.grid(row=r+1, column=0, padx=2)
            row_list = []
            for c in range(COLS):
                button = tk.Button(
                    self.board_frame, text=EMPTY, font=self.cell_font, #<-- MODIFIED
                    width=2, height=1,
                    command=lambda r=r, c=c: self.on_cell_click(r, c)
                )
                button.grid(row=r+1, column=c+1, padx=2, pady=2)
                row_list.append(button)
            self.cell_buttons.append(row_list)

    def update_status_label(self):
        """Updates the text at the bottom of the window."""
        if self.game_over:
            return
            
        player_name = self.current_player
        if self.game_mode == 'PvC':
            player_name = "Your (X)" if self.current_player == PLAYER_X else "Computer (O)"
        
        self.status_label.config(text=f"Turn: Player {player_name}")

    def on_cell_click(self, r, c):
        """Handles a human player clicking on a cell."""
        
        if (self.game_over or
            self.board_model[r][c] != EMPTY or
            (self.game_mode == 'PvC' and self.current_player == PLAYER_O)):
            return

        self.process_move(r, c)

    def computer_turn(self):
        """Handles the AI's turn."""
        if self.game_over:
            return

        # Add "thinking" time
        self.root.after(500, self.run_computer_move)
        
    def run_computer_move(self):
        """Separated logic so 'thinking' delay doesn't freeze UI"""
        move = get_computer_move(self.board_model, PLAYER_O, PLAYER_X)
        
        if move:
            r, c = move
            self.process_move(r, c)
        
    def process_move(self, r, c):
        """
        The core function called by both human and AI to make a move.
        """
        if self.game_over: return # Extra check
        
        # 1. Update the logical board
        self.board_model[r][c] = self.current_player
        
        # 2. Update the visual button
        player_color = 'blue' if self.current_player == PLAYER_X else 'green'
        self.cell_buttons[r][c].config(text=self.current_player, fg=player_color)
        
        # 3. Check for win
        winning_coords = check_win(self.board_model, self.current_player)
        if winning_coords:
            self.end_game(winner=self.current_player, coords=winning_coords)
            return

        # 4. Check for draw
        if is_board_full(self.board_model):
            self.end_game(winner=None, coords=None)
            return
            
        # 5. If no win/draw, switch player
        self.current_player = PLAYER_O if self.current_player == PLAYER_X else PLAYER_X
        self.update_status_label()
        
        # 6. If now computer's turn, trigger it
        if self.game_mode == 'PvC' and self.current_player == PLAYER_O:
            self.computer_turn()

    def end_game(self, winner, coords):
        """Called when the game ends in a win or draw."""
        self.game_over = True
        
        if winner:
            if coords:
                # <-- MODIFIED: Change text color to red, not bg to yellow
                for r, c in coords:
                    self.cell_buttons[r][c].config(fg='red')
            
            winner_name = "You (X)" if winner == PLAYER_X else "Computer (O)"
            if self.game_mode == 'PvP':
                winner_name = f"Player {winner}"
            
            self.status_label.config(text=f"🎉 {winner_name} wins!")
            
        else: # It's a draw
            self.status_label.config(text="🤝 The game is a draw.")

# --- (3) Main execution ---

if __name__ == "__main__":
    root = tk.Tk()
    app = TicTacToeGUI(root)
    root.mainloop()
