# Binance Account Monitor

A Python GUI application to monitor Binance account balances and track performance over time.

## Features

- Monitor multiple Binance accounts simultaneously
- Track spot pair balances in USDT equivalent
- Automatic data collection every 5 minutes
- Real-time line charts showing:
  - USDT balance over time for each account
  - Annual return percentage relative to each account's first record
  - Actual return percentage (non-annualized) for short-term tracking
- Historical data saved to CSV file

## Installation

1. Install Python 3.7 or higher

2. Install system-level dependencies (required for GUI):
   
   **On Debian/Ubuntu:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-tk
   ```
   
   **On Fedora/RHEL:**
   ```bash
   sudo dnf install python3-tkinter
   ```
   
   **On Arch Linux:**
   ```bash
   sudo pacman -S tk
   ```

3. Install Python packages:
```bash
pip install -r requirements.txt
```

4. If you encounter `ImportError: cannot import name 'ImageTk' from 'PIL'`, upgrade Pillow:
```bash
pip install --upgrade pillow
```

## Troubleshooting

### ModuleNotFoundError: No module named 'tkinter'
- Install the system package for tkinter (see step 2 above)
- The package name varies by Linux distribution

### ImportError: cannot import name 'ImageTk' from 'PIL'
- Upgrade Pillow to a newer version: `pip install --upgrade pillow`
- This usually happens when matplotlib requires ImageTk but the system Pillow version is too old

## Configuration

1. Edit `monitorAccounts.conf` and add your Binance API credentials:

```json
{
  "pair": "USDCUSDT",
  "accounts": [
    {
      "Name": "Account1",
      "apiKey": "your_api_key_here",
      "secretKey": "your_secret_key_here"
    },
    {
      "Name": "Account2",
      "apiKey": "another_api_key",
      "secretKey": "another_secret_key"
    }
  ]
}
```

**Important:** 
- Replace `"xxx"` with your actual Binance API keys
- The `pair` field specifies which trading pair to monitor (e.g., "USDCUSDT", "BTCUSDT")
- The application will track the balance of the base asset in that pair and convert it to USDT

## Usage

Run the GUI application:

```bash
python3 account_monitor.py
```

The application will:
- Start monitoring all configured accounts
- Save balance data to `balance_history.csv` every 5 minutes
- Display real-time charts updating every 30 seconds

## How It Works

1. **Balance Calculation**: For each account, the app:
   - Gets the balance of the base asset in the configured trading pair
   - Fetches the current price of the pair
   - Converts the value to USDT equivalent

2. **Data Storage**: Balance data is saved to `balance_history.csv` with timestamps

3. **Return Calculations**: 
   - **Annual Return**: Calculates each account's annual return against its own first record, annualized based on time elapsed
   - **Actual Return**: Shows the non-annualized percentage change from the first record, providing a clearer view of short-term performance without the magnification effect of annualization

## Files

- `account_monitor.py` - Main GUI application
- `binance_monitor.py` - Binance API integration and data management
- `monitorAccounts.conf` - Configuration file with API keys
- `balance_history.csv` - Historical balance data (created automatically)
- `requirements.txt` - Python dependencies

## Security Note

Keep your `monitorAccounts.conf` file secure and never commit it to version control. The application only requires read permissions for your Binance account balances.


