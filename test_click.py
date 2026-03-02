import tkinter as tk
from gui_app import CatsDogsApp

def dump_state(app):
    print("ai_thinking:", app.ai_thinking)
    print("board empty?", all(app.game.board[r][c] == 0 for r in range(app.game.rows) for c in range(app.game.cols)))
    try:
        app.on_click(7, 1)
        print("clicked")
    except Exception as e:
        import traceback
        traceback.print_exc()
        
app = CatsDogsApp()
app.after(1000, lambda: dump_state(app))
app.after(2000, lambda: app.destroy())
app.mainloop()
