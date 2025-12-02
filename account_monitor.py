#!/usr/bin/env python3
"""
GUI Application for Binance Account Monitor
"""

import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
from datetime import datetime, date
from tkcalendar import DateEntry
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
        self.monitor.start_monitoring(interval_minutes=60)
        
        # Initialize filter variables
        self.start_date = None  # Will be set to earliest date by default
        self.selected_accounts = {}  # Dictionary to track selected accounts
        
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
        main_frame.rowconfigure(2, weight=1)
        
        # Control frame for filters
        control_frame = ttk.LabelFrame(main_frame, text="Filters", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        control_frame.columnconfigure(1, weight=1)
        
        # Start Date selection
        date_frame = ttk.Frame(control_frame)
        date_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Label(date_frame, text="Start Date:").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        
        # Date picker widget
        self.date_entry = DateEntry(date_frame, width=12, background='darkblue',
                                    foreground='white', borderwidth=2, year=datetime.now().year)
        self.date_entry.grid(row=0, column=1, padx=(0, 5), sticky=tk.W)
        
        # Clear date button
        clear_date_btn = ttk.Button(date_frame, text="Clear", width=8,
                                    command=self.clear_date_filter)
        clear_date_btn.grid(row=0, column=2, padx=(0, 5), sticky=tk.W)
        
        # Enable/disable date filter checkbox
        self.date_filter_enabled = tk.BooleanVar(value=False)
        date_filter_cb = ttk.Checkbutton(date_frame, text="Filter by date",
                                        variable=self.date_filter_enabled,
                                        command=self.on_filter_change)
        date_filter_cb.grid(row=0, column=3, padx=(0, 0), sticky=tk.W)
        
        # Bind date entry to update charts
        self.date_entry.bind('<<DateEntrySelected>>', lambda e: self.on_filter_change())
        
        # Account selection
        ttk.Label(control_frame, text="Accounts:").grid(row=1, column=0, padx=(0, 5), pady=(10, 0), sticky=(tk.W, tk.N))
        account_frame = ttk.Frame(control_frame)
        account_frame.grid(row=1, column=1, columnspan=2, padx=(0, 0), pady=(10, 0), sticky=(tk.W, tk.E))
        
        # Get account names and create checkboxes
        accounts = self.monitor.config.get("accounts", [])
        for idx, account in enumerate(accounts):
            account_name = account.get("Name")
            var = tk.BooleanVar(value=True)  # All accounts selected by default
            self.selected_accounts[account_name] = var
            cb = ttk.Checkbutton(account_frame, text=account_name, variable=var, 
                                command=self.on_filter_change)
            cb.grid(row=0, column=idx, padx=(0, 15), sticky=tk.W)
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Status: Monitoring...", font=("Arial", 10))
        self.status_label.pack(side=tk.LEFT)
        
        self.last_update_label = ttk.Label(status_frame, text="", font=("Arial", 9))
        self.last_update_label.pack(side=tk.RIGHT)
        
        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Tab 1: Balance Chart
        balance_frame = ttk.Frame(notebook, padding="10")
        notebook.add(balance_frame, text="USDT Balance")
        
        # Tab 2: Annual Return Chart
        return_frame = ttk.Frame(notebook, padding="10")
        notebook.add(return_frame, text="Annual Return")
        
        # Tab 3: Actual Return Chart
        actual_return_frame = ttk.Frame(notebook, padding="10")
        notebook.add(actual_return_frame, text="Actual Return")
        
        # Create charts
        self.create_balance_chart(balance_frame)
        self.create_return_chart(return_frame)
        self.create_actual_return_chart(actual_return_frame)
    
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
    
    def clear_date_filter(self):
        """Clear the date filter and disable it"""
        self.date_filter_enabled.set(False)
        # Set date to today (DateEntry requires a date, but we'll ignore it when checkbox is off)
        self.date_entry.set_date(date.today())
        self.on_filter_change()
    
    def on_filter_change(self):
        """Called when filters change, triggers chart update"""
        self.update_charts()
    
    def get_filtered_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter data based on selected date and accounts"""
        if df is None or df.empty:
            return df
        
        # Filter by date if enabled
        if self.date_filter_enabled.get():
            try:
                selected_date = self.date_entry.get_date()
                # Convert date to datetime for comparison
                start_date = pd.to_datetime(selected_date)
                df = df[df['timestamp'] >= start_date].copy()
            except Exception as e:
                print(f"Error filtering by date: {e}")
                # If date is invalid, show all data
        
        return df
    
    def get_selected_account_names(self) -> list:
        """Get list of selected account names"""
        return [name for name, var in self.selected_accounts.items() if var.get()]
    
    def update_charts(self):
        """Update all charts with latest data"""
        try:
            df = self.monitor.get_historical_data()
            
            if df is not None and not df.empty:
                # Apply filters
                df = self.get_filtered_data(df)
                
                if not df.empty:
                    # Update balance chart
                    self.update_balance_chart(df)
                    
                    # Update return chart
                    self.update_return_chart(df)
                    
                    # Update actual return chart
                    self.update_actual_return_chart(df)
                    
                    # Update status
                    self.last_update_label.config(
                        text=f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                else:
                    self.status_label.config(text="Status: No data after selected date")
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
        
        # Get selected accounts
        selected_accounts = self.get_selected_account_names()
        if len(selected_accounts) == 0:
            return
        
        # Plot each selected account
        for account_name in selected_accounts:
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
        
        # Get selected accounts
        selected_accounts = self.get_selected_account_names()
        if len(selected_accounts) == 0:
            return
        
        # Calculate annual return for each selected account against its own first record
        for account_name in selected_accounts:
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
    
    def create_actual_return_chart(self, parent):
        """Create actual return percentage chart"""
        fig = Figure(figsize=(10, 6), dpi=100)
        self.actual_return_ax = fig.add_subplot(111)
        self.actual_return_ax.set_xlabel("Time")
        self.actual_return_ax.set_ylabel("Actual Return (%)")
        self.actual_return_ax.set_title("Actual Return (Relative to First Record)")
        self.actual_return_ax.grid(True, alpha=0.3)
        self.actual_return_ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
        
        self.actual_return_canvas = FigureCanvasTkAgg(fig, parent)
        self.actual_return_canvas.draw()
        self.actual_return_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def update_actual_return_chart(self, df: pd.DataFrame):
        """Update the actual return percentage chart"""
        self.actual_return_ax.clear()
        self.actual_return_ax.set_xlabel("Time")
        self.actual_return_ax.set_ylabel("Actual Return (%)")
        self.actual_return_ax.set_title("Actual Return (Relative to First Record)")
        self.actual_return_ax.grid(True, alpha=0.3)
        self.actual_return_ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
        
        # Get selected accounts
        selected_accounts = self.get_selected_account_names()
        if len(selected_accounts) == 0:
            return
        
        # Calculate actual return for each selected account against its own first record
        for account_name in selected_accounts:
            if account_name not in df.columns:
                continue
            
            # Find first non-null value for this account
            account_data = df[account_name].dropna()
            if account_data.empty:
                continue
            
            first_index = account_data.index[0]
            first_value = account_data.iloc[0]
            
            if first_value == 0 or pd.isna(first_value):
                continue
            
            # Calculate actual return for each point in time
            returns = []
            timestamps = []
            
            for i in range(len(df)):
                current_index = df.index[i]
                if current_index < first_index:
                    continue
                
                current_value = df.loc[current_index, account_name]
                if pd.isna(current_value):
                    continue
                
                # Calculate actual return: ((current / first) - 1) * 100
                actual_return = ((current_value / first_value) - 1) * 100
                returns.append(actual_return)
                timestamps.append(df.loc[current_index, 'timestamp'])
            
            if returns:
                self.actual_return_ax.plot(timestamps, returns, label=account_name, marker='o', markersize=3)
        
        self.actual_return_ax.legend()
        self.actual_return_ax.tick_params(axis='x', rotation=45)
        self.actual_return_canvas.draw()
    
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

