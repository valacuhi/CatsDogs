import sys
import os

# Ensure the script directory is in sys.path when executed directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui_app import CatsDogsApp

def main():
    app = CatsDogsApp()
    app.mainloop()

if __name__ == "__main__":
    main()
