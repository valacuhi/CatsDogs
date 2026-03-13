# Cats vs Dogs TicTacToe - AI Evolution Workbench

A dynamic, modernized take on Tic-Tac-Toe functioning as an AI experimentation workbench. The application allows humans and AI agents (powered by both local and cloud LLMs) to compete in advanced variants of Tic-Tac-Toe (15x3 or 12x4 grid layouts) with complex win conditions.

This project serves as a Python practice platform with a strong focus on decoupled MVC architectures, agent-based game loops, and testing the reasoning capabilities of Local LLMs (Ollama) and Cloud LLMs (Google Gemini, OpenRouter) against traditional deterministic algorithms (Minimax, Monte Carlo Tree Search).

## Key Features

- **Advanced Variants:** Play on non-standard grids like 15x3 (requires 4 vertical, 3 horizontal/diagonal) or 12x4 (requires 4-in-a-row in any direction).
- **Agent Orchestration:** Choose between Human, Minimax, MCTS, or LLM-based competitors for Player 1 (Cats) and Player 2 (Dogs).
- **Interactive Workbench:** Adjust AI depth, MCTS simulations, and LLM 'temperature' on the fly. You can also inject specific system prompt strategies.
- **Centaur & Error Fallbacks:** Enable Centaur mode to play alongside an AI, or Fallback mode so traditional algorithms instantly take over if an LLM throws an API timeout.
- **Comprehensive Move Logging:** Tracks every turn's latency, agent interventions, and exact mathematically evaluated safety profiles.

## Architecture Highlights
The codebase employs a clean Model-View-Controller (MVC) and Strategy pattern:
- `game_logic.py`: The core domain model handling pure state and win validations.
- `game_controller.py`: The orchestrator handling the asynchronous background game loop to prevent GUI freezing.
- `agents/`: A modular directory standardizing `BaseAgent`. Allows instantaneous swapping between `human_agent.py`, `minimax_agent.py`, `mcts_agent.py`, and `llm_agent.py` without mutating the core engine.
- `gui_app.py`: A decoupled Tkinter view overlay that strictly renders state events raised by the controller.

## Playing without Python (Windows)
If you just want to play the game on Windows without installing Python or setting up an environment, you can download the ready-to-run `.exe` file:
1. Go to the **Actions** tab at the top of this GitHub repository.
2. Click on the latest green successful run under "Build Windows Executable".
3. Scroll to the bottom of the page to the **Artifacts** section.
4. Download the `CatsDogs-Windows-Exe.zip` file, extract it, and double-click `CatsDogs.exe` to play!
*(Note: You will still need to place your `.env` file in the same folder as the `.exe` if you want to use the Cloud LLM agents.)*

## Installation & Setup

If you are a student running this project for the first time, follow these steps to install the required dependencies and configure your API keys.

1. **Clone the repository and enter the directory**
   ```bash
   git clone https://github.com/valacuhi/CatsDogs.git
   cd CatsDogs
   ```

2. **Create and activate a virtual environment**
   - *Windows:*
     ```bash
     python -m venv venv
     venv\\Scripts\\activate
     ```
   - *Mac/Linux:*
     ```bash
     python -m venv venv
     source venv/bin/activate
     ```

3. **Install the dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API Keys**
   To use the Cloud LLMs (like Gemini or OpenRouter), you must provide your own API keys.
   - Copy the provided template file:
     ```bash
     cp .env.template .env
     ```
     *(On Windows Command Prompt, use `copy .env.template .env`)*
   - Open the new `.env` file in a text editor and paste your personal API keys next to the corresponding variables.

5. **Run the Application**
   ```bash
   python gui_app.py
   ```

## Move History Logger
The Move History panel on the right side of the screen offers an incredibly detailed timeline of the current match.

### Game Header
The first two lines summarize the configurations of the match:
```text
15x3; Ryzen AI 9; Centaur NO NO; ErrFallback NO YES; AutoPlay NO
human; oll(Local DeepSeek, t=0.1)
```
- **Line 1:** States the grid variant, host hardware, Centaur/Fallback toggles for P1 and P2 respectively, and the auto-play setting.
- **Line 2:** Short-codes representing the identity of Player 1 and Player 2 for the round.

### Turn Footprints
Each row tracks a chronological turn sequence:
```text
01 H2 hu                | G2 mm(4) 0.06
02 I1 hu                | I3 FB mm(4) 0.01 
03 J3 hu                | E2 INT go(gemini-2.5-pro, t=0.1) 0.81
04 J4 hu                | D2 FB mm(4) 0.12 D2-XXXX
```
- `01`: The current turn number.
- `H2 / G2`: The coordinate where the token was placed (Row alphabet, Column number).
- `hu / mm(4) / oll / go`: The agent short-code that explicitly placed the token.
   - `hu`: Human
   - `mm(x)`: Minimax at Depth X
   - `mcts(x)`: Monte Carlo at X simulations
   - `oll(model, t=0.1)`: Local Ollama model at Temperature 0.1
   - `go(model, t=0.1)`: Google Gemini model at Temperature 0.1
- `FB`: **Fallback**. Signifies the original LLM agent encountered an API timeout or hallucinated coordinates, prompting the deterministic algorithm to step in and save the turn.
- `INT`: **Intervention**. Signifies a configuration changed on the fly during the match, such as sliding the Temperature setting, effectively changing the AI's "brain" mid-round.
- `0.06`: Processing latency to execute the turn in seconds.
- `D2-XXXX` or `F1-I4`: The Win String describing the shape and coordinates of the winning lineup.
