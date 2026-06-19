# Professional Indian Market Backtester

A robust, local, event-driven backtesting engine specifically tailored for the Indian stock market. It fetches historical data directly via `jugaad-data`, operates entirely offline, and features a Streamlit-based user interface where you can write and test custom Python strategies on the fly.

## Features

- **Event-Driven Architecture:** Realistic, bar-by-bar processing preventing look-ahead bias.
- **Indian Market Accuracy:** Simulates standard Indian brokerage calculations (Zerodha approx.), STT, and other exchange taxes.
- **Offline Parquet Storage:** Fast, efficient local storage.
- **Dynamic Strategy Coding:** Write your strategy code directly in the browser and run it instantly.

## How to Install & Run

This project includes automated setup scripts that will check for Python, create an isolated virtual environment (`venv`), install all required dependencies, and launch the dashboard in one go.

### Prerequisites
- Python 3.10 or higher installed and added to your system PATH.

### For Windows Users
Simply double-click the `start.bat` file in the root directory.
Alternatively, open Command Prompt, navigate to the folder, and run:
```cmd
start.bat
```

### For Linux / macOS Users
Open your terminal, navigate to the project directory, and run the shell script:
```bash
./start.sh
```
*(If you get a permission error, make it executable first by running: `chmod +x start.sh`)*

---

## How to Use

1. **Download Data:** Once the Streamlit dashboard opens, navigate to the **"Data Manager"** tab. Select your universe (e.g., NIFTY500 or a custom symbol) and a date range. Click "Download Data". It will be saved locally.
2. **Write Strategy:** Navigate to the **"Backtest Strategy"** tab. You will see a text editor. Write your custom Python class here (it must be named `UserStrategy` and inherit from `Strategy`).
3. **Run Backtest:** Select the symbols you downloaded, set your initial capital, and hit **"Run Backtest"**. The engine will execute your code, calculate metrics (CAGR, Max Drawdown, Sharpe), and plot an interactive equity curve.

## Project Structure

- `/engine/`: Core logic (Events, Portfolio, Execution, Analytics).
- `/ui/`: Streamlit dashboard and dynamic code execution logic.
- `/data/`: (Generated) Where your Parquet files will be stored.
- `start.bat` / `start.sh`: One-click startup scripts.
