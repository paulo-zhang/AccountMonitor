#!/usr/bin/env python3
"""
Binance Account Monitor
Monitors account balances and displays them in a GUI with charts
"""

import json
import os
import threading
import time
from datetime import datetime
from typing import Optional
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException


class BinanceMonitor:
    """Handles Binance API connections and balance fetching"""
    
    def __init__(self, config_path: str = "monitorAccounts.conf"):
        self.config_path = config_path
        self.config = self.load_config()
        self.clients = {}
        self.data_file = "balance_history.csv"
        self.running = False
        self.thread = None
        
        # Initialize Binance clients for each account
        self._initialize_clients()
        
    def load_config(self) -> dict:
        """Load configuration from JSON file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def _initialize_clients(self):
        """Initialize Binance API clients for each account"""
        for account in self.config.get("accounts", []):
            name = account.get("Name")
            api_key = account.get("apiKey")
            secret_key = account.get("secretKey")
            
            if api_key and secret_key and api_key != "xxx" and secret_key != "xxx":
                try:
                    self.clients[name] = Client(api_key, secret_key)
                except Exception as e:
                    print(f"Error initializing client for {name}: {e}")
    
    def get_balance(self, account_name: str) -> Optional[float]:
        """Get USDT equivalent balance for an account based on the spot pair"""
        if account_name not in self.clients:
            return None
        
        try:
            client = self.clients[account_name]
            pair = self.config.get("pair", "USDCUSDT")
            
            # Get account balances
            account_info = client.get_account()
            balances = {item['asset']: float(item['free']) + float(item['locked']) 
                       for item in account_info['balances'] if float(item['free']) + float(item['locked']) > 0}
            
            # Parse the trading pair to get base and quote assets
            # For pairs like USDCUSDT, BTCUSDT, etc.
            # Try common quote assets first (longest first to avoid partial matches)
            quote_assets = ["USDT", "BUSD", "USDC", "BTC", "ETH"]
            base_asset = None
            quote_asset = None
            
            # Sort by length descending to match longest first
            quote_assets_sorted = sorted(quote_assets, key=len, reverse=True)
            for quote in quote_assets_sorted:
                if pair.endswith(quote):
                    base_asset = pair[:-len(quote)]
                    quote_asset = quote
                    break
            
            if not base_asset or not quote_asset:
                # Fallback: try to get exchange info to determine base/quote
                try:
                    exchange_info = client.get_exchange_info()
                    for symbol_info in exchange_info['symbols']:
                        if symbol_info['symbol'] == pair:
                            base_asset = symbol_info['baseAsset']
                            quote_asset = symbol_info['quoteAsset']
                            break
                except:
                    pass
            
            if not base_asset:
                return None
            
            # Get balance of the base asset
            base_balance = balances.get(base_asset, 0)
            
            # Get current price for the pair (price is in quote asset)
            ticker = client.get_symbol_ticker(symbol=pair)
            price = float(ticker['price'])
            
            # Calculate value in quote asset
            quote_value = base_balance * price
            
            # Convert quote value to USDT
            if quote_asset == "USDT":
                # Already in USDT
                usdt_value = quote_value
            elif quote_asset in ["USDC", "BUSD"]:
                # Stablecoins, typically 1:1 with USDT
                usdt_value = quote_value
            else:
                # Need to convert quote asset to USDT
                try:
                    quote_ticker = client.get_symbol_ticker(symbol=f"{quote_asset}USDT")
                    quote_usdt_price = float(quote_ticker['price'])
                    usdt_value = quote_value * quote_usdt_price
                except:
                    # If conversion pair doesn't exist, return None
                    return None
            
            # Also add any direct USDT balance
            usdt_balance = balances.get("USDT", 0)
            
            return usdt_value + usdt_balance
            
        except BinanceAPIException as e:
            print(f"Binance API error for {account_name}: {e}")
            return None
        except Exception as e:
            print(f"Error getting balance for {account_name}: {e}")
            return None
    
    def save_balance_data(self):
        """Save current balance data to CSV file"""
        timestamp = datetime.now()
        data = {"timestamp": timestamp}
        
        for account in self.config.get("accounts", []):
            account_name = account.get("Name")
            balance = self.get_balance(account_name)
            data[account_name] = balance
        
        # Load existing data or create new DataFrame
        if os.path.exists(self.data_file):
            df = pd.read_csv(self.data_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        else:
            df = pd.DataFrame()
        
        # Append new row
        new_row = pd.DataFrame([data])
        df = pd.concat([df, new_row], ignore_index=True)
        
        # Save to CSV
        df.to_csv(self.data_file, index=False)
        
        return data
    
    def start_monitoring(self, interval_minutes: int = 5):
        """Start monitoring in background thread"""
        if self.running:
            return
        
        self.running = True
        interval_seconds = interval_minutes * 60
        
        def monitor_loop():
            while self.running:
                try:
                    self.save_balance_data()
                    print(f"Balance data saved at {datetime.now()}")
                except Exception as e:
                    print(f"Error in monitoring loop: {e}")
                
                time.sleep(interval_seconds)
        
        self.thread = threading.Thread(target=monitor_loop, daemon=True)
        self.thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
    
    def get_historical_data(self) -> Optional[pd.DataFrame]:
        """Load historical balance data from CSV"""
        if not os.path.exists(self.data_file):
            return None
        
        try:
            df = pd.read_csv(self.data_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        except Exception as e:
            print(f"Error loading historical data: {e}")
            return None
    
    def calculate_annual_return(self, df: pd.DataFrame, account_name: str, base_account: str) -> Optional[float]:
        """Calculate annual return percentage based on first account as base"""
        if df is None or df.empty:
            return None
        
        if account_name not in df.columns or base_account not in df.columns:
            return None
        
        # Get first values
        first_row = df.iloc[0]
        first_base_value = first_row[base_account]
        first_account_value = first_row[account_name]
        
        if pd.isna(first_base_value) or pd.isna(first_account_value) or first_base_value == 0:
            return None
        
        # Get latest values
        last_row = df.iloc[-1]
        last_base_value = last_row[base_account]
        last_account_value = last_row[account_name]
        
        if pd.isna(last_base_value) or pd.isna(last_account_value):
            return None
        
        # Calculate time difference in years
        time_diff = (df.iloc[-1]['timestamp'] - df.iloc[0]['timestamp']).total_seconds() / (365.25 * 24 * 3600)
        
        if time_diff <= 0:
            return None
        
        # Calculate return relative to base account
        # If base account changed, we adjust for that
        base_change = (last_base_value / first_base_value) if first_base_value > 0 else 1
        account_change = (last_account_value / first_account_value) if first_account_value > 0 else 1
        
        # Relative return
        relative_return = (account_change / base_change - 1) if base_change > 0 else 0
        
        # Annualize
        annual_return = (relative_return / time_diff) * 100 if time_diff > 0 else 0
        
        return annual_return
    
    def calculate_account_annual_return(self, df: pd.DataFrame, account_name: str) -> Optional[float]:
        """Calculate annual return percentage for an account against its own first record"""
        if df is None or df.empty:
            return None
        
        if account_name not in df.columns:
            return None
        
        # Find first non-null value for this account
        account_data = df[account_name].dropna()
        if account_data.empty:
            return None
        
        first_index = account_data.index[0]
        first_value = account_data.iloc[0]
        
        if first_value == 0 or pd.isna(first_value):
            return None
        
        # Get latest value
        last_value = account_data.iloc[-1]
        if pd.isna(last_value):
            return None
        
        # Calculate time difference in years
        first_timestamp = df.loc[first_index, 'timestamp']
        last_timestamp = df.loc[account_data.index[-1], 'timestamp']
        time_diff = (last_timestamp - first_timestamp).total_seconds() / (365.25 * 24 * 3600)
        
        if time_diff <= 0:
            return None
        
        # Calculate return
        return_pct = ((last_value / first_value) - 1) if first_value > 0 else 0
        
        # Annualize
        annual_return = (return_pct / time_diff) * 100 if time_diff > 0 else 0
        
        return annual_return

