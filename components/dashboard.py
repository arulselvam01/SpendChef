# components/dashboard.py
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

class DashboardWidgets:
    """Dashboard visualization widgets"""
    
    @staticmethod
    def budget_gauge(current_spent: float, monthly_budget: float):
        """Create budget gauge chart"""
        percentage = (current_spent / monthly_budget) * 100 if monthly_budget > 0 else 0
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = current_spent,
            title = {'text': "Budget Spent"},
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [None, monthly_budget]},
                'bar': {'color': "#FF6B6B"},
                'steps': [
                    {'range': [0, monthly_budget * 0.5], 'color': "lightgreen"},
                    {'range': [monthly_budget * 0.5, monthly_budget * 0.8], 'color': "yellow"},
                    {'range': [monthly_budget * 0.8, monthly_budget], 'color': "orange"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': monthly_budget
                }
            }
        ))
        
        fig.update_layout(height=300)
        return fig
    
    @staticmethod
    def spending_timeline(transactions: list, days: int = 30):
        """Create spending timeline chart"""
        if not transactions:
            return None
        
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        df = df[df['date'] >= datetime.now() - timedelta(days=days)]
        
        daily_spending = df.groupby(df['date'].dt.date)['amount'].sum().reset_index()
        
        fig = px.line(daily_spending, x='date', y='amount', 
                      title=f'Daily Spending (Last {days} Days)',
                      labels={'amount': 'Amount ($)', 'date': 'Date'})
        fig.update_layout(height=400)
        return fig
    
    @staticmethod
    def category_breakdown(transactions: list):
        """Create category breakdown pie chart"""
        if not transactions:
            return None
        
        df = pd.DataFrame(transactions)
        category_spending = df.groupby('category')['amount'].sum().reset_index()
        
        fig = px.pie(category_spending, values='amount', names='category',
                     title='Spending by Category',
                     color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_layout(height=400)
        return fig
    
    @staticmethod
    def pantry_health(pantry_items: list):
        """Create pantry health metrics"""
        if not pantry_items:
            return None
        
        categories = {}
        for item in pantry_items:
            cat = item.get('category', 'other')
            categories[cat] = categories.get(cat, 0) + 1
        
        fig = px.bar(x=list(categories.keys()), y=list(categories.values()),
                     title='Pantry Distribution by Category',
                     labels={'x': 'Category', 'y': 'Number of Items'})
        fig.update_layout(height=400)
        return fig