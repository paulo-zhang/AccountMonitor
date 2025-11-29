#!/usr/bin/env python3
"""
GUI Application for Binance Account Monitor
"""

import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
from datetime import datetime
from binance_monitor import BinanceMonitor


class AccountMonitorGUI:
    """Main GUI application for monitoring Binance accounts"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Binance Account Monitor")
        self.root.geometry("1200x800")
        
        # Initialize monitor
        try:
            self.monitor = BinanceMonitor()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")
            self.root.destroy()
            return
        
        # Start monitoring
        self.monitor.start_monitoring(interval_minutes=5)
        
        # Create GUI elements
        self.create_widgets()
        
        # Start update loop
        self.update_charts()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """Create and layout GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Status: Monitoring...", font=("Arial", 10))
        self.status_label.pack(side=tk.LEFT)
        
        self.last_update_label = ttk.Label(status_frame, text="", font=("Arial", 9))
        self.last_update_label.pack(side=tk.RIGHT)
        
        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Tab 1: Balance Chart
        balance_frame = ttk.Frame(notebook, padding="10")
        notebook.add(balance_frame, text="USDT Balance")
        
        # Tab 2: Annual Return Chart
        return_frame = ttk.Frame(notebook, padding="10")
        notebook.add(return_frame, text="Annual Return")
        
        # Create charts
        self.create_balance_chart(balance_frame)
        self.create_return_chart(return_frame)
    
    def create_balance_chart(self, parent):
        """Create balance line chart"""
        fig = Figure(figsize=(10, 6), dpi=100)
        self.balance_ax = fig.add_subplot(111)
        self.balance_ax.set_xlabel("Time")
        self.balance_ax.set_ylabel("USDT Value")
        self.balance_ax.set_title("Account Balances (USDT)")
        self.balance_ax.grid(True, alpha=0.3)
        
        self.balance_canvas = FigureCanvasTkAgg(fig, parent)
        self.balance_canvas.draw()
        self.balance_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_return_chart(self, parent):
        """Create annual return chart"""
        fig = Figure(figsize=(10, 6), dpi=100)
        self.return_ax = fig.add_subplot(111)
        self.return_ax.set_xlabel("Time")
        self.return_ax.set_ylabel("Annual Return (%)")
        self.return_ax.set_title("Annual Return (Relative to First Account)")
        self.return_ax.grid(True, alpha=0.3)
        self.return_ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
        
        self.return_canvas = FigureCanvasTkAgg(fig, parent)
        self.return_canvas.draw()
        self.return_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def update_charts(self):
        """Update both charts with latest data"""
        try:
            df = self.monitor.get_historical_data()
            
            if df is not None and not df.empty:
                # Update balance chart
                self.update_balance_chart(df)
                
                # Update return chart
                self.update_return_chart(df)
                
                # Update status
                self.last_update_label.config(
                    text=f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            else:
                self.status_label.config(text="Status: Waiting for data...")
        
        except Exception as e:
            print(f"Error updating charts: {e}")
        
        # Schedule next update (every 30 seconds)
        self.root.after(30000, self.update_charts)
    
    def update_balance_chart(self, df: pd.DataFrame):
        """Update the balance line chart"""
        self.balance_ax.clear()
        self.balance_ax.set_xlabel("Time")
        self.balance_ax.set_ylabel("USDT Value")
        self.balance_ax.set_title("Account Balances (USDT)")
        self.balance_ax.grid(True, alpha=0.3)
        
        accounts = self.monitor.config.get("accounts", [])
        if len(accounts) == 0:
            return
        
        # Get first account name as base
        base_account = accounts[0].get("Name")
        
        # Plot each account
        for account in accounts:
            account_name = account.get("Name")
            if account_name in df.columns:
                values = df[account_name].dropna()
                if not values.empty:
                    timestamps = df.loc[values.index, 'timestamp']
                    self.balance_ax.plot(timestamps, values, label=account_name, marker='o', markersize=3)
        
        self.balance_ax.legend()
        self.balance_ax.tick_params(axis='x', rotation=45)
        self.balance_canvas.draw()
    
    def update_return_chart(self, df: pd.DataFrame):
        """Update the annual return chart"""
        self.return_ax.clear()
        self.return_ax.set_xlabel("Time")
        self.return_ax.set_ylabel("Annual Return (%)")
        self.return_ax.set_title("Annual Return (Relative to First Record)")
        self.return_ax.grid(True, alpha=0.3)
        self.return_ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
        
        accounts = self.monitor.config.get("accounts", [])
        if len(accounts) == 0:
            return
        
        # Calculate annual return for each account against its own first record
        for account in accounts:
            account_name = account.get("Name")
            
            if account_name not in df.columns:
                continue
            
            # Calculate rolling annual return for each point in time
            returns = []
            timestamps = []
            
            # Find first non-null value for this account
            account_data = df[account_name].dropna()
            if account_data.empty:
                continue
            
            first_index = account_data.index[0]
            
            # Calculate return for each subsequent point
            for i in range(1, len(df)):
                current_index = df.index[i]
                if current_index < first_index:
                    continue
                
                # Get data from first record to current point
                df_subset = df.loc[first_index:current_index]
                
                # Calculate annual return against first record
                annual_return = self.monitor.calculate_account_annual_return(df_subset, account_name)
                
                if annual_return is not None:
                    returns.append(annual_return)
                    timestamps.append(df_subset.iloc[-1]['timestamp'])
            
            if returns:
                self.return_ax.plot(timestamps, returns, label=account_name, marker='o', markersize=3)
        
        self.return_ax.legend()
        self.return_ax.tick_params(axis='x', rotation=45)
        self.return_canvas.draw()
    
    def on_closing(self):
        """Handle window closing"""
        self.monitor.stop_monitoring()
        self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = AccountMonitorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

