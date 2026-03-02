import time
from gui_app import CatsDogsApp

def dump_state(app):
    print("ai_thinking:", app.ai_thinking)
    print("board empty?", all(app.game.board[r][c] == 0 for r in range(app.game.rows) for c in range(app.game.cols)))
    print("Clicking")
    try:
        app.on_click(7, 1)
        print("board clicked...")
        app.after(1000, lambda: print("Board after AI turn:", [row for row in app.game.board if any(c != 0 for c in row)]))
    except Exception as e:
        import traceback
        traceback.print_exc()

app = CatsDogsApp()
app.p2_type.set("AI")
app.p2_provider.set("Minimax")
app.setup_controller()
app.after(1000, lambda: dump_state(app))
app.after(4000, lambda: app.destroy())
app.mainloop()
