# utils/helpers.py
from datetime import datetime, timedelta
from typing import Tuple

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount"""
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "CAD": "C$"}
    symbol = symbols.get(currency, "$")
    return f"{symbol}{amount:.2f}"

def parse_date(date_string: str) -> datetime:
    """Parse date string to datetime"""
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    return datetime.now()

def get_date_range(days: int) -> Tuple[datetime, datetime]:
    """Get date range for last N days"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date

def calculate_savings_goal(current_spent: float, target_savings: float, monthly_budget: float) -> dict:
    """Calculate savings goal progress"""
    current_savings = monthly_budget - current_spent
    percentage = (current_savings / target_savings) * 100 if target_savings > 0 else 0
    
    return {
        'current_savings': current_savings,
        'target_savings': target_savings,
        'percentage': min(percentage, 100),
        'remaining_needed': max(0, target_savings - current_savings)
    }
