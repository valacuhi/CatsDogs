with open("gui_app.py", "r") as f:
    content = f.read()

content = content.replace('cell_frame = tk.Frame(board_frame, width=45, height=45)', 'cell_frame = tk.Frame(board_frame, width=55, height=55)')
content = content.replace('font=("sans-serif", 18)', 'font=("sans-serif", 14)')
content = content.replace('self.buttons[r][c].config(text="😸", fg="black")', 'self.buttons[r][c].config(text="😸\\n(Cat)", fg="#0044cc")')
content = content.replace('self.buttons[r][c].config(text="🐶", fg="black")', 'self.buttons[r][c].config(text="🐶\\n(Dog)", fg="#cc4400")')

with open("gui_app.py", "w") as f:
    f.write(content)

